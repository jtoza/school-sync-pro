from django import forms
from .models import PortfolioItem, PortfolioCategory

class PortfolioItemForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = [
            'title', 'description', 'category', 'file_type',
            'document_file', 'image_file', 'code_file', 
            'external_url', 'skills_used', 'is_published'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'skills_used': forms.TextInput(attrs={'placeholder': 'Python, Django, JavaScript, ...'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        file_type = cleaned_data.get('file_type')
        
        # Validate that the appropriate file is provided based on file_type
        if file_type == 'document' and not cleaned_data.get('document_file'):
            raise forms.ValidationError("Please upload a document file for document type.")
        elif file_type == 'image' and not cleaned_data.get('image_file'):
            raise forms.ValidationError("Please upload an image file for image type.")
        elif file_type == 'code' and not cleaned_data.get('code_file'):
            raise forms.ValidationError("Please upload a code file for code type.")
        
        return cleaned_data