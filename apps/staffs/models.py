from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Staff(models.Model):
    STATUS = [("active", "Active"), ("inactive", "Inactive")]
    GENDER = [("male", "Male"), ("female", "Female")]

    current_status = models.CharField(max_length=10, choices=STATUS, default="active")
    surname = models.CharField(max_length=200)
    firstname = models.CharField(max_length=200)
    other_name = models.CharField(max_length=200, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER, default="male")
    date_of_birth = models.DateField(default=timezone.now)
    date_of_admission = models.DateField(default=timezone.now)

    mobile_num_regex = RegexValidator(
        regex="^[0-9]{10,15}$", message="Entered mobile number isn't in a right format!"
    )
    mobile_number = models.CharField(
        validators=[mobile_num_regex], max_length=13, blank=True
    )

    address = models.TextField(blank=True)
    others = models.TextField(blank=True)
    
    # Add image field
    image = models.ImageField(upload_to='staffs/', blank=True, null=True)

    def __str__(self):
        return f"{self.surname} {self.firstname} {self.other_name}"

    def get_absolute_url(self):
        return reverse("staff-detail", kwargs={"pk": self.pk})

    def get_full_name(self):
        """Get full name of staff member"""
        names = [self.firstname, self.surname]
        if self.other_name:
            names.append(self.other_name)
        return " ".join(names)

    @property
    def is_active(self):
        """Property to check if staff is active - for compatibility"""
        return self.current_status == "active"
    

class TeacherAttendance(models.Model):
    ATTENDANCE_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('leave', 'On Leave'),
    ]

    teacher = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=ATTENDANCE_CHOICES, default='present')
    time_in = models.TimeField(blank=True, null=True)
    time_out = models.TimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Teacher Attendance"
        verbose_name_plural = "Teacher Attendances"
        unique_together = ['teacher', 'date']  # One attendance per teacher per day
        ordering = ['-date', 'teacher']

    def __str__(self):
        return f"{self.teacher} - {self.date} - {self.status}"

    @property
    def hours_worked(self):
        if self.time_in and self.time_out:
            from datetime import datetime
            time_in = datetime.combine(self.date, self.time_in)
            time_out = datetime.combine(self.date, self.time_out)
            duration = time_out - time_in
            hours = duration.total_seconds() / 3600
            return round(hours, 2)
        return None    