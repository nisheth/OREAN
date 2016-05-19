from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token
from django.contrib import messages
import urllib2
import urllib
import traceback
import json
import os,subprocess
from OREAN.views import SCRIPTPATH
from api.models import *
from django.db.models import Max, Avg, Count

def call_api(request, api, params={}, is_post=False):
    if 'projectID' in request.session: params['projectID'] = request.session['projectID']
    try:
        token = Token.objects.get(user=request.user)
        args = urllib.urlencode(params, doseq=True)
        url = handle = None
        if not is_post:
            url = request.build_absolute_uri(reverse(api))+'?%s' % args
            handle = urllib2.Request(url)
        else: 
            url = request.build_absolute_uri(reverse(api))
            handle = urllib2.Request(url, args)
        authheader = "Token %s" % token.key
        handle.add_header("Authorization", authheader)
        results = urllib2.urlopen(handle)
        data = json.load(results)
        return data
    except: raise Exception(traceback.format_exc())

def fieldexpand(s):
    return s.split(',')

def runRscript(script, file):
    cmd = ['Rscript', SCRIPTPATH+'r/'+script, file]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, err = p.communicate()
    return out

def runPerl(script, file):
    cmd = ['perl', SCRIPTPATH+'misc/'+script, file]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, err = p.communicate()
    print out
    return out

def runPython(script, file, args=None):
    try:
        cmd = ['python', SCRIPTPATH+'misc/'+script, file]
        if args: cmd+=args
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return out
    except:
        return "%s" % traceback.format_exc()

def runCmd(cmd):
    return os.system(cmd)

def runC(script, file):
    cmd = [SCRIPTPATH+'c/'+script, file]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, err = p.communicate()
    return out

def topTaxa(projectID, querynames, dataset, method, category, LIMIT=20):
    samplelist = []
    for q in Query.objects.filter(project_id=projectID, name__in=querynames):
      samplelist+=q.expandsamples
    samplelist = list(set(samplelist))
    #results = Analysis.objects.filter(project_id=projectID, sample__in=samplelist, dataset=dataset, method=method, category=category).values('entity').annotate(Avg('profile')).order_by('-profile__avg')[:LIMIT]
    results = Analysis.objects.filter(project_id=projectID, sample__in=samplelist, dataset=dataset, method=method, category=category).values('entity').annotate(Count('entity')).order_by('-entity__count')[:LIMIT]
    return [str(s['entity']) for s in results]

def activateProject(request, project):
    try:
      ap = ActiveProject.objects.get_or_none(user=request.user)
      if ap is None:
          ap = ActiveProject(user=request.user, project=project)
      else:
          ap.project = project
      ap.save()
      request.session['projectID'] = project.pk
      request.session['projectName'] = project.name
      request.session['projectTimecourse'] = ap.project.is_timecourse()
      messages.add_message(request, messages.SUCCESS, "Project changed to %s" %project.name)
    except:
      messages.add_message(request, messages.ERROR, "Unexpected error while selecting the project (%s)" % traceback.format_exc())

def updateSampleCounts(projectID):
  try:
    p = Project.objects.get(pk=projectID)
    sampleCount = Analysis.objects.filter(project=p).values_list('sample', flat=True).distinct().count()
    sampleCountMeta = Attributes.objects.filter(project=p).values_list('sample', flat=True).distinct().count()
    p.attribute_samples = sampleCountMeta
    p.data_samples = sampleCount
    p.save()
    return True
  except:
    return False
