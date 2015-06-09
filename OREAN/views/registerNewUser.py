from django.shortcuts import render, redirect
from django.contrib import messages
from api.models import *
from OREAN.forms import *
from OREAN.utils import *
import traceback
 
def main(request):
  token = request.GET.get('token', None)
  form = registerNewUserForm(initial={'token': token})
  if request.method == 'POST':
    form = registerNewUserForm(request.POST)
    if form.is_valid():
       new_user = User.objects.create_user(form.cleaned_data['email'], form.cleaned_data['email'], form.cleaned_data['choose_password'])
       new_user.is_active = False
       new_user.last_name = form.cleaned_data['last_name']
       new_user.first_name = form.cleaned_data['first_name']
       new_user.save()
       if form.cleaned_data['token']:
           try:
               p = Project.objects.get(invitecode=form.cleaned_data['token'])
               new_inv = Invitations(user = p.user, email = new_user.email, project = p)
               new_inv.save()
           except:
               messages.add_message(request, messages.INFO, "ERROR: %s" % str(traceback.format_exc()))
       type = 'registration'
       myurl = make_url(request, new_user, type)
       msg = """
%s,

This is an automated message from OREAN. This email address was used to establish a new account on the OREAN webserver. 
To activate this account, please visit the following url: %s 

Thanks,
OREAN Staff 
""" % (new_user.first_name, myurl)
       msg = """
%s,

This is a message from OREAN. This email address was used on the OREAN webserver. 
Please visit the following url: %s 

Thanks,
OREAN Staff 
""" % (new_user.first_name, myurl)
       #send_new_email(request, new_user.email, 'OREAN Account Activation', msg)
       send_new_email(request, new_user.email, 'OREAN', msg)
       messages.add_message(request, messages.SUCCESS, "Registration successful. Check your email to activate the new account.")
       return redirect('home')
    else:
       messages.add_message(request, messages.ERROR, "There was a problem with your registration")
  return render(request, 'registerNewUser.html', {"form": form})
