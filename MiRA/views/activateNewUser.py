from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login
from api.models import *
from MiRA.utils import *
import datetime
import traceback

def main(request, token=None):
  try:
      myobj = EmailTokens.objects.get(type=1, token=token)
      myuser = myobj.user
      myuser.is_active=True
      myuser.save()
      invObjs = Invitations.objects.filter(email=myuser.email)
      if invObjs.exists():
          for invObj in invObjs:
              if not UserProject.objects.filter(user=myuser, project=invObj.project).exists(): 
                  newAccessObj = UserProject(user=myuser, project=invObj.project)
                  newAccessObj.save()
      messages.add_message(request, messages.SUCCESS, "Your account has been activated.")
      return redirect('login')
  except: messages.add_message(request, messages.ERROR, "%s" % traceback.format_exc())
  return redirect('home')
