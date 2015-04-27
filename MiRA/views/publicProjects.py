from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from . import myutils
from api import *
from api import internal

@login_required
def enroll(request):
  params=dict()
  publicProjects = internal.ListProjects(request, public=True)
  enroll = request.GET.get('enroll', None)
  if enroll:
    try:
      enroll = int(enroll)
      p = publicProjects.get(pk=enroll)
      if not request.user.is_superuser:
        enrollment, created = UserProject.objects.get_or_create(user=request.user, project = p)
        if created:
          messages.add_message(request, messages.SUCCESS, 'Enrolled into "%s"' % (enrollment.project.name))
      myutils.activateProject(request, p)
      return redirect('managequeries')
    except:
      messages.add_message(request, messages.ERROR, 'Error during attempted enrollment')
  params['publicProjects'] = publicProjects
  return render(request, 'publicProjects.html', params)
