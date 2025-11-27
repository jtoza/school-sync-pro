from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import AttendanceRegister, AttendanceEntry, DailyAttendanceConfig


class AttendanceRegisterForm(forms.ModelForm):
    class Meta:
        model = AttendanceRegister
        fields = ['date', 'student_class', 'term', 'session', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'student_class': forms.Select(attrs={'class': 'form-control'}),
            'term': forms.Select(attrs={'class': 'form-control'}),
            'session': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date(self):
        date = self.cleaned_data['date']
        if date > timezone.now().date():
            raise ValidationError("Attendance date cannot be in the future.")
        return date


class AttendanceEntryForm(forms.ModelForm):
    class Meta:
        model = AttendanceEntry
        fields = ['status', 'remarks', 'time_in', 'time_out']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control status-select'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control remarks-input', 'placeholder': 'Optional remarks...'}),
            'time_in': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control time-input'}),
            'time_out': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control time-input'}),
        }


class BulkRegisterForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    student_class = forms.ModelChoiceField(
        queryset=None,  # Will set in __init__
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    term = forms.ModelChoiceField(
        queryset=None,  # Will set in __init__
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    session = forms.ModelChoiceField(
        queryset=None,  # Will set in __init__
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from apps.corecode.models import StudentClass, AcademicTerm, AcademicSession
        self.fields['student_class'].queryset = StudentClass.objects.all()
        self.fields['term'].queryset = AcademicTerm.objects.all()
        self.fields['session'].queryset = AcademicSession.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("Start date cannot be after end date.")
            if start_date > timezone.now().date():
                raise ValidationError("Cannot create registers for future dates.")
        return cleaned_data


class DailyAttendanceConfigForm(forms.ModelForm):
    class Meta:
        model = DailyAttendanceConfig
        fields = ['auto_create', 'notify_absent', 'absent_threshold']
        widgets = {
            'auto_create': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_absent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'absent_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
        }