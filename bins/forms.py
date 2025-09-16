from django import forms
from django.forms import ModelForm


from bins.models import Create_Bins

class CreateBinsForm(ModelForm):

    
    content = forms.CharField(min_length=10, max_length=10000)
    category = forms.ChoiceField(choices=Create_Bins.CATEGORY_CHOICES)
    language = forms.ChoiceField(choices=Create_Bins.LANGUAGE_CHOICES)
    expiry = forms.ChoiceField(choices=Create_Bins.EXPIRY_CHOICES)
    access = forms.ChoiceField(choices=Create_Bins.ACCESS_CHOICES)
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