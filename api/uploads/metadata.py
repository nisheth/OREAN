from api.uploads.forms import *
from api.uploads.utils import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest
import json
import os,subprocess
from api.tasks import *

def main(request):
    params = {}
    fileform = UploadFileForm(initial={'type': 'metadata', 'user': request.user})
    if request.method == 'POST':
      fileform = UploadFileForm(request.POST,request.FILES)
      if fileform.is_valid():
        uploadedfile = fileform.save(commit=False)
        uploadedfile.project = Project.objects.get(pk=request.session['projectID'])
        uploadedfile.save() 
        task = metadataFileTask.delay(uploadedfile.pk, request.session['projectID'], fileform.cleaned_data['format'])
        uploadedfile.task_id = task.id
        uploadedfile.save()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')
      else: 
        messages.add_message(request, messages.ERROR, 'There was a problem with the analysis submission')
    params['fileform'] = fileform
    return render(request, 'uploadMetadata.html', params)

def timeseries(request):
    params = {}
    fileform = UploadFileForm(initial={'type': 'timeseries', 'user': request.user, 'format': 'matrix'})
    if request.method == 'POST':
      fileform = UploadFileForm(request.POST,request.FILES)
      if fileform.is_valid():
        uploadedfile = fileform.save(commit=False)
        uploadedfile.project = Project.objects.get(pk=request.session['projectID'])
        uploadedfile.save()
        task = timeseriesFileTask.delay(uploadedfile.pk, request.session['projectID'])
        uploadedfile.task_id = task.id
        uploadedfile.save()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')
      else:
        return HttpResponseBadRequest(json.dumps(fileform.errors), content_type='application/json')
    params['fileform'] = fileform
    return render(request, 'uploadTimeseries.html', params)
