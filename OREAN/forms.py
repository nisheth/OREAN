from django import forms
from django.forms.util import ErrorList
from django.db.models import Q
from api.models import *

class registerNewUserForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField(widget=forms.TextInput(attrs={'type': 'email'}))
    choose_password = forms.CharField(widget=forms.PasswordInput())
    verify_password = forms.CharField(widget=forms.PasswordInput())
    token = forms.CharField(widget=forms.HiddenInput(), required=False)

    # custom validation to require matching password fields
    def clean(self):
        cleaned_data = super(registerNewUserForm, self).clean()
        p1 = cleaned_data.get('choose_password')
        p2 = cleaned_data.get('verify_password')
        email = cleaned_data.get('email')
        if len(User.objects.filter(email=email)):
            self._errors["email"] = ErrorList(["Email is already registered"])
        if p1 != p2:
            raise forms.ValidationError("Passwords did not match.")
        return cleaned_data

class resetPasswordForm(forms.Form):
    choose_password = forms.CharField(widget=forms.PasswordInput())
    verify_password = forms.CharField(widget=forms.PasswordInput())

    # custom validation to require matching password fields
    def clean(self):
        cleaned_data = super(resetPasswordForm, self).clean()
        p1 = cleaned_data.get('choose_password')
        p2 = cleaned_data.get('verify_password')
        if p1 != p2:
            raise forms.ValidationError("Passwords did not match.")
        return cleaned_data

class newProjectForm(forms.ModelForm):
    timeseries_flag = forms.BooleanField(label='Timeseries')
    class Meta:
        model = Project
        fields = ['name', 'description', 'publication', 'publication_url', 'project_url', 'public', 'user', 'invitecode' , 'timeseries_flag']
        widgets = {'user': forms.HiddenInput(), 'invitecode': forms.HiddenInput()}

class addUserToProjectForm(forms.Form):
    user_email = forms.EmailField(widget=forms.TextInput(attrs={'type': 'email'}))
    action = forms.CharField(widget=forms.HiddenInput())

class changeProjectLeadForm(forms.Form):
    Project_lead =forms.ModelChoiceField(User.objects.filter(is_superuser=True))
    action = forms.CharField(widget=forms.HiddenInput(), initial='changeLead')

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super(changeProjectLeadForm, self).__init__(*args, **kwargs)

        if project:
            self.fields['Project_lead'].queryset = User.objects.filter(Q(is_superuser=True)|Q(userproject__manager=True, userproject__project=project)).distinct() 
        self.fields['Project_lead'].label_from_instance = lambda obj: "%s" % obj.get_full_name()

