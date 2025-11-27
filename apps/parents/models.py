from django.db import models
from django.contrib.auth.models import User
from apps.students.models import Student

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    students = models.ManyToManyField(Student, related_name='parents')
    phone_number = models.CharField(max_length=15, unique=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.phone_number}"
