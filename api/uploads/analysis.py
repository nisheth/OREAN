from api.uploads.forms import *
from api.uploads.utils import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
import json
import os,subprocess
from api.tasks import analysisFileTask

def main(request):
    params = {}
    form = UploadAnalysisForm()
    fileform = UploadFileForm(initial={'type': 'analysis', 'user': request.user})
    if request.method == 'POST':
      form = UploadAnalysisForm(request.POST,request.FILES)
      fileform = UploadFileForm(request.POST,request.FILES)
      if form.is_valid() and fileform.is_valid():
        taxonomy=None
        if form.cleaned_data['taxonomy']: taxonomy=form.cleaned_data['taxonomy'].pk
        uploadedfile = fileform.save(commit=False)
        uploadedfile.project = Project.objects.get(pk=request.session['projectID'])
        uploadedfile.save() 
        # write file
        #file = '/tmp/%s' % request.FILES['file']
        #with open(file, 'wb+') as destination:
        #    for chunk in request.FILES['file'].chunks(chunk_size=1024*10):
        #       destination.write(chunk)
        #try:
        #   tempFilePath = request.FILES['file'].temporary_file_path()
        #   os.remove(tempFilePath)
        #except:
        #   pass
        #args = ["python", "manage.py", "loadanalysis", file, str(request.session['projectID'])]
        #if taxonomy: args.append(str(taxonomy))
        #subprocess.Popen(args)
        #messages.add_message(request, messages.SUCCESS, 'Started adding the new project data to the database')
        # form = UploadAnalysisForm()
        task = analysisFileTask.delay(uploadedfile.pk, request.session['projectID'], taxonomy)
        uploadedfile.task_id = task.id
        uploadedfile.save()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')
      else: 
        messages.add_message(request, messages.ERROR, 'There was a problem with the analysis submission')
    params['form'] = form
    params['fileform'] = fileform
    return render(request, 'uploadAnalysis.html', params)
