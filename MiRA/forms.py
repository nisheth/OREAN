from django import forms
from django.forms.util import ErrorList
from api.models import *

class registerNewUserForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField(widget=forms.TextInput(attrs={'type': 'email'}))
    choose_password = forms.CharField(widget=forms.PasswordInput())
    verify_password = forms.CharField(widget=forms.PasswordInput())

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
    class Meta:
        model = Project
        fields = ['name', 'public', 'user']
        widgets = {'user': forms.HiddenInput()}

class addUserToProjectForm(forms.Form):
    user_email = forms.EmailField(widget=forms.TextInput(attrs={'type': 'email'}))
    action = forms.CharField(widget=forms.HiddenInput())
