from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone


class Subject(models.Model):
    """Subject model that can be linked to lesson plans"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ClassLevel(models.Model):
    """Class level/grade model"""
    name = models.CharField(max_length=50)
    grade_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        blank=True, 
        null=True
    )
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['grade_level', 'name']
    
    def __str__(self):
        return f"{self.name} (Grade {self.grade_level})" if self.grade_level else self.name


class LessonPlan(models.Model):
    """Main Lesson Plan model"""
    
    VISIBILITY_CHOICES = [
        ('private', 'Private - Only Me'),
        ('admin', 'Administrators'),
        ('teachers', 'All Teachers'),
        ('students', 'Students'),
        ('parents', 'Parents'),
        ('public', 'Public - Everyone'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'In Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
    ]
    
    # Core information
    title = models.CharField(max_length=200)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_plans'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_plans'
    )
    class_level = models.ForeignKey(
        ClassLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_plans'
    )
    
    # Lesson details
    objectives = models.TextField(help_text="Learning objectives for this lesson")
    content = models.TextField(help_text="Main lesson content")
    activities = models.TextField(help_text="Classroom activities")
    materials = models.TextField(blank=True, help_text="Required materials/resources")
    assessment = models.TextField(blank=True, help_text="Assessment methods")
    homework = models.TextField(blank=True, help_text="Homework/assignments")
    
    # Metadata
    duration_minutes = models.IntegerField(
        default=45,
        validators=[MinValueValidator(5), MaxValueValidator(240)],
        help_text="Lesson duration in minutes"
    )
    date_taught = models.DateField(null=True, blank=True)
    week_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(52)],
        null=True,
        blank=True
    )
    term = models.CharField(max_length=50, blank=True)
    
    # Visibility and status
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='private'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Tags/categories
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_approve_lessonplan', 'Can approve lesson plans'),
            ('can_view_all_lessonplans', 'Can view all lesson plans'),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.teacher.username}"
    
    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def get_tags_list(self):
        """Return tags as a list"""
        return [tag.strip() for tag in self.tags.split(',')] if self.tags else []
    
    @property
    def is_published(self):
        return self.status == 'published'
    
    @property
    def can_be_viewed_by_public(self):
        return self.visibility in ['public', 'students', 'parents'] and self.is_published


class LessonPlanAttachment(models.Model):
    """Model for storing attachments for lesson plans"""
    lesson_plan = models.ForeignKey(
        LessonPlan,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='lesson_plan_attachments/%Y/%m/%d/')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def save(self, *args, **kwargs):
        # Automatically determine file type from extension
        if self.file and not self.file_type:
            ext = self.file.name.split('.')[-1].lower()
            self.file_type = ext
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.lesson_plan.title}"


class LessonPlanComment(models.Model):
    """Comments/feedback on lesson plans"""
    lesson_plan = models.ForeignKey(
        LessonPlan,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_plan_comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.lesson_plan.title}"