from django import forms
from django.forms import ModelForm
from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES, EXPIRY_CHOICES, ACCESS_CHOICES

from .models import Create_Bins, BinComment

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

class BinCommentForm(ModelForm):

    text = forms.CharField(min_length=3, max_length=10000, label="")

    def clean_text(self):
        value = self.cleaned_data['text']
        spam_words = ['spam', 'http://', 'https://', 'buy now', 'free money', "click here", "visit", "promo", "discount", "sex", "xxx"]  # додайте свої слова
        for word in spam_words:
            if word in value.lower():
                raise forms.ValidationError("Коментар містить спам або заборонені слова.")
        return value

    class Meta:
        model = BinComment
        fields = ['text']
