import uuid
from django.db import models
from django.core.exceptions import ValidationError

from apps.corecode.models import (
    AcademicSession,
    AcademicTerm,
    StudentClass,
    Subject,
)
from apps.students.models import Student

from .utils import score_grade


# Create your models here.
class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    term = models.ForeignKey(AcademicTerm, on_delete=models.CASCADE)
    current_class = models.ForeignKey(StudentClass, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    test_score = models.IntegerField(default=0, help_text="CA out of 40")
    exam_score = models.IntegerField(default=0, help_text="Exam out of 60")
    teacher_comment = models.CharField(max_length=255, blank=True, default="")
    headteacher_comment = models.CharField(max_length=255, blank=True, default="")

    # SYNC FIELDS - FIXED: Remove default and make nullable initially
    sync_id = models.UUIDField(unique=True, blank=True, null=True)
    sync_status = models.CharField(
        max_length=20, 
        choices=[('synced', 'Synced'), ('pending', 'Pending'), ('conflict', 'Conflict')],
        default='synced'
    )
    last_modified = models.DateTimeField(auto_now=True)
    device_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ["subject"]

    def save(self, *args, **kwargs):
        # Generate sync_id if it doesn't exist
        if not self.sync_id:
            self.sync_id = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} {self.session} {self.term} {self.subject}"

    def clean(self):
        errors = {}
        if self.test_score is not None and self.test_score > 40:
            errors['test_score'] = 'CA must be ≤ 40'
        if self.exam_score is not None and self.exam_score > 60:
            errors['exam_score'] = 'Exam must be ≤ 60'
        if self.test_score is not None and self.test_score < 0:
            errors['test_score'] = 'CA cannot be negative'
        if self.exam_score is not None and self.exam_score < 0:
            errors['exam_score'] = 'Exam cannot be negative'
        if errors:
            raise ValidationError(errors)

    def total_score(self):
        return (self.test_score or 0) + (self.exam_score or 0)

    def grade(self):
        return score_grade(self.total_score())
    
    def grade_points(self):
        """Return grade points for this result (CBC system)."""
        from .utils import grade_to_points
        return grade_to_points(self.grade())
    
    @staticmethod
    def get_student_gpa(student, session, term):
        """Calculate GPA for a student in a given session and term."""
        from .utils import calculate_gpa
        results = Result.objects.filter(
            student=student,
            session=session,
            term=term
        )
        return calculate_gpa(results)