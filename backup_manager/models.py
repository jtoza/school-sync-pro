# backup_manager/models.py
from django.db import models

class BackupLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    backup_type = models.CharField(max_length=50, choices=[
        ('auto', 'Automatic'),
        ('manual', 'Manual'),
        ('export', 'Data Export')
    ])
    file_path = models.CharField(max_length=500)
    file_size = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('in_progress', 'In Progress')
    ])
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.backup_type} - {self.timestamp}"