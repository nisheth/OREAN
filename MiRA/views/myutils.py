from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token
import urllib2
import urllib
import traceback
import json
import subprocess
from MiRA.views import SCRIPTPATH
from api.models import *
from django.db.models import Max, Avg

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

def runC(script, file):
    cmd = [SCRIPTPATH+'c/'+script, file]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, err = p.communicate()
    return out

def topTaxa(querynames, dataset, method, category, LIMIT=20):
    samplelist = []
    for q in Query.objects.filter(name__in=querynames):
      samplelist+=q.expandsamples
    samplelist = list(set(samplelist))
    results = Analysis.objects.filter(dataset=dataset, method=method, category=category).values('entity').annotate(Avg('profile')).order_by('-profile__avg')[:LIMIT]
    return [str(s['entity']) for s in results]
