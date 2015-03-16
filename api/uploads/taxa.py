from api.models import *
from api.uploads.forms import *
from django.shortcuts import render, redirect
from django.contrib import messages

def main(request):
    params = {}
    form = UploadTaxaForm()
    if request.method == 'POST':
      form = UploadTaxaForm(request.POST)
      if form.is_valid():
        taxVersion = form.save()
        messages.add_message(request, messages.SUCCESS, "New taxonomy '%s' added successfully" % ( taxVersion.name ))
        form = UploadTaxaForm()
      else: 
        messages.add_message(request, messages.ERROR, 'There was a problem with the submission')
    params['form'] = form
    return render(request, 'uploadTaxa.html', params)
