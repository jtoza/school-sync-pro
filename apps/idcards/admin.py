from django.contrib import admin
from .models import StudentIDCard, IDCardTemplate

@admin.register(StudentIDCard)
class StudentIDCardAdmin(admin.ModelAdmin):
    list_display = ['id_number', 'student', 'issue_date', 'expiry_date', 'is_active']
    list_filter = ['is_active', 'issue_date', 'expiry_date']
    search_fields = ['id_number', 'student__first_name', 'student__last_name']
    readonly_fields = ['issue_date']

@admin.register(IDCardTemplate)
class IDCardTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'school_logo_position']
    list_editable = ['is_default']