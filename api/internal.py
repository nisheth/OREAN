from rest_framework.exceptions import APIException
from api.models import *
import traceback

def GetDataset(request, params={}):
        if not request.user.is_authenticated(): raise APIException('please provide key or login to fetch data')

        pid = queryname = dataset = method = category = None

        # Get parameters
        pid = params.get('projectID', [None])[0]
        if pid is None: raise APIException('projectID is required')

        queryname = params.get('queryname', [None])[0]
        if queryname is None: raise APIException('queryname is required')

        dataset = params.get('dataset', [None])[0]
        if dataset is None: raise APIException('dataset is required')

        method = params.get('method', [None])[0]
        category = params.get('category', [None])[0] 

        try:
            myquery = Query.objects.get(name=queryname)
            sampleslist = myquery.expandsamples
        except: raise APIException("No query found for name '%s'" % queryname)

        queryset = Analysis.objects.filter(project = pid, dataset = dataset, sample__in=sampleslist)
        if method is not None: queryset = queryset.filter(method=method)
        if category is not None: queryset = queryset.filter(category=category)
        return queryset
