from django import forms
from .models import Homework

class HomeworkForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ['student_class', 'subject', 'title', 'description', 'questions', 'due_date', 'attachment']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'student_class': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'questions': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Enter homework questions here (e.g., 1. Question one\n2. Question two)'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
