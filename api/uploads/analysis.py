from api.uploads.forms import *
from api.uploads.utils import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
import json
import os,subprocess

def main(request):
    params = {}
    form = UploadAnalysisForm()
    if request.method == 'POST':
      form = UploadAnalysisForm(request.POST,request.FILES)
      if form.is_valid():
        taxonomy=None
        if form.cleaned_data['taxonomy']: taxonomy=form.cleaned_data['taxonomy'].pk
        # write file
        file = '/tmp/%s' % request.FILES['file']
        with open(file, 'wb+') as destination:
            for chunk in request.FILES['file'].chunks(chunk_size=1024*10):
               destination.write(chunk)
        try:
           tempFilePath = request.FILES['file'].temporary_file_path()
           os.remove(tempFilePath)
        except:
           pass
        #args = ["python", "manage.py", "loadanalysis", file, str(request.session['projectID'])]
        #if taxonomy: args.append(str(taxonomy))
        #subprocess.Popen(args)
        #messages.add_message(request, messages.SUCCESS, 'Started adding the new project data to the database')
        # form = UploadAnalysisForm()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')
      else: 
        messages.add_message(request, messages.ERROR, 'There was a problem with the analysis submission')
    params['form'] = form
    return render(request, 'uploadAnalysis.html', params)
