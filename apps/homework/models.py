from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from apps.corecode.models import StudentClass, Subject

class Homework(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    student_class = models.ForeignKey(StudentClass, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    questions = models.TextField(blank=True, help_text="Enter homework questions (one per line or numbered)")
    due_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    attachment = models.FileField(upload_to='homework_attachments/', blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.student_class} ({self.subject})"
