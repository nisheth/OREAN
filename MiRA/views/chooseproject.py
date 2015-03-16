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
        projectstring = request.POST.get('project')
        projectID, projectName = projectstring.split("|")
        if not projectID: return render(request, 'buildquery.html', params)
        ap = ActiveProject.objects.get_or_none(user=request.user)
        if ap is None:
            ap = ActiveProject(user=request.user, project=Project.objects.get(pk=int(projectID)))
        else:
            ap.project = Project.objects.get(pk=int(projectID))
        ap.save()
        request.session['projectID'] = int(projectID)
        request.session['projectName'] = projectName
        request.session['projectTimecourse'] = ap.project.is_timecourse()
        messages.add_message(request, messages.SUCCESS, "Project changed to %s" %projectName)
        return redirect('managequeries')
    return render(request, 'chooseproject.html', params)
