from django import forms
from django.forms.util import ErrorList
from django.db.models import Q
from api.models import *

class UploadTaxaForm(forms.ModelForm):
    class Meta:
        model = Taxonomy
        fields = ['name', 'description', 'url'] 

class UploadAnalysisForm(forms.Form):
    use_taxonomy=forms.BooleanField(initial=True, required=False)
    taxonomy=forms.ModelChoiceField(required=False, queryset=Taxonomy.objects.all(), widget=forms.Select(attrs={'class': "black"}))

class UploadFileForm(forms.ModelForm):

    FORMAT_CHOICES = (
     ('columnar', 'columnar'),
     ('matrix', 'matrix')
    )

    format = forms.ChoiceField(choices = FORMAT_CHOICES, label="Format", initial='columnar', widget=forms.Select(), required=True)

    class Meta:
        model = UploadedFile
        fields = ['type', 'user', 'file']
        widgets = {
            'type': forms.HiddenInput,
            'user': forms.HiddenInput,
        }

class MatrixAnalysisForm(forms.Form):
    dataset = forms.CharField()
    method = forms.CharField()
    category = forms.CharField()
