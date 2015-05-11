from django.db.models import Max, Min
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from MiRA.decorators import *
from api.models import *
from api import internal
import traceback

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
        minthresh = int(request.POST.get('minthresh', 0))
        maxthresh = int(request.POST.get('maxthresh', 5))
        minSamplePerc = int(request.POST.get('minSamplePerc', 5))
        maxSamplePerc = int(request.POST.get('maxSamplePerc', 10))
        query = Query.objects.get(project=request.session['projectID'], name=queryname) 
        querysamples = query.expandsamples
        queryset = Analysis.objects.filter(project=request.session['projectID'], method=method, category=category, sample__in=querysamples)
        rareCandidates = queryset.values('entity').annotate(maxprofile=Max('profile')).annotate(minprofile=Min('profile')).order_by('-maxprofile').filter(maxprofile__lte=maxthresh, minprofile__gte=minthresh)
        rareTaxa = []
        for entry in rareCandidates:
            samplesWithTaxa = queryset.filter(entity=entry['entity']).count()
            percentPresence = 100.0*samplesWithTaxa / len(rareCandidates)
            if percentPresence >= minSamplePerc and percentPresence <= maxSamplePerc:
                entry['samplesWithTaxa'] = samplesWithTaxa
                entry['percentPresence'] = percentPresence
                rareTaxa.append(entry)
        params['minthresh'] = minthresh
        params['maxthresh'] = maxthresh
        params['minSamplePerc'] = minSamplePerc
        params['maxSamplePerc'] = maxSamplePerc
        params['rareCandidates'] = len(rareCandidates)
        params['rareTaxa'] = rareTaxa
      except:
        msg = "%s" % traceback.format_exc()
        messages.add_message(request, messages.ERROR, msg)
    return render(request, 'taxaInvestigator.html', params)
