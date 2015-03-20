from api.models import *
from api.uploads.forms import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from api.tasks import *
import json

def main(request):
    params = {}
    form = UploadTaxaForm()
    fileform = UploadFileForm(initial={'type': 'taxonomy', 'user': request.user})
    if request.method == 'POST':
      form = UploadTaxaForm(request.POST)
      fileform = UploadFileForm(request.POST,request.FILES)
      if form.is_valid() and fileform.is_valid():
        taxVersion = form.save()
        uploadedfile = fileform.save()
        #messages.add_message(request, messages.SUCCESS, "New taxonomy '%s' added successfully" % ( taxVersion.name ))
        #form = UploadTaxaForm()
        task = taxonomyFileTask.delay(uploadedfile.pk, taxVersion.id)
        uploadedfile.task_id = task.id
        uploadedfile.save()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')
      else: 
        #messages.add_message(request, messages.ERROR, 'There was a problem with the submission')
        return HttpResponse(json.dumps({'status': 'bad form data'}), content_type='application/json')
    params['form'] = form
    params['fileform'] = fileform
    return render(request, 'uploadTaxa.html', params)
