from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import simplejson as json
import time
import os
from api import internal

@login_required
def alpha(request):
    params = {}
    params['queries'] = myutils.call_api(request, 'ListQueries')
    querynames = request.GET.getlist('query') or None
    if querynames:
        datapoints = []
        outlierpoints = []
        count = 0
        for query in querynames:
            entities = []
            datahash = {}
            dataset =  internal.GetDataset(request, params={'queryname': [query], 'projectID': [1], 'dataset': ['Data-16s'], 'category': ['genus'], 'method': ['RDP-0-5']})
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
            boxplot = myutils.runRscript('/home/MiRA/Rscripts/alphaDiversity.R', filename)
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
def beta(request):
    params = {}
    params['queries'] = myutils.call_api(request, 'ListQueries')
    querynames = request.GET.getlist('query') or None
    if querynames:
        datapoints = []
        outlierpoints = []
        count = 0
        for query in querynames:
            entities = []
            samples = []
            datahash = {}
            dataset =  internal.GetDataset(request, params={'queryname': [query], 'projectID': [1], 'dataset': ['Data-16s'], 'category': ['genus'], 'method': ['RDP-0-5']})
            for d in dataset:
                if d.entity not in entities:
                    entities.append(d.entity)
                if d.sample not in datahash: 
                    datahash[d.sample] = {}
                    samples.append(d.sample)
                datahash[d.sample][d.entity] = d.numreads
            filename = "/tmp/%s-%d.txt" %(request.user.username, int(time.time()))
            with open(filename, 'w') as f:
                for sample in samples: f.write(','+str(sample))
                f.write('\n')
                for taxa in entities:
                    mycontent = taxa
                    for sample in samples:
                        mycontent+=','
                        if taxa in datahash[sample]: mycontent+=str(datahash[sample][taxa])
                        else: mycontent += str('0')
                    mycontent+='\n'
                    f.write(mycontent)
            boxplot = myutils.runRscript('/home/MiRA/Rscripts/betaDiversity.R', filename)
            boxplot,outliers = boxplot.split('\n')[:2]
            boxplot = boxplot.split(',')
            outliers = outliers.split(',')
            if len(boxplot): boxplot = [float(x) for x in boxplot]
            if len(outliers): [outlierpoints.append([count,float(x)]) for x in outliers if x != '']
            os.remove(filename)
            datapoints.append(boxplot)
            count+=1
        finaldata = [querynames, datapoints, outlierpoints]
        return HttpResponse(json.dumps(finaldata), content_type="application/json")
    return render(request, 'beta.html', params)
