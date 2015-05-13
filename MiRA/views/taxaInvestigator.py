from django.db.models import Max, Min, Count
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from MiRA.decorators import *
from api.models import *
from api import internal
import traceback, json

@login_required
@activeproject
def getRareTaxa(request):
    params = dict()
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    if request.method == 'POST':
      try:
        queryname = request.POST.get('query', None)
        datasetname = request.POST.get('dataset', None)
        method = request.POST.get('method', None)
        category = request.POST.get('category', None)
        minthresh = float(request.POST.get('minthresh', 0))
        maxthresh = float(request.POST.get('maxthresh', 5))
        minSamplePerc = float(request.POST.get('minSamplePerc', 5))
        maxSamplePerc = float(request.POST.get('maxSamplePerc', 10))
        query = Query.objects.get(project=request.session['projectID'], name=queryname) 
        querysamples = query.expandsamples
        numSamples = len(querysamples)
        minSampleCount = numSamples * (minSamplePerc / 100.0)
        maxSampleCount = numSamples * (maxSamplePerc / 100.0)
        queryset = Analysis.objects.filter(project=request.session['projectID'], method=method, category=category, sample__in=querysamples)
        rareCandidates = queryset.values('entity').annotate(maxprofile=Max('profile')).annotate(
                                                            minprofile=Min('profile')).annotate(
                                                            mycount=Count('entity')).filter(
                                                            maxprofile__lte=maxthresh, minprofile__gte=minthresh, mycount__gte=minSampleCount, mycount__lte=maxSampleCount).values_list(
                                                            'entity', 'minprofile', 'maxprofile', 'mycount').order_by(
                                                            '-mycount') 
        resp = dict()
        resp['minthresh'] = minthresh
        resp['maxthresh'] = maxthresh
        resp['minSamplePerc'] = minSamplePerc
        resp['maxSamplePerc'] = maxSamplePerc
        resp['minSampleCount'] = minSampleCount
        resp['maxSampleCount'] = maxSampleCount
        resp['rareCandidates'] = len(rareCandidates)
        resp['numSamples'] = numSamples
        resp['rareTaxa'] = list(rareCandidates)
        return HttpResponse(json.dumps(resp), content_type='application/json')
      except:
        msg = "%s" % traceback.format_exc()
        messages.add_message(request, messages.ERROR, msg)
    return render(request, 'taxaInvestigator.html', params)
