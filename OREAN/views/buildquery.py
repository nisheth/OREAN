from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from . import myutils
import json
from OREAN.decorators import *
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
        querydesc = request.POST.get('description', None)
        attributes = filter(bool, request.POST.getlist('attribute'))
        print attributes
        operators = filter(bool, request.POST.getlist('operator'))
        values = filter(bool, request.POST.getlist('filtervalue'))
        text = "Success!<hr>Queryname: %s<br>Attributes:%s<br>Operators:%s<br>Values: %s<br>" %(queryname, attributes, operators, values)
        if len(attributes) == len(operators) == len(values): text+='Argument lengths match'
        else: return render(request, 'buildquery.html', params)
        if not queryname or not projectID: return render(request, 'buildquery.html', params)
        finalquery = None
        if len(values) > 1:
            tmp_queries = []
            for x in range(0,len(values)):
                this_attr = attributes[x]
                this_oper = operators[x]
                this_val = values[x]
                this_query = "tmp_%s_%d" %(request.user.username, x)
                args = {'projectID': [projectID],
                        'attribute': [this_attr],
                        'cmp': [this_oper],
                        'v1': [this_val],
                        'queryname': [this_query]} 
                buildresult =  internal.BuildQuery(request, args)   
                tmp_queries.append(this_query)
            finalquery = internal.MergeQuery(request, {'projectID': [projectID], 'queryname': tmp_queries, 'type':['intersection'], 'mergename': [queryname], 'description': [querydesc]})
            for tmp in tmp_queries:
                status =  internal.DeleteQuery(request, {'queryname':[tmp.name], 'projectID':[projectID]})
        else: finalquery = internal.BuildQuery(request, {'projectID': [projectID], 'attribute': [attributes[0]], 'cmp': [operators[0]], 'v1': [values[0]], 'queryname': [queryname], 'description': [querydesc]})
        return redirect('managequeries')
    return render(request, 'buildquery.html', params)

@login_required
@activeproject
def dataset(request):
    if request.method=='POST':
        projectID = int(request.POST.get('project'))
        queryname = request.POST.get('queryname') or None
        querydesc = request.POST.get('description', None)
        dataset = request.POST.get('dataset') or None
        method = request.POST.get('method') or None
        category = request.POST.get('category') or None
        taxa = filter(bool, request.POST.getlist('taxa'))
        operators = filter(bool, request.POST.getlist('compare'))
        values = filter(bool, request.POST.getlist('value'))
        if not len(taxa) == len(operators) == len(values) or len(values) == 0 or not dataset or not method or not category or not queryname or not projectID:
            return redirect('buildquery')
        attributes = ['dataset', 'method', 'category']+['entity' for x in taxa]+['profile' for x in values]
        ops = ['eq','eq','eq']+['eq' for x in taxa]+operators
        vals = [dataset, method, category]+[ t for t in taxa] + values
        finalquery = None
        args = {'projectID': [projectID],
                'attribute': attributes,
                'cmp': ops,
                'v1': vals,
                'queryname': [queryname],
                'description': [querydesc]
               }
        finalquery = internal.BuildDatasetQuery(request, args)
        return redirect('managequeries')
    return redirect('buildquery')

@login_required
@activeproject
def merge(request):
    return render(request, "mergequeries.html")
