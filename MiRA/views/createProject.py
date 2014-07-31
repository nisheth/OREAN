from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from api.models import *
from MiRA.forms import *

@login_required
def main(request):
    form = newProjectForm(initial={'user': request.user})
    if request.method == 'POST':
       form = newProjectForm(request.POST)
       if form.is_valid():
           newProject = form.save()
           projectPermission = UserProject(user=request.user, project=newProject, manager=True)
           projectPermission.save()
           messages.add_message(request, messages.SUCCESS, "New project created successfully.")
           return redirect('home')
       else:
           messages.add_message(request, messages.ERROR, "Please check your submission.")
    return render(request, 'createProject.html', {"form": form}) 
