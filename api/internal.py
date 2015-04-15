from api import *

def ListProjects(request):
        if not request.user.is_authenticated(): raise NotAuthenticated('Please login or provide a valid token')
        queryset = Project.objects.all()
        if request.user.is_superuser: return queryset
        return queryset.filter(userproject__user=request.user.pk)

def ListAttributes(request, params):
        if not request.user.is_authenticated(): raise NotAuthenticated('Please login or provide a valid token')
        queryset=AttributeInfo.objects.all()
        try:
            pid = int(params.get('projectID', [None])[0])
            attr = params.get('name', [])
        except:
            pid = None
            attr = None
        if pid is not None:
            queryset = queryset.filter(project=pid)
            if len(attr): queryset = queryset.filter(name__in=attr)
            return queryset
        else: raise ParseError('Please provide a projectID')

def ListQueries(request, params):
        queryname = params.get('queryname', [None])[0]
        pid = params.get('projectID', [None])[0]
        full = params.get('full', [None])[0]

	if pid is None: raise ParseError('projectID is required')

        queryset = Query.objects.filter(Q(user=request.user) | Q(share=1))
        queryset = queryset.filter(project=pid)

        if queryname is not None: queryset = queryset.filter(name=queryname)

        if full is None:
            resp = queryset.values('name', 'project', 'share', 'results', 'description')
            for r in resp:
                if r['results'].strip() == '': r['number of samples'] = 0
                else: r['number of samples'] = len(r['results'].split(','))
                r['number of subjects'] = SubjectMap.objects.filter(project=pid).values('subject').distinct().count()
                r['number of visits'] = SubjectMap.objects.filter(project=pid).values('visit', 'subject').distinct().count()
                del r['results']
            return resp
        else:
            resp = queryset.values()
            for r in resp:
                if r['results'].strip() == '': r['number of samples'] = 0
                else: r['number of samples'] = len(r['results'].split(','))
                r['number of subjects'] = SubjectMap.objects.filter(project=pid).values('subject').distinct().count()
                r['number of visits'] = SubjectMap.objects.filter(project=pid).values('visit', 'subject').distinct().count()
                del r['sqlstring']
            return resp

def BuildQuery(request, params):
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

        # Collect potential input
        try:
            pid = params.get('projectID', [None])[0]
            comp = params.get('cmp', [None])[0]
            v1 = params.get('v1', [None])[0]
            v2 = params.get('v2', [None])[0]
            queryname = params.get('queryname', [None])[0]
            attr = params.get('attribute', [None])[0]
            querydesc = params.get('description', [None])[0]
        except:
            raise ParseError('Error in parsing GET parameters. Check API call.')

        # Verify we have the bare minimum to build a query
        if not pid: raise APIException('GET paramter projectID is required')
        if not comp: raise APIException('GET paramter cmp is required')
        if not v1: raise APIException('GET paramter v1 is required')
        if not queryname: raise APIException('GET paramter queryname is required')
        if not attr: raise APIException('GET paramter attribute is required')

        if Query.objects.filter(project=pid, name=queryname).exists(): raise APIException("Sorry. A query already exists for this project with the name '%s'. Please select another name." % queryname)

        # Verify we have reasonable information
        try: pid = int(pid)
        except: raise ParseError('GET paramter projectID must be an integer')

        try: project = Project.objects.get(pk=pid)
        except: raise ParseError("Project does not exist")

        if not comp in comparisons: raise APIException("Comparison operator '%s' is not supported" %comp)
        if comparisons[comp]['values'] > 1 and not v2: raise APIException("GET param v2 is required to use the operator '%s'" % comp)

        try: attrinfo = AttributeInfo.objects.get(project=pid, name=attr)
        except: raise ParseError("The attribute '%s' does not exist." % attr)

        mycasting = 'STRING'
        if attrinfo.fieldtype == 'DECIMAL': 
            try:
                float(v1)
                if v2 is not None: float(v2)
                mycasting = 'DECIMAL'
            except: raise ParseError("Decimal values are required for attribute '%s'" % attr)

        elif attrinfo.fieldtype == 'DATE': 
            try:
                datetime.datetime.strptime(v1, "%Y-%m-%d")
                if v2 is not None: datetime.datetime.strptime(v2, "%Y-%m-%d")
                mycasting = 'DATE'
            except: raise ParseError("Date values are required for attribute '%s'. Please use format YYYY-MM-DD" % attr)

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
                        description=querydesc,
                        sqlstring=sqlstring,
                        results=",".join(queryset)
                       )
        myquery.save()
        return queryset

