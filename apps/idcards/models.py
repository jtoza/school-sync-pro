from django.db import models
from apps.students.models import Student
from django.utils import timezone
from apps.staffs.models import Staff 

class StudentIDCard(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    id_number = models.CharField(max_length=20, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True)
    barcode = models.ImageField(upload_to='idcards/barcodes/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='idcards/qrcodes/', blank=True, null=True)
    template_used = models.CharField(max_length=50, default='default')
    
    class Meta:
        verbose_name = "Student ID Card"
        verbose_name_plural = "Student ID Cards"
    
    def __str__(self):
        return f"ID Card - {self.student} ({self.id_number})"

class IDCardTemplate(models.Model):
    name = models.CharField(max_length=100)
    template_file = models.CharField(max_length=100)  # Path to template
    is_default = models.BooleanField(default=False)
    background_color = models.CharField(max_length=7, default='#FFFFFF')
    text_color = models.CharField(max_length=7, default='#000000')
    school_logo_position = models.CharField(max_length=20, choices=[
        ('top_left', 'Top Left'),
        ('top_center', 'Top Center'),
        ('top_right', 'Top Right'),
    ], default='top_center')
    
    def __str__(self):
        return self.name
    
class TeacherIDCard(models.Model):
    teacher = models.OneToOneField('staffs.Staff', on_delete=models.CASCADE)
    id_number = models.CharField(max_length=20, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    template_used = models.CharField(max_length=50, default='default')
    is_active = models.BooleanField(default=True)
    qr_code = models.ImageField(upload_to='teacher_qrcodes/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Teacher ID Card"
        verbose_name_plural = "Teacher ID Cards"
    
    def __str__(self):
        return f"Teacher ID - {self.teacher.firstname} {self.teacher.surname}"
    
    def is_expired(self):
        return timezone.now().date() > self.expiry_date