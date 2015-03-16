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

class Command(BaseCommand):
    args = '<project_id>'
    help = 'computes alpha diversity for a project and saves to the database'

    def handle(self, *args, **options):
        calculation = 'Alpha Diversity'
        alert('Searching for analysis data', color='BLUE')
        try: projectID = int(args[0])                                                        # unpack file and project ID arguments
        except: raise CommandError('Provide a project ID to compute '+calculation)      # report bad usage of command
        rows = Analysis.objects.filter(project=projectID)
        datasets = rows.values_list('dataset', flat=True).distinct()
        methods = rows.values_list('method', flat=True).distinct()
        categorys = rows.values_list('category', flat=True).distinct()
        alert('Found %d rows of analysis data' %len(rows))
        alert('\t%d datasets: %s' %(len(datasets), datasets))
        alert('\t%d methods: %s' %(len(methods), methods))
        alert('\t%d categories: %s' %(len(categorys), categorys))

        # check for old data for this computation
        olddata = Calculation.objects.filter(project = projectID, calculation = calculation)
        if olddata.exists(): 
          alert('Found old '+calculation+' calculations for this project(%d rows) - that data was removed. Everything will be recalculated based on the current project data.' % len(olddata))
          olddata.delete()


        try: p = Project.objects.get(id=projectID)
        except: raise CommandError('No project numbered %d' % projectID)          

        alert('Starting '+calculation+' calculations')

        newrows = 0
        for d in datasets:
          alert('\t%s' % d)
          for m in methods:
            alert('\t\t%s' % m)
            for c in categorys:
              alert('\t\t\t%s' % c)
              subset = rows.filter(dataset=d, method=m, category=c)
              samples = subset.values_list('sample', flat=True).distinct()  
              for s in samples:
                sampledata = subset.filter(sample=s)
                n = 0
                nnminus1 = 0
                for data in sampledata:
                  n+=data.numreads
                  nnminus1 += (data.numreads*(data.numreads - 1))
                  #print "%s\t%s\t%s\t%s\t%.02f" % (data.sample, data.dataset, data.method, data.category, data.numreads)
                try: D = (1.0*nnminus1) / (n*(n-1)) 
                except: D = 0 
                if D == 0: D = 1.0/len(sampledata) # set D equal to number of species if evenness is perfect
                #print "%s\t%s\t%.02f" %(s, c, 1/D)
                obj = Calculation(project = p,
                                  sample = s,
                                  dataset = d,
                                  method = m,
                                  category = c,
                                  calculation = calculation,
                                  value = 1/D)
                obj.save()
                newrows+=1
        alert('Completed '+calculation+' calculations - created %d new rows' % newrows)
