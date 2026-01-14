from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import AppConfig
from django.contrib.auth.models import User

# Create your models here.

class SiteConfig(models.Model):
    """Site Configurations"""

    key = models.SlugField()
    value = models.CharField(max_length=200)

    def __str__(self):
        return self.key


class AcademicSession(models.Model):
    """Academic Session"""

    name = models.CharField(max_length=200, unique=True)
    current = models.BooleanField(default=True)

    class Meta:
        ordering = ["-name"]

    def __str__(self):
        return self.name


class AcademicTerm(models.Model):
    """Academic Term"""

    name = models.CharField(max_length=20, unique=True)
    current = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subject(models.Model):
    """Subject"""

    name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class StudentClass(models.Model):
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        ordering = ["name"]

    def __str__(self):
        return self.name


# Signal to create default data after migrations
@receiver(post_migrate)
def create_default_data(sender, **kwargs):
    # Only run for the corecode app to avoid running multiple times
    if sender.name == 'apps.corecode':
        try:
            # Create default AcademicSession if none exists
            if not AcademicSession.objects.exists():
                AcademicSession.objects.create(name="2024-2025", current=True)
                print("Created default AcademicSession: 2024-2025")
            
            # Create default AcademicTerm if none exists
            if not AcademicTerm.objects.exists():
                AcademicTerm.objects.create(name="First Term", current=True)
                print("Created default AcademicTerm: First Term")
                
            # Create essential SiteConfig entries
            if not SiteConfig.objects.filter(key="school_name").exists():
                SiteConfig.objects.create(key="school_name", value="Your School Name")
                print("Created default SiteConfig: school_name")
                
        except Exception as e:
            print(f"Error creating default data: {e}")



class ClassManagement(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'groups__name': 'Teachers'})
    student_class = models.ForeignKey(StudentClass, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    assigned_date = models.DateField(auto_now_add=True)
    
    class Meta:
        unique_together = ['teacher', 'student_class']
        verbose_name_plural = "Class Management"
    
    def __str__(self):
        return f"{self.teacher.username} - {self.student_class.name}"