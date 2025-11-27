import uuid
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.corecode.models import StudentClass


class Student(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("inactive", "Inactive")]
    GENDER_CHOICES = [("male", "Male"), ("female", "Female")]

    current_status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="active"
    )
    registration_number = models.CharField(max_length=200, unique=True)
    surname = models.CharField(max_length=200)
    firstname = models.CharField(max_length=200)
    other_name = models.CharField(max_length=200, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="male")
    date_of_birth = models.DateField(default=timezone.now)
    current_class = models.ForeignKey(
        StudentClass, on_delete=models.SET_NULL, blank=True, null=True
    )
    date_of_admission = models.DateField(default=timezone.now)

    mobile_num_regex = RegexValidator(
        regex="^[0-9]{10,15}$", message="Entered mobile number isn't in a right format!"
    )
    parent_mobile_number = models.CharField(
        validators=[mobile_num_regex], max_length=13, blank=True
    )

    # New guardian/contact/medical/service fields
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(validators=[mobile_num_regex], max_length=13, blank=True)
    guardian_email = models.EmailField(blank=True)
    relationship = models.CharField(max_length=50, blank=True, help_text="e.g., Mother, Father, Aunt")
    emergency_contact = models.CharField(max_length=200, blank=True)
    pickup_authorized = models.TextField(blank=True, help_text="Comma-separated list of authorized pickup persons")

    medical_notes = models.TextField(blank=True)
    allergies = models.TextField(blank=True)

    house = models.CharField(max_length=50, blank=True)
    transport_opt_in = models.BooleanField(default=False)
    lunch_opt_in = models.BooleanField(default=False)

    address = models.TextField(blank=True)
    others = models.TextField(blank=True)
    passport = models.ImageField(blank=True, upload_to="students/passports/")

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
        ordering = ["surname", "firstname", "other_name"]

    def __str__(self):
        return f"{self.surname} {self.firstname} {self.other_name} ({self.registration_number})"

    def save(self, *args, **kwargs):
        # Generate sync_id if it doesn't exist
        if not self.sync_id:
            self.sync_id = uuid.uuid4()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("student-detail", kwargs={"pk": self.pk})

    def get_full_name(self):
        """Return the full name of the student"""
        full_name = f"{self.surname} {self.firstname}"
        if self.other_name:
            full_name += f" {self.other_name}"
        return full_name.strip()

    def get_short_name(self):
        """Return short name (surname + firstname only)"""
        return f"{self.surname} {self.firstname}"

    def get_formal_name(self):
        """Return name in formal format (Surname, Firstname Othername)"""
        if self.other_name:
            return f"{self.surname}, {self.firstname} {self.other_name}"
        return f"{self.surname}, {self.firstname}"

    def get_initials(self):
        """Return initials of the student"""
        initials = f"{self.surname[0]}{self.firstname[0]}" if self.surname and self.firstname else ""
        if self.other_name:
            initials += self.other_name[0]
        return initials.upper()


class StudentBulkUpload(models.Model):
    date_uploaded = models.DateTimeField(auto_now=True)
    csv_file = models.FileField(upload_to="students/bulkupload/")