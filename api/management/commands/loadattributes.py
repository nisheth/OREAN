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

def read_input(filename):
        fh = open(filename, 'rU')
        tmp = fh.readlines()
        fh.close()
        attributes = []
        for line in tmp:
            row = line.strip("\n").split("\t")
            if row[-1] == "": row[-1] = "EMPTY"
            if len(row) < 4: row.append("EMPTY")
            attributes.append(row)
        return attributes

def dateparse(s):
    formats = ['%Y-%m-%d', '%Y_%m_%d', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y', '%m/%d/%Y', '%Y-%m-%d']
    for form in formats:
        try: 
            s = datetime.datetime.strptime(s, form)
            return s
        except: 
            pass
    return s

def getfieldtype(s):
    try:
        s = float(s)
        return 'DECIMAL'
    except: pass
    try: 
        s = dateparse(s)
        if isinstance(s, datetime.datetime): return 'DATE'
        else: return 'STRING'
    except:
        return 'STRING'
    
class Command(BaseCommand):
    args = '<attribute_file project_id>'
    help = 'adds attribute data for a project to database'

    def handle(self, *args, **options):

        alert('Input Checking', color='BLUE') 
        # Unpack the input arguments
        try: filename, projectID = args								# unpack file and project ID arguments
        except: raise CommandError('Provide an attribute file and a project ID.')               # report bad usage of command

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
        typecheck = {}
        for idx, line in enumerate(inputdata):
            count+=1
            # attribute data has 4 columns
            if len(line) != 4: raise CommandError('File "%s" fails validation. Must be 4 columns. Line: %d. Content: %s' % (filename, count, line))
            if line[3] not in typecheck: typecheck[line[2]] = getfieldtype(line[3])    
            elif getfieldtype(line[3]) != typecheck[line[2]]: raise CommandError('File "%s" fails validation. Field "%s" has inconsistent type. Expected a "%s" but found a "%s". Line: %d. Content: %s' % (filename, line[2], typecheck[line[2]], getfieldtype(line[3]), count, line))
        # Check if entries for these samples already exist and sample formatting
        samples = list(set(zip(*inputdata)[0]))
        regex = re.compile('[^0-9a-zA-Z_.]') # this is a list of the valid characters
        for s in samples:
            if bool(regex.findall(s)): raise CommandError('Sample syntax is invalid at sample "%s", only alpha, numeric, underscore, and dot characters are allowed' %s)
            if s[0].isdigit() or s[0] == "_": raise CommandError('Sample syntax is invalid at sample "%s", the first character must be a letter or a dot' %s)
            if s[0] == "." and s[1].isdigit(): raise CommandError('Sample syntax is invalid at sample "%s", the first character is a dot, so the second must be a letter' %s)
            if Attributes.objects.filter(project = project, sample = s).exists(): raise CommandError('Data exists for sample %s in project %s (%s). Aborting load...' %(s, projectID, project.name) )
        alert('\tFile "%s" passed all validation criteria. Contains %d rows of data' %(filename, count))                                   
        
        # Insert Validated Input into the database for the project
        alert('Adding data to database', color='BLUE')
        for data in inputdata:
            data[3] = dateparse(data[3])
            if isinstance(data[3], datetime.datetime): data[3] = data[3].strftime('%Y-%m-%d')
                    
            attributes = Attributes(project  = project,
                                    sample   = data[0],
                                    category = data[1],
                                    field    = data[2],
                                    value    = data[3],
                                   )
            if not AttributeInfo.objects.filter(project=project, name=attributes.field).exists():
                alert('\tNo Attribute Info for %s. Adding now...' % attributes.field, color='WARNING')      
                newinfo = AttributeInfo(project   = project,
                                        name      = attributes.field,
                                        fieldtype = getfieldtype(attributes.value),
                                        values    = "",
                                       )
                newinfo.save()
            attributes.save()
        alert('\tAttributes data upload successful. Attributes contains %d rows.' % Attributes.objects.count())      
