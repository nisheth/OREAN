from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from . import myutils
import json
from OREAN.decorators import *
from OREAN.utils import *
from api import internal
from api import *
import logging
from django.contrib import messages
logger = logging.getLogger('django')

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
        params_to_save = []
        if len(values) > 1:
            tmp_queries = []
            for x in range(0,len(values)):
                this_attr = attributes[x]
                this_oper = operators[x]
                this_val = values[x]
                params_to_save.append([this_attr, this_oper, this_val])
                this_query = "tmp_%s_%d" %(request.user.username, x)
                args = {'projectID': [projectID],
                        'attribute': [this_attr],
                        'cmp': [this_oper],
                        'v1': [this_val],
                        'queryname': [this_query]} 
                buildresult =  internal.BuildQuery(request, args)   
                tmp_queries.append(this_query)
            try:
                finalquery = internal.MergeQuery(request, {'projectID': [projectID], 'queryname': tmp_queries, 'type':['intersection'], 'mergename': [queryname], 'description': [querydesc]})
                for tmp in tmp_queries:
                    status =  internal.DeleteQuery(request, {'queryname':[tmp.name], 'projectID':[projectID]})
            except Exception, e:
                messages.add_message(request, messages.ERROR, e)
                return render(request, 'buildquery.html', params)
        else: 
            try:
                finalquery = internal.BuildQuery(request, {'projectID': [projectID], 'attribute': [attributes[0]], 'cmp': [operators[0]], 'v1': [values[0]], 'queryname': [queryname], 'description': [querydesc]})
                params_to_save.append([attributes[0], operators[0], values[0]])
            except Exception, e:
                messages.add_message(request, messages.ERROR, e)
                return render(request, 'buildquery.html', params)
        voodoo_magic = {'metadata': params_to_save}
        finalquery.sqlstring = json.dumps(voodoo_magic)
        finalquery.save()
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
        attributes = ['dataset', 'method', 'category'] #+ ['entity' for x in taxa]+['profile' for x in values]
        ops = ['eq','eq','eq']
        vals = [dataset, method, category]
        for i in range(len(taxa)):
            t = taxa[i]
            o = operators[i]
            v = values [i]
            attributes.append('entity')
            ops.append('eq')
            vals.append(t)
            attributes.append('profile')
            ops.append(o)
            vals.append(v)
        #ops = ['eq','eq','eq']+['eq' for x in taxa]+operators
        #vals = [dataset, method, category]+[ t for t in taxa] + values
        finalquery = None
        args = {'projectID': [projectID],
                'attribute': attributes,
                'cmp': ops,
                'v1': vals,
                'queryname': [queryname],
                'description': [querydesc]
               }
        voodoo_magic = {'omics': {'attribute': attributes,
                                  'cmp': ops,
                                  'v1': vals}}
        savestring = json.dumps(voodoo_magic)
        finalquery = internal.BuildDatasetQuery(request, args)
        finalquery.sqlstring = savestring
        finalquery.save()
        return redirect('managequeries')
    return redirect('buildquery')

@login_required
@activeproject
def merge(request):
    if request.method=='POST':
        projectID = int(request.POST.get('project'))
        queryname = request.POST.get('queryname') or None
        description = request.POST.get('querydescription') or None
        tmplist = request.POST.get('sampleslist') or None
        querylist = request.POST.getlist('queries', None)
        mergemethod = request.POST.get('mergetype') or None
        voodoo_magic = None
        if querylist and mergemethod:
            voodoo_magic = {'merged': {'queries': [],
                                       'type': mergemethod,
                                      }
                           }
            for qname in querylist:
                try:
                    qobj = Query.objects.get(project_id=projectID, name=qname)
                    if not qobj.sqlstring:
                        raise Exception('cannot keep create state on NULL sqlstring')
                    qrecovery = json.loads(qobj.sqlstring)
                    voodoo_magic['merged']['queries'].append(qrecovery)
                except Exception as e:
                    logger.error(e.message)
                    voodoo_magic = None
                    break
        tmplist = tmplist.split('\n')
        samplelist = []
        for sample in tmplist:
            sample = sample.strip()
            if len(sample) == 0: continue
            else: samplelist.append(sample)
        if not queryname or not projectID or not len(samplelist): return render(request, 'buildquery.html', params)
        print 'Views Description:', description
        finalquery = internal.BuildQueryFromList(request, {'projectID': [projectID], 'queryname': [queryname], 'description': [description], 'sample': samplelist})
        if voodoo_magic:
            finalquery.sqlstring = json.dumps(voodoo_magic)
            finalquery.save()
        return redirect('managequeries')
    return render(request, "mergequeries.html")

@login_required
@activeproject
def rebuild(request):
    if request.method=='POST':

        new_name = request.POST.get('new_name', None)
        new_desc = request.POST.get('new_desc', None)
        old_name = request.POST.get('query_name_input', None)
        project_id = request.POST.get('project_id_input', None)

        if not new_name or not old_name or not project_id:
            messages.add_message(request, messages.WARNING, "Required input information was missing from the request")
            return redirect('managequeries') 

        if request.user.is_superuser:
            allowed_projects = Project.objects.all()
        else:
            allowed_projects = request.user.project_set.all()
       
        try:
            project_id = int(project_id)
            query = Query.objects.get(project_id=project_id, name=old_name) 
        except:
            messages.add_message(request, messages.WARNING, "The old query information could not be retrieved")
            return redirect('managequeries') 
    
        if not allowed_projects.filter(id=query.project_id).exists():
            messages.add_message(request, messages.WARNING, "Access is not permitted to the query")
            return redirect('managequeries') 
       
        if query.user_id != request.user.id and not query.share: 
            messages.add_message(request, messages.WARNING, "Access is not permitted to the query")
            return redirect('managequeries') 
    
        try:
            build_rule = json.loads(query.sqlstring)
        except:
            messages.add_message(request, messages.WARNING, "Unfortunately, this query was created before rebuilding was supported and cannot be automatically recreated.")
            return redirect('managequeries')
    
        new_query = rebuild_query(request, query.project_id, build_rule, new_name, new_desc)
        if new_query:
            new_query.sqlstring = query.sqlstring
            new_query.save()
            messages.add_message(request, messages.SUCCESS, "Query '%s' was recreated successfully and was given the new name '%s'." % (query.name, new_query.name))
            return redirect('managequeries')
        else:
            messages.add_message(request, messages.ERROR, "An unanticipated error occurred while attempting to recreate the query")
            return redirect('managequeries')
    else:
        return redirect('managequeries')
