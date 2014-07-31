from api.models import *

def main(request):
    project_admin = False
    if request.user.is_authenticated() and 'projectID' in request.session:
        if request.user.is_superuser or UserProject.objects.get(user=request.user, project=request.session['projectID']).manager: project_admin = True
    return {
       'is_project_admin': project_admin,
    }
