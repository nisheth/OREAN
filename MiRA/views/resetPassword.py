from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from api.models import *
from MiRA.utils import *
from MiRA.forms import *
import datetime
import traceback

def requestReset(request):
  if request.method=='POST':
    email = request.POST.get('email') or None
    try: 
      myuser = User.objects.get(email=email)
      myurl = make_url(request, myuser, 'resetPassword')
      message = """
%s,

This is an automated message from MiRA. A password reset request was made for the account associated with this email. 
To select a new password, please visit the following url: %s 

If this request was made in error, you may ignore this message and continue to use your existing credentials.

Thanks,
MiRA Staff 
""" % (myuser.first_name, myurl)
      send_new_email(request, myuser.email, 'MiRA Password Reset', message)
      messages.add_message(request, messages.SUCCESS, "A reset link has been sent to your email address")
      return redirect('home')
    except:
      messages.add_message(request, messages.ERROR, "The provided email is not valid")
  return render(request, 'requestReset.html')

def main(request, token=None):
  try: myobj = EmailTokens.objects.get(type=2, token=token)
  except: 
    messages.add_message(request, messages.ERROR, "Invalid URL")
    return redirect('home')
  elapsed = timezone.now() - myobj.datetime
  if elapsed.seconds > 900:
    messages.add_message(request, messages.ERROR, "The link has expired. Reset links are only valid for 15 minutes. You must create a new request.")
    myobj.delete()
    return redirect('requestReset')
  form = resetPasswordForm(request.POST or None)
  if request.method=='POST':
    if form.is_valid():
      myuser = myobj.user
      myuser.set_password(form.cleaned_data['choose_password'])
      myuser.save()
      messages.add_message(request, messages.SUCCESS, "Your password has been reset.")
      myobj.delete()
      return redirect('login')
  return render(request, 'resetPassword.html', {'form': form})
