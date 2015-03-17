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
            dataset =  internal.GetDataset(request, params={'queryname': [queryname], 'projectID': [query['project_id']], 'dataset': [datasetname], 'category': [category], 'method': [method]})
            with open(fpath, 'w') as f:
              f.write('sample,taxa,profile\n')
              #for d in dataset.order_by('sample'):
              # if d.profile > 0.1: f.write("%s,%s,%f\n" % ( d.sample, d.entity, d.profile ))

              taxahash = dict()
              samplemax = dict()
              datahash = dict()
              for d in dataset:
                if d.profile < 0.1: continue
                if d.entity not in taxahash or d.profile > taxahash[d.entity]: 
                  taxahash[d.entity] = d.profile
                if d.entity not in datahash: datahash[d.entity] = dict()
                if d.sample not in samplemax: 
                  samplemax[d.sample] = {'e': d.entity, 'p': d.profile}
                  datahash[d.entity][d.sample] = {d.entity: d.profile} 
                elif d.profile > samplemax[d.sample]['p']:
                  current = samplemax[d.sample]
                  samplemax[d.sample] = {'e': d.entity, 'p': d.profile}
                  sampledata = datahash[current['e']][d.sample]
                  del datahash[current['e']][d.sample]
                  sampledata[d.entity] = d.profile
                  datahash[samplemax[d.sample]['e']][d.sample] = sampledata
                else:
                  datahash[samplemax[d.sample]['e']][d.sample][d.entity] = d.profile
              for t, tmax in sorted(taxahash.items(), key=lambda x: -x[1]):
                for sample, data in sorted(datahash[t].items(), key= lambda x: -x[1][t]):
                  for entity, profile in sorted(data.items(), key=lambda x: x[1]):
                    f.write("%s,%s,%s\n" % (sample, entity, profile)) 
        return HttpResponse(json.dumps(furl), content_type="application/json")
    return render(request, 'stackedbars.html', params)

