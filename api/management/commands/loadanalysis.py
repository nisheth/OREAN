from django.core.management.base import BaseCommand, CommandError
from api.models import *
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

def read_input(filename):
        fh = open(filename, 'rU')
        tmp = fh.readlines()
        fh.close()
        analysis = []
        for line in tmp:
            row = line.strip("\n").split("\t")
            for idx,val in enumerate(row[1:3], start=1): row[idx] = val.replace('.', '-')
            analysis.append(row)
        return analysis

class Command(BaseCommand):
    args = '<analysis_file project_id>'
    help = 'adds analysis data for a project to database'

    def handle(self, *args, **options):

        alert('Input Checking', color='BLUE') 
        # Unpack the input arguments
        try: filename, projectID = args								# unpack file and project ID arguments
        except: raise CommandError('Provide an analysis file and a project ID.')                       # report bad usage of command

        # Test File input
        try: inputdata = read_input(filename)
        except: raise CommandError('Error in accessing file "%s"' % (filename))  
        alert('\tSuccessfully read contents from "%s"' % filename)                                                      

        # Test project ID input
        try: project = Project.objects.get(pk=int(projectID))                                           # attempt to find the project for the given ID
        except Project.DoesNotExist: raise CommandError('Project "%s" does not exist' % projectID)      # report if the project ID does not exist
        alert('\tSuccessfully found project "%s" (%s)' % (projectID, project.name))                

        # Once usable data was input check validity of file contents
        header = inputdata.pop(0)
        count = 0
        for idx, line in enumerate(inputdata):
            count+=1
            
            # analysis data has 8 columns
            if len(line) != 8: raise CommandError('File "%s" fails validation. Must be 6 columns. Line: %d. Content: %s' % (filename, count, line))
   
            # Num of reads must be integer
            try: inputdata[idx][5] = int(line[5]) 
            except: raise CommandError('File "%s" fails validation. Column 6 must be an integer. Line: %d. Content: %s' % (filename, count, line)) 

            # profile must be a float
            try: inputdata[idx][6] = float(line[6])
            except: raise CommandError('File "%s" fails validation. Column 7 must be a float. Line: %d. Content: %s' % (filename, count, line)) 

            # average score must be a float
            try: inputdata[idx][7] =float(line[7])
            except: raise CommandError('File "%s" fails validation. Column 8 must be a float. Line: %d. Content: %s' % (filename, count, line)) 

        # Check if entries for these samples already exist
        samples = list(set(zip(*inputdata)[0]))
        regex = re.compile('[^0-9a-zA-Z_.]') # this is a list of the valid characters
        for s in samples:
            if bool(regex.findall(s)): raise CommandError('Sample syntax is invalid at sample "%s", only alpha, numeric, underscore, and dot characters are allowed' %s)
            if s[0].isdigit() or s[0] == "_": raise CommandError('Sample syntax is invalid at sample "%s", the first character must be a letter or a dot' %s)
            if s[0] == "." and s[1].isdigit(): raise CommandError('Sample syntax is invalid at sample "%s", the first character is a dot, so the second must be a letter' %s)
            if Analysis.objects.filter(project = project, sample = s).exists(): raise CommandError('Data exists for sample %s in project %s (%s). Aborting load...' %(s, projectID, project.name) )

        alert('\tFile "%s" passed all validation criteria. Contains %d rows of data' %(filename, count))                                   
        
        # Insert Validated Input into the database for the project
        alert('Adding data to database', color='BLUE')
        for data in inputdata:
            analysis = Analysis(project  = project,
                                sample   = data[0],
                                dataset  = data[1],
                                method   = data[2],
                                category = data[3],
                                entity   = data[4],
                                numreads = data[5],
                                profile  = data[6],
                                avgscore = data[7],
                               )
            analysis.save()
        alert('\tAnalysis data upload successful. Analysis contains %d rows.' % Analysis.objects.count())      
