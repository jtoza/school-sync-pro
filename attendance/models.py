from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.corecode.models import StudentClass, AcademicSession, AcademicTerm
from apps.students.models import Student


class AttendanceRegister(models.Model):
    date = models.DateField(default=timezone.now)
    student_class = models.ForeignKey(StudentClass, on_delete=models.CASCADE, related_name='attendance_registers')
    term = models.ForeignKey(AcademicTerm, on_delete=models.PROTECT)
    session = models.ForeignKey(AcademicSession, on_delete=models.PROTECT)
    taken_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    is_locked = models.BooleanField(default=False)
    auto_created = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('date', 'student_class', 'term', 'session')
        ordering = ('-date',)
        permissions = [
            ('can_lock_register', 'Can lock attendance register'),
            ('can_bulk_create', 'Can bulk create registers'),
        ]

    def __str__(self):
        return f"Register {self.date} - {self.student_class} ({self.term} {self.session})"

    def clean(self):
        if self.date > timezone.now().date():
            raise ValidationError("Attendance date cannot be in the future.")
    
    @property
    def total_students(self):
        return Student.objects.filter(current_class=self.student_class, current_status='active').count()
    
    @property
    def present_count(self):
        return self.entries.filter(status=AttendanceEntry.STATUS_PRESENT).count()
    
    @property
    def absent_count(self):
        return self.entries.filter(status=AttendanceEntry.STATUS_ABSENT).count()
    
    @property
    def late_count(self):
        return self.entries.filter(status=AttendanceEntry.STATUS_LATE).count()
    
    @property
    def attendance_rate(self):
        if self.total_students == 0:
            return 0
        return round((self.present_count / self.total_students) * 100, 1)


class AttendanceEntry(models.Model):
    STATUS_PRESENT = 'P'
    STATUS_ABSENT = 'A'
    STATUS_LATE = 'L'
    STATUS_EXCUSED = 'E'
    STATUS_HALF_DAY = 'H'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_LATE, 'Late'),
        (STATUS_EXCUSED, 'Excused'),
        (STATUS_HALF_DAY, 'Half Day'),
    ]

    register = models.ForeignKey(AttendanceRegister, on_delete=models.CASCADE, related_name='entries')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    remarks = models.CharField(max_length=255, blank=True, default='')
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('register', 'student')
        ordering = ('student__surname', 'student__firstname')
        verbose_name_plural = 'Attendance entries'

    def __str__(self):
        return f"{self.student} - {self.get_status_display()}"


class DailyAttendanceConfig(models.Model):
    student_class = models.ForeignKey(StudentClass, on_delete=models.CASCADE)
    auto_create = models.BooleanField(default=True)
    notify_absent = models.BooleanField(default=True)
    absent_threshold = models.PositiveIntegerField(default=3, help_text="Notify after consecutive absences")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Config for {self.student_class}"


class AttendanceSummary(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(AcademicTerm, on_delete=models.CASCADE)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    total_days = models.PositiveIntegerField(default=0)
    days_present = models.PositiveIntegerField(default=0)
    days_absent = models.PositiveIntegerField(default=0)
    days_late = models.PositiveIntegerField(default=0)
    attendance_rate = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'term', 'session')
        verbose_name_plural = 'Attendance summaries'

    def __str__(self):
        return f"Summary - {self.student} ({self.term} {self.session})"