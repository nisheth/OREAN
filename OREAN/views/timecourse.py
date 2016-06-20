from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
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
from collections import Counter

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

@login_required
@activeproject
def mostAbundantOverTime(request):
    params = {}
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    if request.method=='POST':
        query = request.POST.get('query', None)
        dataset = request.POST.get('dataset', None)
        method = request.POST.get('method', None)
        category = request.POST.get('category', None)
        if not query:
            return HttpResponseBadRequest(json.dumps("query is a required argument"), content_type='application/json') 
        if not dataset:
            return HttpResponseBadRequest(json.dumps("dataset is a required argument"), content_type='application/json') 
        if not method:
            return HttpResponseBadRequest(json.dumps("method is a required argument"), content_type='application/json') 
        if not category:
            return HttpResponseBadRequest(json.dumps("category is a required argument"), content_type='application/json') 
	
	queryobj = Query.objects.get(project_id=request.session['projectID'], name=query)
	samplelist = queryobj.expandsamples
        subjects = Attributes.objects.filter(project_id=request.session['projectID'], sample__in=samplelist, field='tssubject.').values_list('value', flat=True)
        if not subjects:
            return HttpResponseBadRequest(json.dumps("project does not have timeseries information"), content_type='application/json')
        allsamples = Attributes.objects.filter(project_id=request.session['projectID'], field='tssubject.', value__in=subjects).values('sample', 'value')
        subjectmap = {}
        for s in allsamples:
            subjectmap.setdefault(s['sample'], {})
            subjectmap[s['sample']]['subject'] = s['value']
        timepoints = Attributes.objects.filter(project_id=request.session['projectID'], field='tstimepoint.', sample__in=subjectmap.keys()).values('sample', 'value')
        for s in timepoints:
            subjectmap[s['sample']]['timepoint'] = float(s['value'])

	mostAbundant = {}
        featureCount = Counter()
        for sample in subjectmap.keys():
	    try: dataObjs = Analysis.objects.filter(project_id=request.session['projectID'], dataset=dataset, method=method, category=category, sample=sample).order_by('-profile')[:3]
            except: continue
            for rank, dataObj in enumerate(dataObjs, start=1):
                mostAbundant.setdefault(sample, [])
                mostAbundant[sample].append((dataObj.entity, dataObj.profile, rank))
                featureCount[dataObj.entity] += 1
        topFeatures = {}
        for x,y in featureCount.most_common(9):
            topFeatures[x] = y
        resp = []
        for sample in mostAbundant:
            for entryrank in mostAbundant[sample]:
                entity, abundance, rank = entryrank
                if entity not in topFeatures:
                    entity = 'Other'
                resp.append({'subject': subjectmap[sample]['subject'], 'feature': entity, 'value': abundance, 'timepoint': subjectmap[sample]['timepoint'], 'sample': sample, 'rank': rank})
        return HttpResponse(json.dumps(resp), content_type='application/json')
    return render(request, 'mostAbundantOverTime.html', params)
