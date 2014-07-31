from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from api.models import *
from MiRA.forms import *
import json
import traceback

# Handler for management of projects
# requires "action" POST parameter 
# 
# Supported actions:
#  addUser: give user access to current project or send an invitation to an unregistered email address
#  promote: gives user access to project management controls
#  remove: removes user's access to the project
@login_required
def main(request):
    params = {}
    form = addUserToProjectForm(initial={'action': 'addUser'})
    if 'projectID' not in request.session: return redirect("chooseproject")
    if request.method == 'POST':
       form = addUserToProjectForm(request.POST)
       myaction = request.POST.get('action')
       userproject = request.POST.get('userproject') or 0
       try:
          if myaction == 'addUser':
            if form.is_valid():
              email = form.cleaned_data['user_email']
              usrObj = User.objects.filter(email=email)
              if usrObj.exists():
                 usrObj = usrObj[0]
                 if not usrObj.is_superuser and not UserProject.objects.filter(project=request.session['projectID'], user=usrObj).exists(): 
                    newAccessObj = UserProject(user=usrObj, project = request.session['projectID'])
                    newAccessObj.save()
                    messages.add_message(request, messages.SUCCESS, "added "+usrObj.get_full_name()+" to this project")
                 else: 
                    messages.add_message(request, messages.WARNING, usrObj.get_full_name()+" already has access to this project")
              else:
                 miraURL = request.build_absolute_uri(reverse('home'))
                 msg = """
Hello,

This is an automated message from MiRA. This email was added to an existing project on our system(%s) by %s. You can start exploring the data for this project by creating a MiRA account: 

%s

Thanks,
MiRA Staff 
""" % (request.session['projectName'], request.user.get_full_name(), miraURL)
                 newInvObj = Invitations(email=email, project=request.session['projectID'], user=usrObj)
                 newInvObj.save()
                 send_new_email(request, email, "MiRA Invitation", msg)
                 messages.add_message(request, messages.SUCCESS, "sent registration invitation to '"+email+"'")
            else: 
              messages.add_message(request, messages.ERROR, "You entered an invalid email address")
          else:
            myObj=UserProject.objects.get(pk=int(userproject))
            if myaction == 'promote': 
              myObj.manager = True
              myObj.save()
              return HttpResponse(json.dumps("user successfully granted to project management"), content_type="application/json")
            elif myaction == 'remove':
              myObj.delete()
              return HttpResponse(json.dumps("user successfully removed from project"), content_type="application/json")
            else:
              return HttpResponse(json.dumps("invalid action"), content_type="application/json")
       except:
            #return HttpResponse(json.dumps("exception during processing"), content_type="application/json")
            return HttpResponse(json.dumps("%s" % traceback.format_exc()), content_type="application/json")
    params['project_members'] = UserProject.objects.filter(project=request.session['projectID'])
    params['form'] = form
    return render(request, 'manageProject.html', params) 
