from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
import json
from OREAN.decorators import *
from api.models import *
import traceback
from django.shortcuts import render, get_object_or_404
from django.db.models import Q

# saves pages for users to retrieve
# quickly at a later time
@login_required
@activeproject
def save(request):
    # request.session['projectID'] 
    # request.user.id
    if request.method == 'POST':
        url = request.POST.get('url', None)
        name = request.POST.get('savedPageName', None)
        description = request.POST.get('description', '')
        dataBlob = request.POST.get('datablob', None)
        shared = request.POST.get('share', False)
        if not dataBlob or not url or not name:
            return HttpResponseBadRequest('name and data are required but both were not provided')
        try:
            newpage = SavedPage(user_id=request.user.id,
				project_id = request.session["projectID"],
				url = url,
                                name = name,
				description = description,
				blob = dataBlob,
				shared = shared)
            newpage.save()
	    return HttpResponse('your page was successfully added to the archive')
        except Exception, e:
            #return HttpResponseBadRequest('invalid data was provided')
            return HttpResponseBadRequest("%s" % str(e))
        return HttpResponse("<p>Description: "+description+"</p><p>Blob:</p>"+dataBlob)
    else: 
        return HttpResponseNotAllowed(['POST'])

@login_required
@activeproject
def fetch(request, archive_id):
    my_object = get_object_or_404(SavedPage.objects.filter(project_id=request.session["projectID"], pk=archive_id), Q(user=request.user.id)|Q(shared=True) )
    return HttpResponse(my_object.blob, content_type='application/json')


@login_required
@activeproject
def list(request):
    params = {}
    mypages = SavedPage.objects.filter(project_id=request.session["projectID"], user_id=request.user.id)
    sharedpages = SavedPage.objects.filter(project_id=request.session["projectID"], shared=True).exclude(user_id=request.user.id)
    params['mypages'] = mypages
    params['sharedpages'] = sharedpages
    return render(request, "ListSavedPages.html", params)

@login_required
@activeproject
def toggleShare(request):
    try:
        archive_id = request.GET.get('id', None)
        archive_id = int(archive_id)
    except:
        archive_id = -1
    myobject = get_object_or_404(SavedPage, pk=archive_id)
    if myobject.user_id != request.user.id:
        return HttpResponseForbidden("only the person who saved the page can alter the sharing status")
    if myobject.project_id != request.session["projectID"]:
        return HttpResponseForbidden("only saved pages for the active project may be modified")
    myobject.shared = not myobject.shared
    myobject.save()
    return HttpResponse("Set the shared status for \"%s\" to \"%s\"" % (myobject.name, myobject.shared) )

@login_required
@activeproject
def delete(request):
    try:
        archive_id = request.GET.get('id', None)
        archive_id = int(archive_id)
    except:
        archive_id = -1
    myobject = get_object_or_404(SavedPage, pk=archive_id)
    if myobject.user_id != request.user.id:
        return HttpResponseForbidden("only the person who saved the page can delete it")
    if myobject.project_id != request.session["projectID"]:
        return HttpResponseForbidden("only saved pages for the active project may be modified")
    myobject.delete()
    return HttpResponse("saved page \"%s\" was removed" % (myobject.name) )
