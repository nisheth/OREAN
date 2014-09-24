from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.contrib import messages
from api.models import *
import os
import hashlib

def make_random():
  random_data = os.urandom(128)
  return hashlib.md5(random_data).hexdigest()

def make_url(request, user, type):
  token = make_random()
  while (EmailTokens.objects.filter(token=token).exists()):
    token = make_random()
  namedURL = 'activateNewUser'
  type_num = 1
  if type=='resetPassword': 
    namedURL=type
    type_num = 2
  myurl = request.build_absolute_uri(reverse(namedURL, args=(token,)))
  newTokenInstance = EmailTokens(user=user, type=type_num, token=token)
  newTokenInstance.save()
  return myurl

def send_new_email(request, to_address, subject, message):
  try: 
     send_mail(subject,
               message,
               'MiRA Web Server <mira@vcu.edu>',
               [to_address],
               fail_silently=False)
  except:
     messages.add_message(request, messages.ERROR, "An error occurred when attempting to send an email.")

def in_project(user, p):
     if not user.is_authenticated(): return False
     if user.is_superuser or UserProject.objects.filter(project=p, user=user).exists(): return True
     return False
