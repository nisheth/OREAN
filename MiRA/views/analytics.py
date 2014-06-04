from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from . import myutils
import json

@login_required
def main(request):
    params = {}
    params['queries'] = myutils.call_api(request, 'ListQueries')
    params['attributes'] = sorted([x['name'] for x in myutils.call_api(request, 'ListAttributes', params = {'projectID': 1})])
    return render(request, 'analytics.html', params)
