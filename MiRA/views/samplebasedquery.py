from django.shortcuts import render, redirect
from MiRA.decorators import *
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from . import myutils
import json
from api import internal
from api import *
@login_required
@activeproject
def main(request):
    params = {}
    params['projects'] = internal.ListProjects(request)
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
        finalquery = internal.BuildQueryFromList(request, {'projectID': [projectID], 'queryname': [queryname], 'description': [description], 'sample': samplelist})
        return redirect('managequeries')
    return render(request, 'samplebasedquery.html', params)
