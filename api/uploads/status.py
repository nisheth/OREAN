from django.shortcuts import render, redirect
from django.contrib import messages
from api.tasks import *

def main(request):
    params = {}
    uploads = UploadedFile.objects.filter(project__pk = request.session['projectID']).order_by('-datestamp')
    for upload in uploads:
        if upload.type == 'analysis':
           feedback = analysisFileTask.AsyncResult(upload.task_id)
        elif upload.type =='metadata': 
           feedback = metadataFileTask.AsyncResult(upload.task_id)
        elif upload.type == 'timeseries':
           feedback = timeseriesFileTask.AsyncResult(upload.task_id)
        upload.basename = upload.file.name.split('/')[-1]
        upload.feedback = feedback
    params['tasks'] = uploads

    if request.user.is_superuser:
        uploads = UploadedFile.objects.filter(type='taxonomy')
        for upload in uploads:
           feedback = taxonomyFileTask.AsyncResult(upload.task_id)
           upload.basename = upload.file.name.split('/')[-1]
           upload.feedback = feedback
    params['admintasks'] = uploads
    return render(request, 'uploadStatus.html', params)
