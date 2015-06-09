from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import json, os
from api import internal
from api.models import Analysis, Attributes, Query
from OREAN.decorators import *
from OREAN.views import SCRIPTPATH
from OREAN.local_settings import MEDIA_URL as murl, MEDIA_ROOT as mroot
from hashlib import md5

@login_required
@activeproject
def manager(request):
    params = dict()
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    params['attributes'] = internal.ListAttributes(request, {'projectID': [request.session['projectID']]})
    if request.method == 'POST':
        queryname = request.POST.get('query', None)
        dataset = request.POST.get('dataset', None)
        method = request.POST.get('method', None)
        category=request.POST.get('category', None)
        metadatafield = request.POST.get('attribute', None)
        if not queryname or not dataset or not method or not category or not metadatafield:
            return HttpResponse(json.dumps('Please check that the input form is complete.'), content_type='application/json')
        query = Query.objects.get(project=request.session['projectID'], name=queryname)
        filename = md5(request.session['projectName']+query.name+dataset+method+category+metadatafield).hexdigest()+'.pdf'
        outputpath = mroot+filename
        outputurl = murl+filename
        if not os.path.isfile(outputpath):
            from rpy2 import robjects
            from api.models import Analysis, Attributes
            # fetch Analysis data of interest
            clusterScript = SCRIPTPATH+'r/hierarchicalClustering.R'
            robjects.r.source(clusterScript)
            clusterCommand = robjects.r['clusterSamples']
            
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
            metadata = Attributes.objects.filter(project=request.session['projectID'], field=metadatafield, sample__in=query.expandsamples).values_list('sample', 'value')
            metadata = zip(*metadata)
            
            # load metadata into R and merge with ordered samples
            metadataRdata = robjects.DataFrame({'samples': robjects.StrVector(metadata[0]), 
                                                metadatafield: robjects.StrVector(metadata[1])})
            
            clusterCommand(profileRdata, metadataRdata, outputpath)
        return HttpResponse(json.dumps(outputurl), content_type='application/json')
    return render(request, 'clustering.html', params)
