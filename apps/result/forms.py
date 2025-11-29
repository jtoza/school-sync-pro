from django import forms
from django.forms import ModelForm, modelformset_factory
from django.forms import modelformset_factory

from apps.corecode.models import AcademicSession, AcademicTerm, Subject

from .models import Result


class CreateResults(forms.Form):
    session = forms.ModelChoiceField(queryset=AcademicSession.objects.all())
    term = forms.ModelChoiceField(queryset=AcademicTerm.objects.all())
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(), widget=forms.CheckboxSelectMultiple
    )


EditResults = modelformset_factory(
    Result,
    fields=("test_score", "exam_score", "teacher_comment", "headteacher_comment"),
    extra=0,
    can_delete=True,
)


class BulkUploadForm(forms.Form):
    """Form for bulk uploading results via Excel/CSV file."""
    file = forms.FileField(
        label="Upload File",
        help_text="Upload an Excel (.xlsx) or CSV file with student results",
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls,.csv',
            'class': 'form-control'
        })
    )
    session = forms.ModelChoiceField(
        queryset=None,
        label="Academic Session",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    term = forms.ModelChoiceField(
        queryset=None,
        label="Term",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    student_class = forms.ModelChoiceField(
        queryset=None,
        label="Class",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.corecode.models import AcademicSession, AcademicTerm, StudentClass
        self.fields['session'].queryset = AcademicSession.objects.all()
        self.fields['term'].queryset = AcademicTerm.objects.all()
        self.fields['student_class'].queryset = StudentClass.objects.all()
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            if not file.name.endswith(('.xlsx', '.xls', '.csv')):
                raise forms.ValidationError("Only Excel (.xlsx, .xls) and CSV files are allowed.")
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must not exceed 5MB.")
        return file
