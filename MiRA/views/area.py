from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import json
from api import internal 
import time
@login_required
def main(request):
    params = {}
    params['queries'] = myutils.call_api(request, 'ListQueries')
    if request.method=='POST':
        queryname = request.POST.get('query') or None
        dataset = request.POST.get('dataset') or None
        method = request.POST.get('method') or None
        category = request.POST.get('category') or None
        if not queryname or not dataset or not method or not category: return render(request, 'profile.html', params)
        params['feedback'] = 'Query selected: "%s"' % queryname
        query = myutils.call_api(request, 'ListQueries', params={'queryname': queryname, 'full': True})
        if not query or not len(query): return render(request, 'profile.html', params)
        else: query = query[0]
        samplelist = myutils.fieldexpand(query['results'])
        #dataset =  myutils.call_api(request, 'GetDataset', params={'queryname': request.POST.get('query'), 'projectID': query['project_id'], 'dataset': 'Data-16s', 'method': 'RDP-0-8', 'category': 'genus'})
        #dataset =  myutils.call_api(request, 'GetDataset', params={'queryname': queryname, 'projectID': query['project_id'], 'dataset': dataset, 'category': category, 'method': method})
        #header = dataset.pop(0)
        mark = time.time()
        dataset =  internal.GetDataset(request, params={'queryname': [queryname], 'projectID': [query['project_id']], 'dataset': [dataset], 'category': [category], 'method': [method]})
        jsondata = []
        magichash = {}
        maxhash = {}
        sorterhash = {}
        entityorder = []
#        for d in dataset:
#            if d[1] not in maxhash or d[7] > maxhash[d[1]]['val']: maxhash[d[1]] = {'entity': d[5], 'val': d[7]}
#            if d[5] in magichash: magichash[d[5]][d[1]] = d[7]
#            else: magichash[d[5]] = {d[1]:d[7]}
        for d in dataset:
            if d.profile < 1: continue
            if d.sample not in maxhash or d.profile > maxhash[d.sample]['val']: maxhash[d.sample] = {'entity': d.entity, 'val': d.profile}
            if d.entity in magichash: magichash[d.entity][d.sample] = d.profile
            else: magichash[d.entity] = {d.sample:d.profile}
        for sample in sorted(maxhash, key=lambda x: maxhash[x]['val'], reverse=True):
            if maxhash[sample]['val'] < 5: continue 
            if maxhash[sample]['entity'] not in sorterhash: 
                sorterhash[maxhash[sample]['entity']] = [sample]
                entityorder.append(maxhash[sample]['entity'])
            else: sorterhash[maxhash[sample]['entity']].append(sample)
        samplelist = []
        for element in entityorder:
            for x in sorterhash[element]: samplelist.append(x)
        for m in magichash:
            tmp = {'name': m, 'data': []}
            for i,s in enumerate(samplelist):
                if s in magichash[m]: tmp['data'].append(magichash[m][s])
                else: tmp['data'].append(0)
            jsondata.append(tmp)
        params['json'] = json.dumps([samplelist, jsondata])
        #print "Data Fetch took %.02f seconds" %(time.time() - mark)
        #print "Taxa Count: %d" % len(entityorder)
        #print len(dataset.values_list('entity', flat=True).distinct())
        return HttpResponse(params['json'], content_type="application/json")
    return render(request, 'profile.html', params)

