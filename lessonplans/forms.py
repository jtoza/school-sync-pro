from django import forms
from django.contrib.auth.models import User
from .models import LessonPlan, Subject, ClassLevel, LessonPlanAttachment, LessonPlanComment


class LessonPlanForm(forms.ModelForm):
    """Form for creating and editing lesson plans"""
    
    class Meta:
        model = LessonPlan
        fields = [
            'title',
            'subject',
            'class_level',
            'objectives',
            'content',
            'activities',
            'materials',
            'assessment',
            'homework',
            'duration_minutes',
            'date_taught',
            'week_number',
            'term',
            'tags',
            'visibility',
            'status'
        ]
        widgets = {
            'objectives': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 5}),
            'activities': forms.Textarea(attrs={'rows': 4}),
            'materials': forms.Textarea(attrs={'rows': 3}),
            'assessment': forms.Textarea(attrs={'rows': 3}),
            'homework': forms.Textarea(attrs={'rows': 3}),
            'date_taught': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_staff:
            # Limit status choices for non-staff users
            self.fields['status'].choices = [
                ('draft', 'Draft'),
                ('review', 'Submit for Review'),
            ]


class LessonPlanFilterForm(forms.Form):
    """Form for filtering lesson plans"""
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        empty_label="All Subjects"
    )
    class_level = forms.ModelChoiceField(
        queryset=ClassLevel.objects.all(),
        required=False,
        empty_label="All Classes"
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + LessonPlan.STATUS_CHOICES,
        required=False
    )
    visibility = forms.ChoiceField(
        choices=[('', 'All Visibility')] + LessonPlan.VISIBILITY_CHOICES,
        required=False
    )
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search...'}))
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'From date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'To date'})
    )


class LessonPlanAttachmentForm(forms.ModelForm):
    """Form for uploading attachments"""
    
    class Meta:
        model = LessonPlanAttachment
        fields = ['file', 'title', 'description']


class LessonPlanCommentForm(forms.ModelForm):
    """Form for adding comments"""
    
    class Meta:
        model = LessonPlanComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add your comment here...'})
        }