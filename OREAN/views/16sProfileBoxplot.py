from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import simplejson as json
import time
import os
from api import internal
from OREAN.views import SCRIPTPATH
from operator import itemgetter
from OREAN.decorators import *

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

@login_required
@activeproject
def main(request):
    CUTOFF=20
    params = {}
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    querynames = request.GET.getlist('query') or None
    querynames = request.GET.getlist('query') or None
    inputdataset = request.GET.get('dataset') or None
    category = request.GET.get('category') or None
    method = request.GET.get('method') or None
    print querynames
    if querynames:
        if not querynames or not inputdataset or not method or not category: return render(request, 'alpha.html', params)
        #entities = []
        entities = myutils.topTaxa(querynames, inputdataset, method, category, CUTOFF)
        elementOfGlory = {}
        for query in querynames:
            filename = "/tmp/%s-%d.txt" %(request.user.pk, int(time.time()))
            datahash = {}
            for ent in entities: datahash[ent] = []
            longest_list = -1
            print "Query:", query
            dataset = internal.GetDataset(request, params={'queryname': [query], 'projectID': [request.session['projectID']], 'dataset': [inputdataset], 'category': [category], 'method': [method], 'entity': entities})
            for d in dataset:
                taxa = d.entity
                datahash[taxa].append(d.profile)
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
            boxplot = myutils.runRscript('16sProfilesBoxplot.R', filename)
            os.remove(filename)
            tmp = boxplot.split('\n')
            boxplot = []
            for bp in tmp: 
              if bp == "": continue
              tmp2 = bp.split(',')
              tmp2 = [float(s) if isfloat(s) else s for s in tmp2]
              if tmp2[0] in elementOfGlory: elementOfGlory[tmp2[0]][query] = tmp2 
              else: elementOfGlory[tmp2[0]] = {query : tmp2}
        finaldata = [ [], [], [] ]
        i = 0
        for en in entities:
          for query in querynames:
            bp = elementOfGlory[en][query]
            bp.pop(0)
            if len(bp[5:]): [finaldata[2].append([i,float(x)]) for x in bp[5:] if x != '']
            finaldata[0].append(en)
            finaldata[1].append(bp[:5])
            i+=1  
        return HttpResponse(json.dumps(finaldata), content_type="application/json")
    return render(request, '16sProfileBoxplot.html', params)
