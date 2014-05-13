from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from . import myutils
import json

@login_required
def main(request):
    params = {}
    params['queries'] = myutils.call_api(request, 'ListQueries')
    params['attributes'] = sorted([x['name'] for x in myutils.call_api(request, 'ListAttributes', params = {'projectID': 1})])
    if request.method=='POST':
        queryname = request.POST.get('query') or None
        attribute = request.POST.get('attribute') or 'Race'
        if not queryname: return render(request, 'home.html', params)
        params['feedback'] = 'Query selected: "%s"' % queryname
        query = myutils.call_api(request, 'ListQueries', params={'queryname': queryname, 'full': True})
        if not query or not len(query): return render(request, 'home.html', params)
        else: query = query[0]
        samplelist = myutils.fieldexpand(query['results'])
        #dataset =  myutils.call_api(request, 'GetDataset', params={'queryname': request.POST.get('query'), 'projectID': query['project_id'], 'dataset': 'Data-16s', 'method': 'RDP-0-8', 'category': 'genus'})
        dataset =  myutils.call_api(request, 'ShowDistribution', params={'queryname': queryname, 'projectID': query['project_id'], 'attribute': [attribute,],})
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
    return render(request, 'home.html', params)
