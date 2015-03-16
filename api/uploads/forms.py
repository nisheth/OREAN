from django import forms
from django.forms.util import ErrorList
from django.db.models import Q
from api.models import *

class UploadTaxaForm(forms.ModelForm):
    class Meta:
        model = Taxonomy
        fields = ['name', 'description', 'url'] 

class UploadAnalysisForm(forms.Form):
    file=forms.FileField()
    use_taxonomy=forms.BooleanField(initial=True, required=False)
    taxonomy=forms.ModelChoiceField(required=False, queryset=Taxonomy.objects.all(), widget=forms.Select(attrs={'class': "black"}))
