from django.shortcuts import render
from OREAN.decorators import *
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from . import myutils
from api import * 
from api import internal
import json

@login_required
@activeproject
def main(request):
    params = {}
    params['queries'] = []
    params['pubqueries'] = []
    queries = internal.ListQueries(request, {'projectID': [request.session['projectID']], 'full': [True]})
    for q in queries:
         tmp = {}
         tmp['name'] = q['name']
         tmp['numsamples'] = q['number of samples']
         tmp['numsubjects'] = q['number of subjects']
         tmp['numvisits'] = q['number of visits']
         tmp['share'] = bool(q['share'])
         tmp['user'] = User.objects.get(pk=q['user_id']).username
         tmp['project'] = q['project_id']
         tmp['description'] = q['description']
         if request.user.username == tmp['user']: params['queries'].append(tmp)
         else: params['pubqueries'].append(tmp)
    return render(request, 'managequeries.html', params)
