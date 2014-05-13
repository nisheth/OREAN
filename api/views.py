from django.db.models import Count
from django.db import connection
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import views
from rest_framework.permissions import IsAuthenticated
from api.models import *
from rest_framework.reverse import reverse
from rest_framework import generics
from django.db.models import Q
import datetime
import traceback
import time
import MySQLdb
from MiRA import settings
from django.http import HttpResponse
import simplejson as json
from api import internal

# API Root
# Lists the available APIs for use
# provides URLs to each
# Written by Steven Bradley
class APIRoot(views.APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        # Assuming we have views named 'foo-view' and 'bar-view'
        # in our project's URLconf.
        return Response([
            {'ListProjects': reverse('ListProjects', request=request)},
            {'ListAttributes': reverse('ListAttributes', request=request)},
            {'ListQueries': reverse('ListQueries', request=request)},
            {'BuildQuery': reverse('BuildQuery', request=request)},
            {'GetData': reverse('GetData', request=request)},
            {'ShowDistribution': reverse('ShowDistribution', request=request)},
            {'ListDatasets': reverse('ListDatasets', request=request)},
            {'ListMethods': reverse('ListMethods', request=request)},
            {'ListCategories': reverse('ListCategories', request=request)},
            {'GetDataset': reverse('GetDataset', request=request)},
            {'MergeQuery': reverse('MergeQuery', request=request)},
            {'BuildDatasetQuery': reverse('BuildDatasetQuery', request=request)},
            {'DeleteQuery': reverse('DeleteQuery', request=request)},
            {'ShareQuery': reverse('ShareQuery', request=request)},
            {'FastFetch': reverse('FastFetch', request=request)},
        ])

# List Datasets
# Required GET parameter: projectID, alerts user in JSON response if missing
# Displays available dataset types for project in projectID
# Written by Steven Bradley
class ListDatasets(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('Please login or provide a valid token')
        queryset = Analysis.objects.all()
        try: pid = int(request.QUERY_PARAMS.get('projectID', None))
        except: pid = None    
        if pid is not None:
            queryset = queryset.filter(project=pid).values_list('dataset', flat=True).distinct() 
            return Response(queryset)
        raise APIException("Please Specify a projectID as a GET parameter")

# List Projects
# Displays the projects a user can acccess
# or all projects is user is admin
# Written by Steven Bradley
class ListProjects(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    model = Project

    def get_queryset(self):
        if not self.request.user.is_authenticated(): raise APIException('Please login or provide a valid token')
        queryset = Project.objects.all()
        if self.request.user.is_superuser: return queryset
        return queryset.filter(userproject__user=self.request.user.pk)
        raise APIException('must be logged in or use a valid token')

# List Methods View
# Requires GET parameters projectID and dataset(string)
# Shows the methods in the database for the dataset
class ListMethods(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('Please login or provide a valid token')
        queryset = Analysis.objects.all()
        try: 
            pid = int(request.QUERY_PARAMS.get('projectID', None))
            dataset = request.QUERY_PARAMS.get('dataset', None)
        except: 
            pid = None    
            dataset = None
        if pid is not None and dataset is not None:
            queryset = queryset.filter(project=pid, dataset=dataset).values_list('method', flat=True).distinct()
            return Response(queryset)
        raise APIException("Please Specify a projectID and a Dataset as GET parameters")

# List Categories View
# Requires GET parameters projectID, dataset(string), and method
# Shows the categories in the database for the dataset and method
class ListCategories(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('Please login or provide a valid token')
        queryset = Analysis.objects.all()
        try:
            pid = int(request.QUERY_PARAMS.get('projectID', None))
            dataset = request.QUERY_PARAMS.get('dataset', None)
            method = request.QUERY_PARAMS.get('method', None)
        except:
            pid = None
            dataset = None
            method=None
        if pid is not None and dataset is not None and method is not None:
            queryset = queryset.filter(project=pid, dataset=dataset, method=method).values_list('category', flat=True).distinct()
            return Response(queryset)
        raise APIException("Please Specify a projectID, dataset, and a method as GET parameters")

# List Attributes View
# Requires GET param projectID 
# optional GET param name to narrow results to specific attribute
# Written by Steven Bradley
class ListAttributes(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    model = AttributeInfo

    def get_queryset(self):
        if not self.request.user.is_authenticated(): raise APIException('Please login or provide a valid token')
        queryset=AttributeInfo.objects.all()
        try:
            pid = int(self.request.QUERY_PARAMS.get('projectID', None))
            attr = self.request.QUERY_PARAMS.get('name', None)
        except:
            pid = None
            attr = None
        if pid is not None:
            queryset = queryset.filter(project=pid)
            if attr is not None: queryset = queryset.filter(name=attr)
            return queryset
        else: raise APIException('Please provide a projectID')

# Build Query View
# Assembles Queries based on criteria
# stores resulting sample ids into Query table for reference
# Written by Steven Bradley
class BuildQuery(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('Please login or provide a valid token')

        comparisons = {'eq' : {'description': 'equal to', 'types': ['STRING', 'DECIMAL', 'DATE'], 'values': 1, 'operator': '='}, 
                       'ne' : {'description': 'Not equal to', 'types': ['STRING', 'DECIMAL', 'DATE'], 'values': 1, 'operator': '!='},  
                       'gt': {'description': 'greater than', 'types': ['DECIMAL', 'DATE'], 'values': 1, 'operator': '>'}, 
                       'gte': {'description': 'greater than or equal to', 'types': ['DECIMAL', 'DATE'], 'values': 1, 'operator': '>='}, 
                       'lte': {'description': 'less than or equal to', 'types': ['DECIMAL', 'DATE'], 'values': 1, 'operator': '<='}, 
                       'lt': {'description': 'less than', 'types': ['DECIMAL', 'DATE'], 'values': 1, 'operator': '<'}}

        parameters = {'projectID' : {'description': 'ID of project for the query', 'types': ['INT'] , 'required': True}, 
                      'cmp' : {'description': 'Comparison operator. See details below.', 'types': ['STRING'], 'required': True},  
                      'v1': {'description': 'value 1 for search criteria', 'types': ['DECIMAL', 'DATE'], 'required': True}, 
                      'v2': {'description': 'value 2 for search criteria for certain operators', 'types': ['STRING', 'DECIMAL', 'DATE'], 'required': False}, 
                      'queryname': {'description': 'name to associate with query', 'types': ['STRING'], 'required': True}, 
                      'attribute': {'description': 'the attribute to filter on', 'types': ['STRING'], 'required': True}}


        helpmessage =  [
                        {'Build Query': 'This is some documentation to help clarify query requirements!'},
                        {'paramters': parameters},
                        {'operators' : comparisons}
                       ]

        if len(request.GET) == 0: return Response(helpmessage)

        # Collect potential input
        try:
            pid = request.QUERY_PARAMS.get('projectID', None)
            comp = request.QUERY_PARAMS.get('cmp', None)
            v1 = request.QUERY_PARAMS.get('v1', None)
            v2 = request.QUERY_PARAMS.get('v2', None)
            queryname = request.QUERY_PARAMS.get('queryname', None)
            attr = request.QUERY_PARAMS.get('attribute', None)
        except:
            raise APIException('Error in parsing GET parameters. Check API call.')

        # Verify we have the bare minimum to build a query
        if not pid: raise APIException('GET paramter projectID is required')
        if not comp: raise APIException('GET paramter cmp is required')
        if not v1: raise APIException('GET paramter v1 is required')
        if not queryname: raise APIException('GET paramter queryname is required')
        if not attr: raise APIException('GET paramter attribute is required')

        if Query.objects.filter(name=queryname).exists(): raise APIException("Sorry. A query already exists with the name '%s'. Please select another" % queryname)

        # Verify we have reasonable information
        try: pid = int(pid)
        except: raise APIException('GET paramter projectID must be an integer')

        try: project = Project.objects.get(pk=pid)
        except: raise APIException("Project with id '%s' does not exist" % pid)

        if not comp in comparisons: raise APIException("Comparison operator '%s' is not supported" %comp)
        if comparisons[comp]['values'] > 1 and not v2: raise APIException("GET param v2 is required to use the operator '%s'" % comp)

        try: attrinfo = AttributeInfo.objects.get(project=pid, name=attr)
        except: raise APIException("The attribute '%s' does not exist." % attr)

        mycasting = 'STRING'
        if attrinfo.fieldtype == 'DECIMAL': 
            try:
                float(v1)
                if v2 is not None: float(v2)
                mycasting = 'DECIMAL'
            except: raise APIException("Decimal values are required for attribute '%s'" % attr)

        elif attrinfo.fieldtype == 'DATE': 
            try:
                datetime.datetime.strptime(v1, "%Y-%m-%d")
                if v2 is not None: datetime.datetime.strptime(v2, "%Y-%m-%d")
                mycasting = 'DATE'
            except: raise APIException("Date values are required for attribute '%s'. Please use format YYYY-MM-DD" % attr)

        # Now that the data appears acceptable, we need to query for samples based on this criteria
        # Starting working set -  all samples for this project
        queryset = Attributes.objects.filter(project=pid)

        # Now filter the data customized to the comparison operator at hand
        cmd = ""          # the command that will run
        params = []       # the uncontrolled v1 and v2 strings need to be properly escaped via params option
        if mycasting != 'STRING': 
            cmd = 'CAST(value as %s)%s' % (mycasting, comparisons[comp]['operator'])
        else: 
            cmd = 'value%s' % comparisons[comp]['operator']
        if mycasting == 'DATE': cmd+='date '
        if mycasting != 'DECIMAL': 
            cmd+="%s" # use params to properly escape an uncontrolled string
            params.append(v1)
        else: cmd+=v1 # this is not escaped, its already verified safe from passing numeric check
        queryset = queryset.filter(field=attr).extra(where=[cmd], params=params)

        # Once data is filtered, get the unique list of sample ids
        queryset = queryset.values_list('sample', flat=True).distinct()
        sqlstring = "%s" % queryset.query

        # Store this new query in the query table
        myquery = Query(
                        user=request.user,
                        project= project,
                        name=queryname,
                        sqlstring=sqlstring,
                        results=",".join(queryset)
                       )
        myquery.save()
        return Response(queryset)            

class ShowDistribution(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('please provide key or login to fetch data')
   
        myquery = attr = projectID = attrinfo = None

        try: 
            myquery = request.GET.get('queryname')
            if myquery is None: raise Exception()
            myquery = Query.objects.get(name=myquery)
        except: raise APIException('queryname is a required parameter')

        try: 
            pid = request.GET.get('projectID')
            if pid is None: raise Exception()
        except: raise APIException('projectID is a required parameter')

        try: 
            attr = request.GET.get('attribute')
            if attr is None: raise Exception()
        except: raise APIException('attribute is a required parameter')

        try: attrinfo = AttributeInfo.objects.get(project=pid, name=attr) 
        except: raise APIException("The attribute '%s' does not exist." % attr)

        querysamples = myquery.expandsamples
        results = list(Attributes.objects.filter(project = pid,  field = attr, sample__in=querysamples).values_list('value').annotate(Count('value')))
        if attrinfo.fieldtype == 'DECIMAL':
            for idx, r in enumerate(results): 
                r = list(r)
                r.insert(0, float(r.pop(0)))
                results[idx] = r
        results.insert(0, [attr, 'Count']) 
        return Response(results)

class ListQueries(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
 
        queryname = request.GET.get('queryname') or None
        pid = request.GET.get('projectID') or None
        full = request.GET.get('full') or None

        queryset = Query.objects.filter(Q(user=self.request.user) | Q(share=1))

        if queryname is not None: queryset = queryset.filter(name=queryname)
        if pid is not None: queryset = queryset.filter(project=pid)
  
        if full is None: 
            resp = queryset.values('name', 'project', 'share', 'results', 'description')
            for r in resp:
                r['number of samples'] = len(r['results'].split(','))
                del r['results']
            return Response(resp)
        else:
            resp = queryset.values()
            for r in resp:
                r['number of samples'] = len(r['results'].split(','))
                del r['sqlstring']
            return Response(resp)

class GetData(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    model=Attributes

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('please provide key or login to fetch data')
        
        queryname=pid=attributelist=None
        
        queryname = self.request.GET.get('queryname') or None
        if queryname is None: raise APIException('a query name is required')

        pid = self.request.GET.get('projectID') or None
        if pid is None: raise APIException('a projectID is required')

        attributelist = self.request.GET.getlist('attribute') or None
        if attributelist is None: raise APIException('please provide a list of attributes')

        try:
            myquery = Query.objects.get(name=queryname) 
            querysamples = myquery.results.split(',')
        except: raise APIException("No query found for name '%s'" % queryname)
        queryset = Attributes.objects.filter(project=pid, field__in=attributelist, sample__in=querysamples)
        resp = {}
        header = ['Sample'] + attributelist
        for q in queryset:
            if not q.sample in resp:
                resp[q.sample] =  {}
            resp[q.sample][q.field] = q.value
        array = []
        array.append(header)
        for r in resp:
            tmp = [r]
            for attr in attributelist:
                try:tmp.append(resp[r][attr])
                except: tmp.append(None)
            array.append(tmp)
        return Response(array)

class GetDataset(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('please provide key or login to fetch data')
        
        pid = queryname = dataset = method = category = None
        
        # Get parameters
        pid = request.GET.get('projectID') or None
        if pid is None: raise APIException('projectID is required') 
   
        queryname = request.GET.get('queryname') or None
        if queryname is None: raise APIException('queryname is required') 

        dataset = request.GET.get('dataset') or None
        if dataset is None: raise APIException('dataset is required') 

        method = request.GET.get('method') or None
        category = request.GET.get('category') or None

        try:
            myquery = Query.objects.get(name=queryname)
            sampleslist = myquery.expandsamples
        except: raise APIException("No query found for name '%s'" % queryname)

        queryset = Analysis.objects.filter(project = pid, dataset = dataset, sample__in=sampleslist)
        if method is not None: queryset = queryset.filter(method=method)
        if category is not None: queryset = queryset.filter(category=category)
        header = ['project', 'sample', 'dataset', 'method', 'category', 'entity', 'numreads', 'profile', 'avgscore']
        array = []
        array.append(header)
        for q in queryset:
            tmp = [q.project.pk, q.sample, q.dataset, q.method, q.category, q.entity, q.numreads, q.profile, q.avgscore]
            array.append(tmp)
        return Response(array) 
        #cursor = connection.cursor()
        #cursor.execute("SELECT project_id, dataset, method, category, entity, numreads, profile, avgscore FROM api_analysis WHERE method='RDP-0-5'")
        #rows = cursor.fetchall()
        #header = zip(*cursor.description)[0]
        #cursor.close()
        #myjson = (header, )+ rows
        #return HttpResponse(json.dumps(myjson), content_type='application/json')
        #return Response(queryset.defer.values_list()) 

class MergeQuery(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('please provide key or login to fetch data')

        querylist = request.GET.getlist('queryname')
        if len(querylist) < 2: raise APIException('must provide at least 2 querynames')

        mergetype = request.GET.get('type') or None
        if mergetype != 'union' and mergetype != 'intersection': raise APIException("must provide a merge 'type' of either 'union' or 'intersection'")

        mergename = request.GET.get('mergename') or None
        if mergename is None: raise APIException("must provide a 'mergename' for the merged query")
 
        samplescounter = {}
        project = None
        for idx,q in enumerate(querylist):
            try:
                query = Query.objects.get(name=q)
                querylist[idx] = query
                if project is None: project = query.project
                elif project != query.project: raise APIException('queries from different projects cannot be merged')
                sampleslist = query.expandsamples
                for s in sampleslist:
                    if s not in samplescounter: samplescounter[s] = 1
                    else: samplescounter[s] += 1
            except: continue
     
        mergedlist = []   
        for s in samplescounter: 
            if mergetype=='union' and samplescounter[s]>=1: mergedlist.append(s)
            elif mergetype=='intersection' and samplescounter[s]==len(querylist): mergedlist.append(s)
     
        myquery = Query(
                        user=request.user,
                        project= project,
                        name=mergename,
                        sqlstring='MERGED QUERY',
                        results=','.join(mergedlist)
                       )
        myquery.save()
        return Response(mergedlist)

class BuildDatasetQuery(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('please provide key or login to fetch data')
        pid = request.GET.get('projectID') or None
        fieldlist = request.GET.getlist('attribute') or None
        queryname = request.GET.get('queryname') or None
        complist = request.GET.getlist('cmp') or None
        v1list = request.GET.getlist('v1') or None

        comparisons = {'eq' : {'description': 'equal to', 'types': ['STRING', 'DECIMAL', 'DATE'], 'values': 1, 'operator': '='}, 
                       'ne' : {'description': 'Not equal to', 'types': ['STRING', 'DECIMAL', 'DATE'], 'values': 1, 'operator': '!='},  
                       'gt': {'description': 'greater than', 'types': ['DECIMAL', 'DATE'], 'values': 1, 'operator': '>'}, 
                       'gte': {'description': 'greater than or equal to', 'types': ['DECIMAL', 'DATE'], 'values': 1, 'operator': '>='}, 
                       'lte': {'description': 'less than or equal to', 'types': ['DECIMAL', 'DATE'], 'values': 1, 'operator': '<='}, 
                       'lt': {'description': 'less than', 'types': ['DECIMAL', 'DATE'], 'values': 1, 'operator': '<'}}

        parameters = {'projectID' : {'description': 'ID of project for the query', 'required': True}, 
                      'cmp' : {'description': 'Comparison operator. See details below.', 'required': True},  
                      'v1': {'description': 'value 1 for search criteria', 'required': True}, 
                      'queryname': {'description': 'name to associate with query', 'required': True}, 
                      'attribute': {'description': 'the attribute to filter on', 'required': True, 'choices': {'dataset': 'STRING', 'method': 'STRING', 'category': 'STRING', 'entity': 'STRING', 'numreads': 'DECIMAL', 'profile': 'DECIMAL', 'avgscore': 'DECIMAL'}}}

        helpmessage =  [
                        {'Build Query': 'This is some documentation to help clarify query requirements!'},
                        {'paramters': parameters},
                        {'operators' : comparisons}
                       ]
        if len(request.GET) == 0: return Response(helpmessage)

        if not pid: raise APIException('projectID is required')
        if not fieldlist: raise APIException('attribute is required')
        if not complist: raise APIException('cmp is required')
        if not queryname: raise APIException('queryname is required')
        if Query.objects.filter(name=queryname).exists(): raise APIException("Query name '%s' is already in use, please select another name" % queryname)
        n = len(fieldlist)
        if not all(len(x) == n for x in [fieldlist, complist, v1list]): raise APIException('filtering criteria parameters are different lengths')

        queryset = Analysis.objects.filter(project = pid)
        while len(fieldlist):
            fieldname = fieldlist.pop(0)
            comp = complist.pop(0)
            v1 = v1list.pop(0)
            if comp not in comparisons: raise APIException('%s is not a supported comparison' % comp)
            if fieldname not in parameters['attribute']['choices']: raise APIException('%s is not a supported attribute' % fieldname)
            if parameters['attribute']['choices'][fieldname] != 'STRING': 
                try: v1 = float(v1)
                except: raise APIException('attribute %s requires numeric values, but v1 is not a numeric')
            if not pid: raise APIException('projectID is required')
            if parameters['attribute']['choices'][fieldname] not in comparisons[comp]['types']: raise APIException('%s does not support %s comparisons' %(fieldname, comp)) 
            try: project = Project.objects.get(pk=pid)
            except: raise APIException("Project '%s' could not be found" %pid)
    
            params = {}
            if comp != 'eq' and comp != 'ne': 
                params[fieldname+'__'+comp] = v1
                queryset = queryset.filter(**params)
            else: 
                params = {fieldname : v1}
                if comp=='eq': queryset = queryset.filter(**params)
                else: queryset = queryset.exclude(**params)
        queryset = queryset.values_list('sample', flat=True).distinct()
        sqlstring = "%s" % queryset.query

        # Store this new query in the query table
        myquery = Query(
                        user=request.user,
                        project= project,
                        name=queryname,
                        sqlstring=sqlstring,
                        results=",".join(queryset)
                       )
        myquery.save()
        return Response(queryset)


class DeleteQuery(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('please provide key or login to fetch data')
        pid = request.GET.get('projectID') or None
        queryname = request.GET.get('queryname') or None
        try: 
            query = Query.objects.get(project = pid, name=queryname, user=request.user)
            query.delete()
            return Response("ok")
        except: raise APIException("No query named '%s' in project '%s' for user '%s'" % (queryname,pid, request.user.username)) 
        
class ShareQuery(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('please provide key or login to fetch data')
        pid = request.GET.get('projectID') or None
        queryname = request.GET.get('queryname') or None
        try:
            query = Query.objects.get(project = pid, name=queryname, user=request.user)
            if query.share == 0: query.share = 1
            else: query.share = 0
            query.save()
            return Response(query.share)
        except: raise APIException("No query named '%s' in project '%s' for user '%s'" % (queryname,pid, request.user.username))

class FastFetch(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        print request.GET.getlist('foo')
        params = dict(request.GET)
        queryset = internal.GetDataset(request, params=params)
        header = ['project', 'sample', 'dataset', 'method', 'category', 'entity', 'numreads', 'profile', 'avgscore']
        array = []
        array.append(header)
        for q in queryset:
            tmp = [q.project.pk, q.sample, q.dataset, q.method, q.category, q.entity, q.numreads, q.profile, q.avgscore]
            array.append(tmp)
        return Response(array)
