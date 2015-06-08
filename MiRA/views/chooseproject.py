from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from . import myutils
from api import *
from api import internal
@login_required
def main(request):
    params = {}
    params['projects'] = internal.ListProjects(request)
    if request.method=='POST':
        projectID = request.POST.get('project', 0)
        goto = request.POST.get('goto', 'managequeries')
        project=Project.objects.get_or_none(pk=int(projectID))
        if not project:
            messages.add_message(request, messages.ERROR, "Unable to find the project")
            return redirect('home')
        myutils.activateProject(request, project)
        return redirect(goto)
    return render(request, 'chooseproject.html', params)
