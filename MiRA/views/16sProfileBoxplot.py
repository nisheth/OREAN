from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import simplejson as json
import time
import os
from api import internal
from MiRA.views import RPATH
from operator import itemgetter

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

@login_required
def main(request):
    CUTOFF=50
    params = {}
    params['queries'] = myutils.call_api(request, 'ListQueries')
    querynames = request.GET.getlist('query') or None
    print querynames
    if querynames:
        entities = []
        boxplot = ""
        for query in querynames:
            filename = "/tmp/%s-%d.txt" %(request.user.username, int(time.time()))
            datahash = {}
            longest_list = -1
            print "Query:", query
            dataset =  internal.GetDataset(request, params={'queryname': [query], 'projectID': [1], 'dataset': ['Data-16s'], 'category': ['genus'], 'method': ['RDP-0-5']})
            for d in dataset:
                taxa = d.entity
                if taxa not in datahash:
                    if d.profile == 0: continue
                    datahash[taxa] = [d.profile]
                else: datahash[taxa].append(d.profile)
                if len(datahash[taxa]) > longest_list: longest_list = len(datahash[taxa])
            with open(filename, 'a') as f:
                for taxa in datahash: 
                    f.write(str(taxa))
                    count = 0
                    for profile in datahash[taxa]: 
                        count +=1
                        f.write(','+str(profile))
                    while count < longest_list: 
                        f.write(','+str('0'))
                        count+=1
                    f.write('\n')
            boxplot += myutils.runRscript('16sProfilesBoxplot.R', filename)
            #os.remove(filename)
        tmp = boxplot.split('\n')
        boxplot = []
        for bp in tmp: 
          if bp == "": continue
          tmp2 = bp.split(',')
          tmp2 = [float(s) if isfloat(s) else s for s in tmp2]
          boxplot.append(tmp2)
        boxplot = sorted(boxplot, key=itemgetter(3), reverse=True)
        outliers = []
        for i, bp in enumerate(boxplot[:CUTOFF]):
            entities.append(bp.pop(0))
            if len(bp[5:]): [outliers.append([i,float(x)]) for x in bp[5:] if x != '']
            boxplot[i] = bp[:5]
        finaldata = [entities[:CUTOFF], boxplot[:CUTOFF], outliers]
        return HttpResponse(json.dumps(finaldata), content_type="application/json")
    return render(request, '16sProfileBoxplot.html', params)
