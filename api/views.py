from django.db import connection
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import views
from rest_framework.permissions import IsAuthenticated
from rest_framework.reverse import reverse
from rest_framework import generics
import datetime
import time
import MySQLdb
from MiRA import settings
from django.http import HttpResponse
import simplejson as json
from api import internal
from api import *

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
            {'ListTaxa': reverse('ListTaxa', request=request)},
            {'PullAttributeValues': reverse('PullAttributeValues', request=request)},
        ])

# List Datasets
# Required GET parameter: projectID, alerts user in JSON response if missing
# Displays available dataset types for project in projectID
# Written by Steven Bradley
class ListDatasets(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        kwargs = dict(request.QUERY_PARAMS)
        #kwargs['projectID'] = Project.objects.filter(name__in=kwargs['projectID']).values_list('pk', flat=True)
        queryset = internal.ListDatasets(request, kwargs)
        return Response(queryset)

# List Projects
# Displays the projects a user can acccess
# or all projects is user is admin
# Written by Steven Bradley
class ListProjects(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    model = Project

    def get_queryset(self):
        return internal.ListProjects(self.request)

# List Methods View
# Requires GET parameters projectID and dataset(string)
# Shows the methods in the database for the dataset
class ListMethods(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        kwargs = dict(request.QUERY_PARAMS)
        #kwargs['projectID'] = Project.objects.filter(name__in=kwargs['projectID']).values_list('pk', flat=True)
        queryset = internal.ListMethods(request, kwargs)
        return Response(queryset)

# List Categories View
# Requires GET parameters projectID, dataset(string), and method
# Shows the categories in the database for the dataset and method
class ListCategories(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        kwargs = dict(request.QUERY_PARAMS)
        #kwargs['projectID'] = Project.objects.filter(name__in=kwargs['projectID']).values_list('pk', flat=True)
        queryset = internal.ListCategories(request, kwargs)
        return Response(queryset)

# List Attributes View
# Requires GET param projectID 
# optional GET param name to narrow results to specific attribute
# Written by Steven Bradley
class ListAttributes(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    model = AttributeInfo

    def get_queryset(self):
        kwargs =  dict(self.request.QUERY_PARAMS)
        #kwargs['projectID'] = Project.objects.filter(name__in=kwargs['projectID']).values_list('pk', flat=True)
        return internal.ListAttributes(self.request, kwargs)

# Build Query View
# Assembles Queries based on criteria
# stores resulting sample ids into Query table for reference
# Written by Steven Bradley
class BuildQuery(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    model=Query
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

        kwargs = dict(request.QUERY_PARAMS)
        return Response(internal.BuildQuery(request, kwargs))

    def post(self, request, *args, **kwargs):
        kwargs = dict(request.POST)
        results = internal.BuildQueryFromList(request, kwargs)
        return Response(results)

        #pid = request.POST.get('projectID', None)
        #queryname = request.POST.get('queryname', None)
        #querydesc = request.POST.get('description', None)
        #samples = request.POST.getlist('sample', None)
        #if not pid or not queryname or not samples:
        #    raise APIException("required parameters are: projectID, queryname, sample")
        #try:
        #   pid = int(pid)
        #   project = Project.objects.get(pk=pid)
        #except:
        #   raise APIException("invalid projectID")
        #print 'API description:', querydesc
        #myquery = Query(
        #                user=request.user,
        #                project = project,
        #                name=queryname,
        #                description=querydesc,
        #                sqlstring = None,
        #                results = ",".join(samples)
        #               )
        #myquery.save()
        #return Response(samples)

class ShowDistribution(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        kwargs = dict(request.GET)
        results = internal.ShowDistribution(request, kwargs)
        return Response(results)

class ListQueries(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        kwargs = dict(request.GET) 
        #kwargs['projectID'] = Project.objects.filter(name__in=kwargs['projectID']).values_list('pk', flat=True)
        return Response(internal.ListQueries(request, kwargs))

class GetData(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    model=Attributes

    def get(self, request, *args, **kwargs):
        kwargs = dict(request.GET)
        array = internal.GetData(request, kwargs)
        return Response(array)

class GetDataset(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        kwargs = dict(request.GET)
        queryset = internal.GetDataset(request, kwargs)
        header = ['project', 'sample', 'dataset', 'method', 'category', 'entity', 'numreads', 'profile', 'avgscore']
        array = []
        array.append(header)
        for q in queryset:
            tmp = [q.project.pk, q.sample, q.dataset, q.method, q.category, q.entity, q.numreads, q.profile, q.avgscore]
            array.append(tmp)
        return Response(array) 

class MergeQuery(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        kwargs = dict(request.GET)
        results = internal.MergeQuery(request, kwargs)
        return Response(results)

class BuildDatasetQuery(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated(): raise APIException('please provide key or login to fetch data')
        pid = request.GET.get('projectID') or None
        fieldlist = request.GET.getlist('attribute') or None
        queryname = request.GET.get('queryname') or None
        querydesc = request.GET.get('description') or None
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

        kwargs = dict(request.GET)
        results = internal.BuildDatasetQuery(request, kwargs)
        return Response(results)

class DeleteQuery(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        kwargs = dict(request.GET)
        return Response(internal.DeleteQuery(request, kwargs))
        
class ShareQuery(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        kwargs = dict(request.GET)
        return Response(internal.ShareQuery(request, kwargs))

class ListTaxa(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        kwargs = dict(request.QUERY_PARAMS)
        return Response(internal.ListTaxa(request, kwargs))

class PullAttributeValues(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        kwargs = dict(request.QUERY_PARAMS)
        return Response(internal.PullAttributeValues(request, kwargs))
