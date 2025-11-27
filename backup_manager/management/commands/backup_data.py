# backup_manager/management/commands/backup_data.py
from django.core.management.base import BaseCommand
import os
import json
from datetime import datetime
from django.core import serializers
from django.apps import apps
from backup_manager.models import BackupLog

class Command(BaseCommand):
    help = 'Backup all school management data to JSON files'
    
    def add_arguments(self, parser):
        parser.add_argument('--model', type=str, help='Specific model to backup')
    
    def handle(self, *args, **options):
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        backup_dir = f"backups/{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        
        try:
            # Define models to backup (all your school models)
            models_to_backup = [
                'corecode.AcademicSession',
                'corecode.AcademicTerm', 
                'corecode.Subject',
                'corecode.StudentClass',
                'corecode.ClassManagement',
                'students.Student',
                'staffs.Staff',
                'staffs.TeacherAttendance',
                'finance.Invoice',
                'finance.InvoiceItem', 
                'finance.Receipt',
                'result.Result',
                'attendance.AttendanceRegister',
                'attendance.AttendanceEntry',
                'attendance.DailyAttendanceConfig',
                'attendance.AttendanceSummary',
                'idcards.StudentIDCard',
                'idcards.IDCardTemplate',
                'idcards.TeacherIDCard',
                'student_portfolio.PortfolioCategory',
                'student_portfolio.PortfolioItem',
            ]
            
            backup_data = {}
            
            for model_path in models_to_backup:
                try:
                    model = apps.get_model(model_path)
                    model_name = f"{model._meta.app_label}.{model._meta.model_name}"
                    self.stdout.write(f"Backing up {model_name}...")
                    
                    # Get all objects for this model
                    objects = model.objects.all()
                    serialized_data = serializers.serialize('python', objects)
                    backup_data[model_name] = serialized_data
                    
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Could not backup {model_path}: {str(e)}"))
                    continue
            
            # Save to JSON file
            backup_file = f"{backup_dir}/school_data_backup.json"
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Log the backup
            file_size = f"{os.path.getsize(backup_file) / 1024 / 1024:.2f} MB"
            BackupLog.objects.create(
                backup_type='manual',
                file_path=backup_file,
                file_size=file_size,
                status='success',
                notes=f'Backup completed for {len(backup_data)} models'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f"Backup completed: {backup_file}")
            )
            
        except Exception as e:
            BackupLog.objects.create(
                backup_type='manual',
                file_path='',
                file_size='0',
                status='failed',
                notes=f'Error: {str(e)}'
            )
            self.stdout.write(self.style.ERROR(f"Backup failed: {str(e)}"))