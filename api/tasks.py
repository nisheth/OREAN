from __future__ import absolute_import
from celery import shared_task, current_task
from celery.exceptions import Ignore
from time import sleep
from api.uploads.utils import *

@shared_task
def analysisFileTask(fileid, projectID, taxonomy=None):
    uploadedfile = UploadedFile.objects.get(pk=fileid)
    filename = uploadedfile.file.path
    meta={'type':'Analysis File', 'projectID': projectID, 'filename': filename.split('/')[-1], 'taxonomy':taxonomy}
    current_task.update_state(state='STARTED', meta=meta) 
    resp = insertAnalysisFromFile(filename,projectID,taxonomy)
    resp.update(meta)
    return resp

@shared_task
def taxonomyFileTask(fileid, taxonomy):
    uploadedfile = UploadedFile.objects.get(pk=fileid)
    filename = uploadedfile.file.path
    current_task.update_state(state='VALIDATING')
    validation = checkTaxaFile(filename, taxonomy)
    rowcount = validation['rows']
    if validation['ok']:
        current_task.update_state(state='ADDING TAXA')
        resp = insertTaxaFromFile(filename, taxonomy, rowcount)
        return resp
    else:
        # only keep taxonomy if the file is good
        Taxonomy.objects.get(pk=taxonomy).delete()
        return validation
    
@shared_task
def metadataFileTask(fileid, projectID):
    uploadedfile = UploadedFile.objects.get(pk=fileid)
    filename = uploadedfile.file.path
    meta={'type':'Metadata File', 'projectID': projectID, 'filename': filename.split('/')[-1]}
    current_task.update_state(state='STARTED', meta=meta)
    resp = insertMetadataFromFile(filename,projectID)
    resp.update(meta)
    return resp
