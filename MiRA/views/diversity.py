from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import simplejson as json
import time
import os
from api import internal
from MiRA.views import SCRIPTPATH
from MiRA.decorators import *

@login_required
@activeproject
def alpha(request):
    params = {}
    params['queries'] = myutils.call_api(request, 'ListQueries')
    querynames = request.GET.getlist('query') or None
    inputdataset = request.GET.get('dataset') or None
    method = request.GET.get('method') or None
    category = request.GET.get('category') or None
    if querynames:
        if not querynames or not inputdataset or not method or not category: return render(request, 'alpha.html', params)
        datapoints = []
        outlierpoints = []
        count = 0
        for query in querynames:
            entities = []
            datahash = {}
            dataset =  internal.GetDataset(request, params={'queryname': [query], 'projectID': [request.session['projectID']], 'dataset': [inputdataset], 'category': [category], 'method': [method]})
            for d in dataset:
                if d.entity not in entities:
                    entities.append(d.entity)
                if d.sample not in datahash: datahash[d.sample] = {}
                datahash[d.sample][d.entity] = d.numreads
            filename = "/tmp/%s-%d.txt" %(request.user.username, int(time.time()))
            with open(filename, 'w') as f:
                for taxa in entities: f.write(','+str(taxa))
                f.write('\n')
                for sample in datahash:
                    mycontent = sample
                    for taxa in entities:
                        mycontent+=','
                        if taxa in datahash[sample]: mycontent+=str(datahash[sample][taxa])
                        else: mycontent += str('0')
                    mycontent+='\n'
                    f.write(mycontent)
            boxplot = myutils.runRscript('alphaDiversity.R', filename)
            boxplot,outliers = boxplot.split('\n')[:2]
            boxplot = boxplot.split(',')
            outliers = outliers.split(',')
            if len(boxplot): boxplot = [float(x) for x in boxplot]
            if len(outliers): outliers = [[count,float(x)] for x in outliers if x != '']
            os.remove(filename)
            datapoints.append(boxplot)
            outlierpoints.append(outliers)
            count+=1
        finaldata = [querynames, datapoints, outlierpoints]
        return HttpResponse(json.dumps(finaldata), content_type="application/json")
    return render(request, 'alpha.html', params)

@login_required
@activeproject
def beta(request):
    params = {}
    params['queries'] = myutils.call_api(request, 'ListQueries')
    querynames = request.GET.getlist('query') or None
    inputdataset = request.GET.get('dataset') or None
    method = request.GET.get('method') or None
    category = request.GET.get('category') or None
    if querynames:
        if not querynames or not inputdataset or not method or not category: return render(request, 'alpha.html', params)
        datapoints = []
        outlierpoints = []
        count = 0
        for query in querynames:
            entities = []
            samples = []
            datahash = {}
            dataset =  internal.GetDataset(request, params={'queryname': [query], 'projectID': [request.session['projectID']], 'dataset': [inputdataset], 'category': [category], 'method': [method]})
            for d in dataset:
                if d.entity not in entities:
                    entities.append(d.entity)
                if d.sample not in datahash: 
                    datahash[d.sample] = {}
                    samples.append(d.sample)
                datahash[d.sample][d.entity] = d.numreads
            filename = "/tmp/%s-%d.txt" %(request.user.pk, int(time.time()))
            with open(filename, 'w') as f:
                #for sample in samples: f.write(','+str(sample))
                f.write('%d,%d\n' %(len(entities), len(samples)))
                for taxa in entities:
                    mycontent = taxa
                    for sample in samples:
                        mycontent+=','
                        if taxa in datahash[sample]: mycontent+=str(datahash[sample][taxa])
                        else: mycontent += str('0')
                    mycontent+='\n'
                    f.write(mycontent)
            #boxplot = myutils.runRscript('betaDiversity.R', filename)
            #boxplot = myutils.runPerl('braycurtis.pl', filename)
            boxplot = myutils.runC('braycurtis', filename)
            boxplot,outliers = boxplot.split('\n')[:2]
            boxplot = boxplot.split(',')
            outliers = outliers.split(',')
            if len(boxplot): boxplot = [float(x) for x in boxplot]
            if len(outliers): [outlierpoints.append([count,float(x)]) for x in outliers if x != '']
            #os.remove(filename)
            datapoints.append(boxplot)
            count+=1
        finaldata = [querynames, datapoints, outlierpoints]
        return HttpResponse(json.dumps(finaldata), content_type="application/json")
    return render(request, 'beta.html', params)
