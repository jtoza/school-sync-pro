# backup_manager/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.backup_dashboard, name='backup_dashboard'),
    path('create-backup/', views.CreateBackupView.as_view(), name='create_backup'),
    
    # Export URLs - Make sure ALL of these are included
    path('export/students/excel/', views.ExportStudentsExcel.as_view(), name='export_students_excel'),
    path('export/teachers/excel/', views.ExportTeachersExcel.as_view(), name='export_teachers_excel'),
    path('export/finance/excel/', views.ExportFinanceExcel.as_view(), name='export_finance_excel'),
    path('export/academic/excel/', views.ExportAcademicExcel.as_view(), name='export_academic_excel'),
    path('export/results/excel/', views.ExportResultsExcel.as_view(), name='export_results_excel'),
    path('export/attendance/excel/', views.ExportAttendanceExcel.as_view(), name='export_attendance_excel'),
    path('export/idcards/excel/', views.ExportIdCardsExcel.as_view(), name='export_idcards_excel'),
    path('export/portfolio/excel/', views.ExportPortfolioExcel.as_view(), name='export_portfolio_excel'),
    path('export/all/', views.ExportAllData.as_view(), name='export_all_data'),
]