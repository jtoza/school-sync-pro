# backup_manager/views.py
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views import View
from django.core.management import call_command
from django.core.mail import EmailMessage
from django.conf import settings
from .utils.export_utils import *
from .models import BackupLog
import os
from pathlib import Path

def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def backup_dashboard(request):
    """Main backup and export dashboard"""
    recent_backups = BackupLog.objects.all()[:10]
    return render(request, 'backup_manager/dashboard.html', {
        'recent_backups': recent_backups
    })

class CreateBackupView(View):
    def post(self, request):
        try:
            # Run backup
            call_command('backup_data')

            # Locate latest backup file
            backups_root = Path('backups')
            latest_file = None
            if backups_root.exists():
                subdirs = [d for d in backups_root.iterdir() if d.is_dir()]
                if subdirs:
                    latest_dir = sorted(subdirs, key=lambda p: p.name, reverse=True)[0]
                    candidate = latest_dir / 'school_data_backup.json'
                    if candidate.exists():
                        latest_file = candidate

            # Email the backup if possible
            emailed = False
            if latest_file:
                subject = f"School Data Backup - {latest_file.parent.name}"
                body = "This email contains the latest school data backup as an attachment."
                # Recipients priority: custom setting, ADMINS, current user email
                recipients = []
                backup_to = getattr(settings, 'BACKUP_EMAIL_TO', None)
                if backup_to:
                    recipients = backup_to if isinstance(backup_to, (list, tuple)) else [backup_to]
                elif getattr(settings, 'ADMINS', None):
                    recipients = [addr for _, addr in settings.ADMINS]
                elif request.user and request.user.email:
                    recipients = [request.user.email]

                if recipients:
                    email = EmailMessage(
                        subject=subject,
                        body=body,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or None,
                        to=recipients,
                    )
                    with open(latest_file, 'rb') as fp:
                        email.attach(latest_file.name, fp.read(), 'application/json')
                    try:
                        email.send(fail_silently=False)
                        emailed = True
                    except Exception:
                        emailed = False

            return JsonResponse({'status': 'success', 'message': 'Backup created successfully', 'emailed': emailed})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

# Export views for each data type
class ExportStudentsExcel(View):
    def get(self, request):
        excel_file = export_students_excel()
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="students_data.xlsx"'
        return response

class ExportTeachersExcel(View):
    def get(self, request):
        excel_file = export_teachers_excel()
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="teachers_staff_data.xlsx"'
        return response

class ExportFinanceExcel(View):
    def get(self, request):
        excel_file = export_finance_excel()
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="financial_data.xlsx"'
        return response

class ExportAcademicExcel(View):
    def get(self, request):
        excel_file = export_academic_data()
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="academic_data.xlsx"'
        return response

class ExportResultsExcel(View):
    def get(self, request):
        excel_file = export_results_excel()
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="results_data.xlsx"'
        return response

class ExportAttendanceExcel(View):
    def get(self, request):
        excel_file = export_attendance_excel()
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="attendance_data.xlsx"'
        return response

class ExportIdCardsExcel(View):
    def get(self, request):
        excel_file = export_idcards_excel()
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="id_cards_data.xlsx"'
        return response

class ExportPortfolioExcel(View):
    def get(self, request):
        excel_file = export_portfolio_excel()
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="portfolio_data.xlsx"'
        return response

class ExportAllData(View):
    def get(self, request):
        export_dir, success, export_results = export_all_data()
        if success:
            return JsonResponse({
                'status': 'success', 
                'message': f'All data exported to: {export_dir}',
                'export_path': export_dir,
                'results': export_results
            })
        else:
            return JsonResponse({
                'status': 'error', 
                'message': export_dir,
                'results': export_results
            })