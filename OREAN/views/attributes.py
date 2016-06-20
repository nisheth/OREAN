from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from . import myutils
import json
from OREAN.decorators import *
from api import internal
from api.models import Query, Attributes

@login_required
@activeproject
def main(request):
    params = {}
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    kwargs = dict(request.GET)
    kwargs['projectID'] = [request.session['projectID']]
    params['attributes'] = sorted([x.name for x in internal.ListAttributes(request, kwargs)])
    if request.method=='POST':
        queryname = request.POST.get('query') or None
        attribute = request.POST.get('attribute') or 'Race'
        if not queryname: return render(request, 'home.html', params)
        params['feedback'] = 'Query selected: "%s"' % queryname
        query = internal.ListQueries(request, {'projectID': [request.session['projectID']], 'full': [True]})
        if not query or not len(query): return render(request, 'home.html', params)
        else: query = query[0]
        samplelist = myutils.fieldexpand(query['results'])
        dataset =  internal.ShowDistribution(request,{'queryname': [queryname], 'projectID': [query['project_id']], 'attribute': [attribute,],})
        jsondata = {'key': attribute, 'values': []}
        for d in sorted(dataset[1:], key=lambda x: x[0]):
            tmp = {'label': d[0], 'value': d[1]}
            jsondata['values'].append(tmp)
        params['data'] = dataset
        params['json'] = json.dumps([jsondata])
        params['selectedquery'] = queryname
        params['selectedattribute'] = attribute
        if request.POST.get('format') =='json': return HttpResponse(params['json'], content_type="application/json")
        #params['data'] = sorted(dataset, key=lambda x: x[1])
        #params['data'] = sorted(params['data'], key=lambda x: x[5])
    return render(request, 'attributes.html', params)

@login_required
@activeproject
def timeseries(request):
    params = {}
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    kwargs = {}
    kwargs['projectID'] = [request.session['projectID']]
    params['attributes'] = sorted([x.name for x in internal.ListAttributes(request, kwargs)])
    if request.method=='POST':
        queryname = request.POST.get('query') or None
        attribute = request.POST.get('attribute') or 'Race'
        if not queryname: return render(request, 'home.html', params)
	query = Query.objects.get(project_id=request.session['projectID'], name=queryname)
        samplelist = query.expandsamples
        subjects = Attributes.objects.filter(project_id=request.session['projectID'], sample__in=samplelist, field='tssubject.').values_list('value', flat=True)
        allsamples = Attributes.objects.filter(project_id=request.session['projectID'], field='tssubject.', value__in=subjects).values('sample', 'value')
        subjectmap = {}
        for s in allsamples:
            subjectmap.setdefault(s['sample'], {})
            subjectmap[s['sample']]['subject'] = s['value']
        timepoints = Attributes.objects.filter(project_id=request.session['projectID'], field='tstimepoint.', sample__in=subjectmap.keys()).values('sample', 'value')
        for s in timepoints:
            subjectmap[s['sample']]['timepoint'] = float(s['value'])
        attributedata = Attributes.objects.filter(project_id=request.session['projectID'], sample__in=subjectmap.keys(), field=attribute).values('sample', 'value')
        for a in attributedata:
            subjectmap[a['sample']]['feature'] = a['value']
        resp = []
        for sample in subjectmap:
            try:
                resp.append( {'subject': subjectmap[sample]['subject'], 'timepoint': subjectmap[sample]['timepoint'], 'feature': subjectmap[sample]['feature'], 'sample': sample} )
            except: continue
        return HttpResponse(json.dumps(resp), content_type="application/json")
    return render(request, 'metadataTimeline.html', params)

