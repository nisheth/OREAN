from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from . import myutils
import json

@login_required
def main(request):
    params = {}
    params['projects'] = myutils.call_api(request, 'ListProjects')
    if request.method=='POST':
        projectID = int(request.POST.get('project'))
        queryname = request.POST.get('queryname') or None
        description = request.POST.get('querydescription') or None
        tmplist = request.POST.get('sampleslist') or None
        tmplist = tmplist.split('\n')
        samplelist = []
        for sample in tmplist:
            sample = sample.strip()
            if len(sample) == 0: continue
            else: samplelist.append(sample)
        if not queryname or not projectID or not len(samplelist): return render(request, 'buildquery.html', params)
        print 'Views Description:', description
        finalquery = myutils.call_api(request, 'BuildQuery', params={'projectID': projectID, 'queryname': queryname, 'description': description, 'sample': samplelist}, is_post=True)
        return redirect('managequeries')
    return render(request, 'samplebasedquery.html', params)
