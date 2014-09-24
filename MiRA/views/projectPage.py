from django.shortcuts import render, redirect
from django.contrib import messages
from api.models import *
from MiRA.utils import *

def main(request, invitecode=None):
    params = {}
    p = None
    try: p = Project.objects.get(invitecode=invitecode)
    except:
        messages.add_message(request, messages.ERROR, "No such project")
        return redirect('home') 
    member = in_project(request.user, p)
    if not p.public and (not request.user.is_authenticated() or not member): return redirect('home')
    params['project'] = p
    params['samplecount'] = Analysis.objects.filter(project=p).values_list('sample', flat=True).distinct().count()
    params['attrcount'] = AttributeInfo.objects.filter(project=p).count()
    params['member'] = member
    return render(request, 'projectPage.html', params) 
