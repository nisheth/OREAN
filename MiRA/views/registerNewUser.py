from django.shortcuts import render, redirect
from django.contrib import messages
from api.models import *
from MiRA.forms import *
from MiRA.utils import *
  
def main(request):
  form = registerNewUserForm(request.POST or None)
  if request.method == 'POST':
    if form.is_valid():
       new_user = User.objects.create_user(form.cleaned_data['email'], form.cleaned_data['email'], form.cleaned_data['choose_password'])
       new_user.is_active = False
       new_user.last_name = form.cleaned_data['last_name']
       new_user.first_name = form.cleaned_data['first_name']
       new_user.save()
       type = 'registration'
       myurl = make_url(request, new_user, type)
       msg = """
%s,

This is an automated message from MiRA. This email address was used to establish a new account on the MiRA webserver. 
To activate this account, please visit the following url: %s 

Thanks,
MiRA Staff 
""" % (new_user.first_name, myurl)

       send_new_email(request, new_user.email, 'MiRA Account Activation', msg)
       messages.add_message(request, messages.SUCCESS, "Registration successful. Check your email to activate the new account.")
       return redirect('home')
    else:
       messages.add_message(request, messages.ERROR, "There was a problem with your registration")
  return render(request, 'registerNewUser.html', {"form": form})
