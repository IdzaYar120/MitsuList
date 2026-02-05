from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'mitsulist-input',
                'rows': 4,
                'placeholder': 'Write your review here...'
            }),
        }
