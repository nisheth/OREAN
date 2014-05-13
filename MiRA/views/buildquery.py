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
                args = {'projectID': projectID,
                        'attribute': this_attr,
                        'cmp': this_oper,
                        'v1': this_val,
                        'queryname': this_query} 
                buildresult =  myutils.call_api(request, 'BuildQuery', params=args)   
                print this_query
                tmp_queries.append(this_query)
            finalquery = myutils.call_api(request, 'MergeQuery', params={'queryname': tmp_queries, 'type':'intersection', 'mergename': queryname})
            for tmp in tmp_queries:
                status =  myutils.call_api(request, 'DeleteQuery', params={'queryname':tmp, 'projectID':projectID})
                print "deleted tmp query:", this_query
        else: finalquery = myutils.call_api(request, 'BuildQuery', params={'projectID': projectID, 'attribute': attributes[0], 'cmp': operators[0], 'v1': values[0], 'queryname': queryname})
        return redirect('managequeries')
    return render(request, 'buildquery.html', params)
