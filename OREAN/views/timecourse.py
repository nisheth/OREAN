from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import simplejson as json
import time
import os
import numpy as np
from api import internal
from api.models import *
from OREAN.views import SCRIPTPATH
from OREAN.decorators import *

@login_required
@activeproject
def viewTimecourseInTable(request):
  params = {}
  params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
  params['attributes'] = sorted([x.name for x in internal.ListAttributes(request, {'projectID': [request.session['projectID']]})])
  if request.method == "POST":
     name = request.POST.get('query', None)
     attr = request.POST.get('attribute', None)
     if name and attr:
       query = Query.objects.get(project=request.session['projectID'], name=name) 
       samples = query.expandsamples
       svm = SubjectMap.objects.filter(sample__in=samples)
       subjects = svm.values_list('subject', flat=True)
       params['subjects'] = {}
       for subj in subjects:
          params['subjects'][subj] = []
          visits = svm.filter(subject = subj).values_list('visit', flat=True).distinct()
          data = {}
          data['samples'] = []
          for v in visits:
             data['id'] = v
             data['samples']+=svm.filter(subject = subj, visit=v).values_list('sample', flat=True).distinct() 
          params['subjects'][subj].append(data)
  return render(request, 'viewTimecourseInTable.html', params)
