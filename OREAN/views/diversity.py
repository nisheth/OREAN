from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import simplejson as json
import time
import os
import numpy as np
from api import internal
from api.models import *
from OREAN.views import SCRIPTPATH
from OREAN.decorators import *

@login_required
@activeproject
def alpha2(request):
    params = {}
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
    querynames = request.GET.getlist('query') or None
    inputdataset = request.GET.get('dataset') or None
    method = request.GET.get('method') or None
    category = request.GET.get('category') or None
    if querynames:
        if not querynames or not inputdataset or not method or not category: return render(request, 'alpha2.html', params)
        datapoints = []
        outlierpoints = []
        count = 0
        for query in querynames:
            sampleslist = Query.objects.get(project=request.session['projectID'], name=query).expandsamples
            querydata = list(Calculation.objects.filter(project=request.session['projectID'], calculation='Alpha Diversity', dataset=inputdataset, method=method, category=category, sample__in=sampleslist).values_list('value', flat=True))
            querydata.sort()
            myarr = np.array(querydata)
            median = np.percentile(myarr, 50)
            lowerq = np.percentile(myarr, 25)
            upperq = np.percentile(myarr, 75)
            iqr = 1.5 * (upperq - lowerq)
            outliers = [[count, x] for x in querydata if x < lowerq-iqr or x > iqr+upperq]
            lowerx = [x for x in querydata if x > lowerq-iqr][0]
            upperx = [x for x in querydata if x < upperq+iqr][-1]
            datapoints.append([lowerx, lowerq, median, upperq, upperx])
            outlierpoints.append(outliers)
            count+=1
        finaldata = [querynames, datapoints, outlierpoints]
        return HttpResponse(json.dumps(finaldata), content_type="application/json")
    return render(request, 'alpha2.html', params)

@login_required
@activeproject
def alpha(request):
    params = {}
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
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
    params['queries'] = internal.ListQueries(request, {'projectID': [request.session['projectID']]})
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
