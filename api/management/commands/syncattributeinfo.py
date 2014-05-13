from django.core.management.base import BaseCommand, CommandError
from api.models import *
import traceback
import datetime

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def alert(cmd, color='GREEN'):
    print eval('bcolors.'+color) + cmd + bcolors.ENDC

def numrange(array):
    ranges = ['EMPTY', 'EMPTY']
    for x in array:
        if x =='EMPTY': continue
        if ranges[0] == 'EMPTY' or float(x) < float(ranges[0]): ranges[0] = x 
        if ranges[1] == 'EMPTY' or float(x) > float(ranges[1]): ranges[1] = x
    return ranges

def todate(s):
    return datetime.datetime.strptime(s, '%Y-%m-%d')

def daterange(array):
    ranges = ['EMPTY', 'EMPTY']
    for x in array:
        if x =='EMPTY': continue
        if ranges[0] == 'EMPTY' or todate(x) < todate(ranges[0]): ranges[0] = x
        if ranges[1] == 'EMPTY' or todate(x) > todate(ranges[1]): ranges[1] = x
    return ranges

class Command(BaseCommand):
    args = '<analysis_file project_id>'
    help = 'adds analysis data for a project to database'

    def handle(self, *args, **options):
        alert('Collecting Attributes', color='BLUE') 
        for p in Project.objects.all():
            try: attributes = Attributes.objects.filter(project=p.pk).values_list('field', flat=True).distinct()		# get a list of attribute fields
            except: raise CommandError('Error in extracting attribute fields\n %s' % traceback.format_exc())                       	# report bad usage of command
            alert('\tSuccessfully collected %d unique attributes for project %d' % (len(attributes), p.pk))                
    
            for attr in attributes:
                values = Attributes.objects.filter(field=attr).values_list('value', flat=True).distinct()
                info = AttributeInfo.objects.get(project=p.pk, name=attr)
                myvals = ""
                if info.fieldtype == 'STRING': myvals =  ",".join(values)
                elif info.fieldtype == 'DECIMAL': myvals =  ','.join(numrange(values))
                else: myvals = ','.join(daterange(values)) 
                info.values = myvals          
                info.save()
        alert('\tAttribute info sync successful.')      
