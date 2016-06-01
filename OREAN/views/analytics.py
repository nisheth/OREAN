from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from . import myutils
import json
from OREAN.decorators import *
from api import *
from api import internal
@login_required
@activeproject
def main(request):
    params = {}
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    params['attributes'] = sorted([x.name for x in internal.ListAttributes(request, {'projectID': [request.session['projectID']]})])
    return render(request, 'analytics.html', params)

@login_required
@activeproject
def comparison(request):
    params = {}
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    params['attributes'] = sorted([x.name for x in internal.ListAttributes(request, {'projectID': [request.session['projectID']]})])
    return render(request, 'visualComparison.html', params)

