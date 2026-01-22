from django.contrib import admin
from django.utils.html import format_html
from .models import Subject, ClassLevel, LessonPlan, LessonPlanAttachment, LessonPlanComment


class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['created_at']


class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade_level', 'description']
    list_filter = ['grade_level']
    search_fields = ['name']


class LessonPlanAttachmentInline(admin.TabularInline):
    model = LessonPlanAttachment
    extra = 1


class LessonPlanCommentInline(admin.TabularInline):
    model = LessonPlanComment
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LessonPlan)
class LessonPlanAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'teacher', 
        'subject', 
        'class_level',
        'status',
        'visibility',
        'created_at',
        'duration_minutes',
        'is_published'
    ]
    list_filter = [
        'status', 
        'visibility', 
        'created_at',
        'subject',
        'class_level'
    ]
    search_fields = [
        'title', 
        'objectives', 
        'content',
        'teacher__username',
        'teacher__email'
    ]
    readonly_fields = ['created_at', 'updated_at', 'published_at']
    inlines = [LessonPlanAttachmentInline, LessonPlanCommentInline]
    filter_horizontal = []
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'teacher', 'subject', 'class_level', 'tags')
        }),
        ('Lesson Details', {
            'fields': ('objectives', 'content', 'activities', 'materials', 'assessment', 'homework')
        }),
        ('Schedule', {
            'fields': ('duration_minutes', 'date_taught', 'week_number', 'term')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'visibility', 'published_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_lesson_plans', 'publish_lesson_plans']
    
    def approve_lesson_plans(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} lesson plans have been approved.")
    approve_lesson_plans.short_description = "Approve selected lesson plans"
    
    def publish_lesson_plans(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='approved').update(status='published', published_at=timezone.now())
        self.message_user(request, f"{updated} lesson plans have been published.")
    publish_lesson_plans.short_description = "Publish approved lesson plans"


@admin.register(LessonPlanAttachment)
class LessonPlanAttachmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson_plan', 'file_type', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['title', 'description', 'lesson_plan__title']


@admin.register(LessonPlanComment)
class LessonPlanCommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'lesson_plan', 'created_at', 'is_resolved']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['content', 'author__username', 'lesson_plan__title']


admin.site.register(Subject, SubjectAdmin)
admin.site.register(ClassLevel, ClassLevelAdmin)