from django.core.management.base import BaseCommand, CommandError
from api.models import *
import datetime
import re

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def alert(cmd, color='GREEN'):
    print eval('bcolors.'+color) + cmd + bcolors.ENDC

class Command(BaseCommand):
    args = '<attribute_file project_id>'
    help = 'adds attribute data for a project to database'

    def handle(self, *args, **options):

        alert('Input Checking', color='BLUE') 
        # Unpack the input arguments
        try: filename, projectID = args								# unpack file and project ID arguments
        except: raise CommandError('Provide a mapping file and a project ID.')                	# report bad usage of command

        # Test project ID input
        try: project = Project.objects.get(pk=int(projectID))                                           # attempt to find the project for the given ID
        except Project.DoesNotExist: raise CommandError('Project "%s" does not exist' % projectID)      # report if the project ID does not exist
        alert('\tSuccessfully found project "%s" (%s)' % (projectID, project.name))                

        if SubjectMap.objects.filter(project = project).exists(): 
            alert('\tWARNING: existing mappings are found for this project. They will be replaced.', color='WARNING')
            SubjectMap.objects.filter(project = project).delete()

        f = open(filename, 'U')
        header = f.readline()
        # Insert Validated Input into the database for the project
        alert('Adding data to database', color='BLUE')
        i = 0
        for line in f:
          i+=1
          try:
            line = line.strip()
            subject, visit, sample = line.split('\t')
            newMap = SubjectMap(project = project,
                                subject = subject,
                                visit = visit,
                                sample = sample
                               )
            newMap.save()
          except:
            alert('\tError in adding mapping data on input line %d -- could not add mappings for this project (%s)' % (i, project.name), color='FAIL')
            SubjectMap.objects.filter(project = project).delete()

        alert('\tMapping data upload successful. Mapping data contains %d rows.' % SubjectMap.objects.count())      
