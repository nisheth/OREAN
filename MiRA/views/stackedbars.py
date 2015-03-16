from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import json
from api import internal 
import time, os
from MiRA.decorators import *
from MiRA.settings import MEDIA_URL as murl, MEDIA_ROOT as mroot

@login_required
@activeproject
def main(request):
    params = {}
    params['time'] = []
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    if request.method=='POST':
        start = time.time()
        queryname = request.POST.get('query') or None
        datasetname = request.POST.get('dataset') or None
        method = request.POST.get('method') or None
        category = request.POST.get('category') or None
        if not queryname or not datasetname or not method or not category: return render(request, 'profile.html', params)
        params['feedback'] = 'Query selected: "%s"' % queryname

        query = internal.ListQueries(request, {'projectID': [request.session['projectID']], 'full': [True], 'queryname': [queryname]})
        if not query or not len(query): return render(request, 'profile.html', params)
        else: query = query[0]
        filename = 'stackedbars.%d.%d.%s.%s.%s.csv' % ( query['id'], query['project_id'], datasetname, method, category )
        furl = murl + filename
        fpath = mroot + filename

        if not os.path.isfile(fpath):
            samplelist = myutils.fieldexpand(query['results'])
            mark = time.time()
            dataset =  internal.GetDataset(request, params={'queryname': [queryname], 'projectID': [query['project_id']], 'dataset': [datasetname], 'category': [category], 'method': [method]})
            entityorder = []
            datahash = {}
            with open(fpath, 'w') as f:
              f.write('sample,taxa,profile\n')
              for d in dataset.order_by('sample'):
               #if d.entity not in datahash: 
               #  entityorder.append(d.entity)
               #  datahash[d.entity] = []
               #datahash[d.entity].append(d)
               if d.profile > 0.1: f.write("%s,%s,%f\n" % ( d.sample, d.entity, d.profile ))
            #for taxa in entityorder:
            #  for row in datahash[taxa]:
            #    resp += "%s,%s,%f\n" % ( row.sample, row.entity, row.profile )
        return HttpResponse(json.dumps(furl), content_type="application/json")

        #jsondata = []
        #magichash = {}
        #maxhash = {}
        #sorterhash = {}
        #entityorder = []
        #first = True
        #for d in dataset:
        #    if first: 
        #        params['time'].append('parsed input and fetched API data: %.02f' %(time.time() - start))
        #        first=False
        #    if d.profile < 1: continue
        #    if d.sample not in maxhash or d.profile > maxhash[d.sample]['val']: maxhash[d.sample] = {'entity': d.entity, 'val': d.profile}
        #    if d.entity in magichash: magichash[d.entity][d.sample] = d.profile
        #    else: magichash[d.entity] = {d.sample:d.profile}
        #params['time'].append('computed max profile values: %.02f ' %(time.time() - start))
        #for sample in sorted(maxhash, key=lambda x: maxhash[x]['val'], reverse=True):
        #    if maxhash[sample]['val'] < 5: continue 
        #    if maxhash[sample]['entity'] not in sorterhash: 
        #        sorterhash[maxhash[sample]['entity']] = [sample]
        #        entityorder.append(maxhash[sample]['entity'])
        #    else: sorterhash[maxhash[sample]['entity']].append(sample)
        #params['time'].append('sorted taxa: %.02f' %(time.time() - start))
        #samplelist = []
        #for element in entityorder:
        #    for x in sorterhash[element]: samplelist.append(x)
        #params['time'].append('sorted samples: %.02f' %(time.time() - start))
        #for m in magichash:
        #    tmp = {'name': m, 'data': []}
        #    for i,s in enumerate(samplelist):
        #        if s in magichash[m]: tmp['data'].append(magichash[m][s])
        #        else: tmp['data'].append(0)
        #    jsondata.append(tmp)
        #params['time'].append('formatted data for JSON conversion: %.02f' %(time.time() - start))
        #params['json'] = json.dumps([samplelist, jsondata, params['time']])
        #return HttpResponse(params['json'], content_type="application/json")
    return render(request, 'stackedbars.html', params)

