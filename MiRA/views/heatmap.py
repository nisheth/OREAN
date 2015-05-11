from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import json, os
from api import internal
from api.models import Analysis, Attributes, Query
from MiRA.decorators import *
from MiRA.views import SCRIPTPATH
from MiRA.local_settings import MEDIA_URL as murl, MEDIA_ROOT as mroot
from hashlib import md5
import numpy 

@login_required
@activeproject
def manager(request):
    params = dict()
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    if request.method == 'POST':
        resp = dict()
        queryname = request.POST.get('query', None)
        dataset = request.POST.get('dataset', None)
        method = request.POST.get('method', None)
        category=request.POST.get('category', None)
        count=request.POST.get('count', 20)
        if not queryname or not dataset or not method or not category:
            return HttpResponse(json.dumps('Please check that the input form is complete.'), content_type='application/json')
        query = Query.objects.get(project=request.session['projectID'], name=queryname)
        from rpy2 import robjects
        import rpy2.robjects.numpy2ri as rpyn
        # fetch Analysis data of interest
        heatmapScript = SCRIPTPATH+'r/heatmapDataCreator.R'
        robjects.r.source(heatmapScript)
        heatmapCommand = robjects.r['heatmapDataCreator']
        
        profiles1 = Analysis.objects.filter(project=request.session['projectID'], 
                                           dataset=dataset, 
                                           method=method, 
                                           category=category,
                                           sample__in=query.expandsamples).values_list('sample', 
                                                                                       'entity', 
                                                                                       'profile')
        
        # format analysis data and load into R                   
        profiles = zip(*profiles1)
        profileRdata = robjects.DataFrame({'samples': robjects.StrVector(profiles[0]), 
                                           'entity': robjects.StrVector(profiles[1]), 
                                           'profile': robjects.FloatVector(profiles[2])})
        processedMatrix = heatmapCommand(profileRdata, count)
        vector=rpyn.ri2numpy(processedMatrix)
        resp['rows'] = list(processedMatrix.rownames)
        resp['cols'] = list(processedMatrix.colnames)
        resp['maxVal'] = numpy.amax(vector) 
        resp['minVal'] = numpy.amin(vector) 
        resp['data'] = vector.tolist()
        return HttpResponse(json.dumps(resp), content_type='application/json')
    return render(request, 'heatmap.html', params)
