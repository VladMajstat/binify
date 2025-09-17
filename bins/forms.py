from django import forms
from django.forms import ModelForm
from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES, EXPIRY_CHOICES, ACCESS_CHOICES

from bins.models import Create_Bins

class CreateBinsForm(ModelForm):

    
    content = forms.CharField(min_length=10, max_length=10000)
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES)
    expiry = forms.ChoiceField(choices=EXPIRY_CHOICES)
    access = forms.ChoiceField(choices=ACCESS_CHOICES)
    title = forms.CharField()
    tags = forms.CharField(required=False)

    class Meta:
        model = Create_Bins
        fields = [
            'content',
            'category',
            'language',
            'expiry',
            'access',
            'title',
            'tags',
        ]
