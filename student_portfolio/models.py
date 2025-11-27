from django.db import models
from apps.students.models import Student  # Fixed import path
from django.core.validators import FileExtensionValidator

class PortfolioCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class PortfolioItem(models.Model):
    FILE_TYPES = [
        ('image', 'Image'),
        ('document', 'Document'),
        ('code', 'Code'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='portfolio_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(PortfolioCategory, on_delete=models.SET_NULL, null=True)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    
    # File upload fields
    document_file = models.FileField(
        upload_to='portfolio/documents/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'txt'])]
    )
    image_file = models.ImageField(
        upload_to='portfolio/images/',
        blank=True,
        null=True
    )
    code_file = models.FileField(
        upload_to='portfolio/code/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['py', 'js', 'java', 'cpp', 'html', 'css'])]
    )
    
    # For external links (GitHub repos, YouTube videos, etc.)
    external_url = models.URLField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    
    # Skills/tags
    skills_used = models.CharField(max_length=300, blank=True, help_text="Comma-separated skills")
    
    def __str__(self):
        return f"{self.title} - {self.student}"
    
    def get_display_file(self):
        """Returns the appropriate file based on file_type"""
        file_mapping = {
            'document': self.document_file,
            'image': self.image_file,
            'code': self.code_file,
        }
        return file_mapping.get(self.file_type)
    
    class Meta:
        ordering = ['-created_at']