from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.contrib import messages
from api.models import *
from api import internal
import os
import hashlib
import json
import logging
import string
import random

def id_generator(size=255, chars=string.ascii_letters + string.digits):
   return ''.join(random.SystemRandom().choice(chars) for _ in range(size))

# Get an instance of a logger
logger = logging.getLogger('django')

def make_random():
  random_data = os.urandom(128)
  return hashlib.md5(random_data).hexdigest()

def make_url(request, user, type):
  token = make_random()
  while (EmailTokens.objects.filter(token=token).exists()):
    token = make_random()
  namedURL = 'activateNewUser'
  type_num = 1
  if type=='resetPassword': 
    namedURL=type
    type_num = 2
  myurl = request.build_absolute_uri(reverse(namedURL, args=(token,)))
  newTokenInstance = EmailTokens(user=user, type=type_num, token=token)
  newTokenInstance.save()
  return myurl

def send_new_email(request, to_address, subject, message):
  try: 
     send_mail(subject,
               message,
               'OREAN Web Server <orean@vcu.edu>',
               [to_address],
               fail_silently=False)
  except:
     messages.add_message(request, messages.ERROR, "An error occurred when attempting to send an email.")

def in_project(user, p):
     if not user.is_authenticated(): return False
     if user.is_superuser or UserProject.objects.filter(project=p, user=user).exists(): return True
     return False

def rebuild_query(request, projectID, build_rule, new_name, new_desc=None):
    """
    This function will recreate a new instance of the provided query and assign the 
    new query the string passed as "new_name". If the query cannot be rebuilt, the 
    function will return None, otherwise the function will return the new query
    """
    # loop through the rebuild rules
    new_query = None
    for qt in build_rule:
        if qt == 'omics':
               args = build_rule[qt]
               args['projectID']= [projectID]
               args['queryname']= new_name,
               args['description']= [new_desc]
               new_query = internal.BuildDatasetQuery(request, args)
        elif qt == 'metadata':
            values = build_rule[qt]
            if len(values) > 1:
                tmp_queries = []
                for x, mylist in enumerate(values):
                    this_attr, this_oper, this_val = mylist
                    this_query = id_generator()
                    args = {'projectID': [projectID],
                            'attribute': [this_attr],
                            'cmp': [this_oper],
                            'v1': [this_val],
                            'queryname': [this_query]}
                    buildresult =  internal.BuildQuery(request, args)
                    tmp_queries.append(this_query)
                new_query = internal.MergeQuery(request, {'projectID': [projectID], 'queryname': tmp_queries, 'type':['intersection'], 'mergename': [new_name], 'description': [new_desc]})
                for tmp in tmp_queries:
                    status =  internal.DeleteQuery(request, {'queryname':[tmp.name], 'projectID':[projectID]})
            else:
                mylist = values[0]
                this_attr, this_oper, this_val = mylist
                new_query = internal.BuildQuery(request, {'projectID': [projectID], 'attribute': [this_attr], 'cmp': [this_oper], 'v1': [this_val], 'queryname': [new_name], 'description': [new_desc]})
        elif qt == 'list':
            samplelist = build_rule[qt]
            new_query = internal.BuildQueryFromList(request, {'projectID': [projectID], 'queryname': [new_name], 'description': [new_desc], 'sample': samplelist})    
        elif qt == 'merged':
            mergetype = build_rule[qt]['type']
            queries = build_rule[qt]['queries']
            tmplist = []
            for x, query_rules in enumerate(queries):
                tmp_name = id_generator()
                tmp_query = rebuild_query(request, projectID, query_rules, tmp_name)
                tmplist.append(tmp_name)
            new_query = internal.MergeQuery(request, {'projectID': [projectID], 'queryname': tmplist, 'type':[mergetype], 'mergename': [new_name], 'description': [new_desc]})
            for tmp in tmplist:
                status =  internal.DeleteQuery(request, {'queryname':[tmp.name], 'projectID':[projectID]})
        else:
            return None
    new_query.sqlstring = json.dumps(build_rule)
    new_query.save()
    return new_query   
