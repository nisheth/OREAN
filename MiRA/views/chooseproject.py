from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from . import myutils

@login_required
def main(request):
    params = {}
    params['projects'] = myutils.call_api(request, 'ListProjects')
    if request.method=='POST':
        projectstring = request.POST.get('project')
        projectID, projectName = projectstring.split("|")
        if not projectID: return render(request, 'buildquery.html', params)
        request.session['projectID'] = int(projectID)
        request.session['projectName'] = projectName
        messages.add_message(request, messages.SUCCESS, "Project changed to %s" %projectName)
        return redirect('managequeries')
    return render(request, 'chooseproject.html', params)
