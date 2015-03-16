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
    querynamelist = request.GET.getlist('query') or None
    inputdataset = request.GET.get('dataset') or None
    method = request.GET.get('method') or None
    category = request.GET.get('category') or None
    bothcount = 0
    mydata = {}
    sa = {}
    if querynamelist:
        if not len(querynamelist) == 2 or not inputdataset or not method or not category: return HttpResponse("required GET parameters: query, dataset, method, category, query2" , content_type='text/plain')
        queryname, queryname2 = querynamelist
        #query1dataset =  internal.GetDataset(request, params={'queryname': [queryname], 'projectID': [request.session['projectID']], 'dataset': [inputdataset], 'category': [category], 'method': [method]})
        #query2dataset =  internal.GetDataset(request, params={'queryname': [queryname2], 'projectID': [request.session['projectID']], 'dataset': [inputdataset], 'category': [category], 'method': [method]})
        query1dataset =  internal.GetDataset(request, params={'queryname': [queryname], 'projectID': [request.session['projectID']], 'dataset': [inputdataset], 'method': [method]})
        query2dataset =  internal.GetDataset(request, params={'queryname': [queryname2], 'projectID': [request.session['projectID']], 'dataset': [inputdataset], 'method': [method]})
        query1samples = internal.ListQueries(request, {'projectID': [request.session['projectID']], 'full': [True], 'queryname': [queryname]})[0]['results'].split(',')
        query2samples = internal.ListQueries(request, {'projectID': [request.session['projectID']], 'full': [True], 'queryname': [queryname2]})[0]['results'].split(',')
        totalsamples = list(set(query1samples+query2samples))
        dataset = query1dataset | query2dataset
        for s in totalsamples:
            if s in query1samples and s in query2samples: 
                sa[s] = "Both"
                bothcount+=1
            elif s in query1samples and s not in query2samples:
                sa[s] = queryname
            elif s not in query1samples and s in query2samples:
	        sa[s] = queryname2
            else: 
                return HttpResponse(json.dumps({'msg': "Could not determine how to group sample '%s'. Aborting LefSE analysis." % s, 'data': False}), content_type='application/json')
        if bothcount == len(totalsamples): return HttpResponse(json.dumps({'msg': "Queries have the same sample composition. Cannot perform an analysis", 'data': False}), content_type='application/json')
        samples = list(set(dataset.values_list('sample', flat=True)))
        for row in dataset:
            #if row.entity in mydata: mydata[row.entity][row.sample] = row.profile/100
            #else: mydata[row.entity] = {row.sample: row.profile/100}
            if row.taxatree.full_tree in mydata: mydata[row.taxatree.full_tree][row.sample] = row.profile/100
            else: mydata[row.taxatree.full_tree] = {row.sample: row.profile/100}
        inputfile = "/tmp/%d-%d-lefse.txt" %(request.user.pk, int(time.time()))
        formatfile = inputfile+".format"
        resultfile = inputfile+".result"
        with open(inputfile, 'w') as f:
            f.write("QueryStatus")
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
        lefseresp = "<strong>Query 1:</strong> "+queryname+"<br><strong>Query 2:</strong> "+queryname2+"<hr>"+lefseresp
        #lefseresp = myutils.runCmd("python /home/mira/MiRA/scripts/misc/lefse/run_lefse.py "+ formatfile+" "+resultfile)
        rows = ""
        with open(resultfile, 'r') as f:
            rows = f.read()
        #os.remove(inputfile)
        #os.remove(formatfile)
        #os.remove(resultfile)
        return HttpResponse(json.dumps({'msg': lefseresp, 'data': rows}), content_type='application/json')
    return render(request, "lefse2.html", params)
