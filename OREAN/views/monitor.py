from django.http import HttpResponse, HttpResponseNotFound, Http404

def resources(request):
    if not request.user.is_superuser:
        #return HttpResponseNotFound('<h1>404 page not found</h1>')
        raise Http404('page not found')
    response = HttpResponse()
    path = request.get_full_path()
    path = path.replace('monitorix', 'sysmonitor', 1)
    response['X-Accel-Redirect'] = path
    return response