def GetData(request, params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('please provide key or login to fetch data')

        queryname=pid=attributelist=None

        queryname = params.get('queryname', [None])[0]
        if queryname is None: raise APIException('a query name is required')

        pid = params.get('projectID', [None])[0]
        if pid is None: raise APIException('a projectID is required')

        attributelist = params.get('attribute', [])
        if not len(attributelist): raise APIException('please provide a list of attributes')

        try:
            myquery = Query.objects.get(project=pid, name=queryname)
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
        return array

def ShowDistribution(request, params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('please provide key or login to fetch data')

        myquery = attr = pid = attrinfo = None

        try:
            pid = params.get('projectID', [None])[0]
            if pid is None: raise Exception()
        except: raise APIException('projectID is a required parameter')

        try:
            myquery = params.get('queryname', [None])[0]
            if myquery is None: raise Exception()
            myquery = Query.objects.get(project=pid, name=myquery)
        except: raise APIException('queryname is a required parameter')


        try:
            attr = params.get('attribute', [None])[0]
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
        return results

def ListDatasets(request, params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('Please login or provide a valid token')
        queryset = Analysis.objects.all()
        try: pid = int(params.get('projectID', [None])[0])
        except: pid = None
        if pid is not None:
            #queryset = queryset.filter(project=pid).values_list('dataset', flat=True).distinct()
            queryset = queryset.filter(project=pid).values_list('project', 'dataset').distinct()
            queryset = [x[1] for x in queryset]
            return queryset
        raise APIException("Please Specify a projectID as a GET parameter")

def ListMethods(request, params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('Please login or provide a valid token')
        queryset = Analysis.objects.all()
        try:
            pid = int(params.get('projectID', [None])[0])
            dataset = params.get('dataset', [None])[0]
        except:
            pid = None
            dataset = None
        if pid is not None and dataset is not None:
            #queryset = queryset.filter(project=pid, dataset=dataset).values_list('method', flat=True).distinct()
            queryset = queryset.filter(project=pid, dataset=dataset).values_list('project', 'dataset', 'method').distinct()
            queryset = [x[2] for x in queryset]
            return queryset
        raise APIException("Please Specify a projectID and a Dataset as GET parameters")

def ListCategories(request, params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('Please login or provide a valid token')
        queryset = Analysis.objects.all()
        try:
            pid = int(params.get('projectID', [None])[0])
            dataset = params.get('dataset', [None])[0]
            method = params.get('method', [None])[0]
        except:
            pid = None
            dataset = None
            method=None
        if pid is not None and dataset is not None and method is not None:
            #queryset = queryset.filter(project=pid, dataset=dataset, method=method).values_list('category', flat=True).distinct()
            queryset = queryset.filter(project=pid, dataset=dataset, method=method).values_list('project', 'dataset', 'method', 'category').distinct()
            queryset = [x[3] for x in queryset]
            return queryset
        raise APIException("Please Specify a projectID, dataset, and a method as GET parameters")

def GetDataset(request, params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('please provide key or login to fetch data')

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
        entities = params.get('entity', None)

        try:
            myquery = Query.objects.get(project=pid, name=queryname)
            sampleslist = myquery.expandsamples
        except: raise APIException("No query found for name '%s'" % queryname)

        queryset = Analysis.objects.filter(project = pid, dataset = dataset, sample__in=sampleslist)
        if method is not None: queryset = queryset.filter(method=method)
        if category is not None: queryset = queryset.filter(category=category)
        if entities is not None: queryset = queryset.filter(entity__in=entities)
        return queryset.order_by('sample')

def MergeQuery(request,params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('please provide key or login to fetch data')

        pid = params.get('projectID', [None])[0]
        if pid is None: raise APIException('projectID is required')

        querylist = params.get('queryname', [])
        if len(querylist) < 2: raise APIException('must provide at least 2 querynames')

        mergetype = params.get('type', [None])[0]
        if mergetype != 'union' and mergetype != 'intersection': raise APIException("must provide a merge 'type' of either 'union' or 'intersection'")

        mergename = params.get('mergename', [None])[0]
        if mergename is None: raise APIException("must provide a 'mergename' for the merged query")
        if Query.objects.filter(project = pid, name=mergename).exists(): raise APIException("A query named '%s' already exists for the project" % mergename)

        querydesc = params.get('description', [None])[0]

        samplescounter = {}
        project = None
        for idx,q in enumerate(querylist):
            try:
                try: query = Query.objects.get(project = pid, name=q)
                except: raise APIException("No query named '%s' found in project ID '%s'" % (q, pid) )
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
                        description=querydesc,
                        sqlstring='MERGED QUERY',
                        results=','.join(mergedlist)
                       )
        myquery.save()
        return mergedlist

def BuildDatasetQuery(request, params={}):
        pid = params.get('projectID', [None])[0]
        fieldlist = params.get('attribute', None)
        queryname = params.get('queryname', [None])[0]
        querydesc = params.get('description', [None])[0]
        complist = params.get('cmp', None)
        v1list = params.get('v1', None)

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

        if not pid: raise APIException('projectID is required')
        if not fieldlist: raise APIException('attribute is required')
        if not complist: raise APIException('cmp is required')
        if not queryname: raise APIException('queryname is required')
        if Query.objects.filter(project=pid, name=queryname).exists(): raise APIException("Query name '%s' is already in use, please select another name" % queryname)
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
                        description=querydesc,
                        sqlstring=sqlstring,
                        results=",".join(queryset)
                       )
        myquery.save()
        return queryset

def DeleteQuery(request, params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('please provide key or login to fetch data')
        pid = params.get('projectID', [None])[0]
        queryname = params.get('queryname', [None])[0]
        try:
            query = Query.objects.get(project = pid, name=queryname, user=request.user)
            query.delete()
            return "ok"
        except: raise APIException("No query named '%s' in project '%s' for user '%s'" % (queryname,pid, request.user.username))

def ShareQuery(request, params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('please provide key or login to fetch data')
        pid = params.get('projectID', [None])[0]
        queryname = params.get('queryname', [None])[0]
        try:
            query = Query.objects.get(project = pid, name=queryname, user=request.user)
            if query.share == 0: query.share = 1
            else: query.share = 0
            query.save()
            return query.share
        except: raise APIException("No query named '%s' in project '%s' for user '%s'" % (queryname,pid, request.user.username))

def ListTaxa(request, params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('Please login or provide a valid token')
        queryset = Analysis.objects.all()
        try:
            pid = int(params.get('projectID', [None])[0])
            dataset = params.get('dataset', [None])[0]
            method = params.get('method', [None])[0]
            category = params.get('category', [None])[0]
        except:
            pid = None
            dataset = None
            method=None
            category=None
        if pid is not None and dataset is not None and method is not None and category is not None:
            queryset = queryset.filter(project=pid, dataset=dataset, method=method, category=category).values_list('entity', flat=True).distinct().order_by('entity')
            return queryset
        raise APIException("Please Specify a projectID, dataset, method, and category as GET parameters")

def PullAttributeValues(request, params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('Please login or provide a valid token')
        pid = params.get('projectID', [None])[0]
        attribute = params.get('attribute', [None])[0]
        try:
            pid=int(pid)
            attrinfo = AttributeInfo.objects.get(project=pid, name=attribute)
            data = None
            resp = {}
            resp['type'] = attrinfo.fieldtype
            if attrinfo.fieldtype == 'DECIMAL':
                data = Attributes.objects.filter(field=attribute, project=pid).values_list('value', flat=True)
                data = [float(n) for n in data]
                data.sort()
                data = [data[0], data[-1]]
            else:
                data = Attributes.objects.filter(field=attribute, project=pid).values_list('value', flat=True).distinct().order_by("value")
            resp['data'] = data
            return resp
        except:
            #raise APIException("%s" % (traceback.format_exc()))
            raise APIException("Unable to pull attribute values for %s" % (attribute))

def BuildQueryFromList(request, params={}):
        if not request.user.is_authenticated(): raise NotAuthenticated('Please login or provide a valid token')
        pid = params.get('projectID', [None])[0]
        queryname = params.get('queryname', [None])[0]
        querydesc = params.get('description', [None])[0]
        samples = params.get('sample', None)
        if not pid or not queryname or not samples:
            raise APIException("required parameters are: projectID, queryname, sample")
        try:
           pid = int(pid)
           project = Project.objects.get(pk=pid)
        except:
           raise APIException("invalid projectID")
        print 'API description:', querydesc
        myquery = Query(
                        user=request.user,
                        project = project,
                        name=queryname,
                        description=querydesc,
                        sqlstring = None,
                        results = ",".join(samples)
                       )
        myquery.save()
        return samples
