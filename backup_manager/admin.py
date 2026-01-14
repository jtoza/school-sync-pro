# backup_manager/admin.py
from django.contrib import admin
from .models import BackupLog

@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'backup_type', 'file_size', 'status']
    list_filter = ['backup_type', 'status', 'timestamp']
    readonly_fields = ['timestamp', 'backup_type', 'file_path', 'file_size', 'status', 'notes']
    search_fields = ['file_path', 'notes']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation of backup logs
    
    def has_change_permission(self, request, obj=None):
        return False  # Make logs read-only
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete logs

# If you want to add a custom admin view, use this approach:
from django.urls import path
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

class BackupAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('backup-dashboard/', self.admin_view(self.backup_dashboard), name='backup-dashboard'),
        ]
        return custom_urls + urls
    
    def backup_dashboard(self, request):
        from .models import BackupLog
        recent_backups = BackupLog.objects.all()[:10]
        context = {
            'title': 'Backup & Export Dashboard',
            'recent_backups': recent_backups,
            **self.each_context(request),
        }
        return render(request, 'backup_manager/dashboard.html', context)

# If you want to override the default admin site, uncomment:
# admin.site = BackupAdminSite()