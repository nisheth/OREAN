from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from api.models import *
from OREAN.utils import *

@login_required
def main(request, invitecode=None):
    p=None
    if invitecode:
        try: 
            p = Project.objects.get(invitecode = invitecode)
        except:
            messages.add_message(request, messages.ERROR, "The invitation code is not valid.")
            return redirect('home') 
        if in_project(request.user, p): 
            messages.add_message(request, messages.WARNING, "You already have access to this project (%s)." %p.name)
        else:
            try:
                up = UserProject(user=request.user, project=p, manager=False)
                up.save()
                messages.add_message(request, messages.SUCCESS, "You have joined this project (%s)."%p.name)    
            except:
                messages.add_message(request, messages.ERROR, "Unexpected error while attempting to join the project (%s)." %p.name)
    return redirect('projectPage', p.invitecode) 
