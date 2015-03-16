from django.shortcuts import render
from MiRA.decorators import *
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import simplejson as json
import time
import os
from api import internal
from MiRA.views import SCRIPTPATH


@login_required
@activeproject
def main(request):
    params = {}
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    params['attributes'] = internal.ListAttributes(request, {'projectID': [request.session['projectID']]})
    queryname = request.GET.get('query') or None
    inputdataset = request.GET.get('dataset') or None
    method = request.GET.get('method') or None
    category = request.GET.get('category') or None
    attribute = request.GET.get('attribute') or None
    mydata = {}
    sa = {}
    if queryname:
        if not queryname or not inputdataset or not method or not category: return HttpResponse("required GET parameters: query, dataset, method, category" , content_type='text/plain')
        dataset =  internal.GetDataset(request, params={'queryname': [queryname], 'projectID': [request.session['projectID']], 'dataset': [inputdataset], 'category': [category], 'method': [method]})
        attributes =  internal.GetData(request, {'queryname': [queryname], 'projectID': [request.session['projectID']], 'attribute': [attribute,],})
        attributes.pop(0)
        for a in attributes: sa[a[0]] = a[1]
        samples = list(set(dataset.values_list('sample', flat=True)))
        for row in dataset:
            if row.entity in mydata: mydata[row.entity][row.sample] = row.profile/100
            else: mydata[row.entity] = {row.sample: row.profile/100}
 
        inputfile = "/tmp/%d-%d-%s.txt" %(request.user.pk, int(time.time()), attribute.replace(' ', '_'))
        formatfile = inputfile+".format"
        resultfile = inputfile+".result"
        with open(inputfile, 'w') as f:
            f.write(attribute)
            for s in samples: 
                if s in sa: f.write("\t"+str(sa[s]).lower())
                else: f.write("\tNA")
            f.write("\nsubject_id")
            for s in samples: f.write("\t"+str(s))
            for e in sorted(mydata):
                f.write("\n"+e)
                for s in samples:
                    if s in mydata[e]: f.write("\t"+str(mydata[e][s]))
                    else: f.write("\t0")
        formatresp = myutils.runPython("lefse/format_input.py", inputfile, [formatfile, "-u2", "-o1000000"])
        lefseresp = myutils.runPython("lefse/run_lefse.py", formatfile, [resultfile]).strip()
        lefseresp = lefseresp.replace('\n', '<br />')
        lefseresp = "<strong>Query:</strong> "+queryname+"<br><strong>Attribute:</strong> "+attribute+"<hr>"+lefseresp
        #lefseresp = myutils.runCmd("python /home/mira/MiRA/scripts/misc/lefse/run_lefse.py "+ formatfile+" "+resultfile)
        rows = ""
        with open(resultfile, 'r') as f:
            rows = f.read()
        os.remove(inputfile)
        os.remove(formatfile)
        os.remove(resultfile)
        return HttpResponse(json.dumps({'msg': lefseresp, 'data': rows}), content_type='application/json')
    return render(request, "lefse.html", params)
