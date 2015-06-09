from django.core.management.base import BaseCommand, CommandError
from api.models import *
from OREAN.views import SCRIPTPATH
from OREAN.views import myutils 
import re, sys, time

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def alert(cmd, color='GREEN'):
    print eval('bcolors.'+color) + cmd + bcolors.ENDC

def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = int(sec_elapsed % 60)
    return "{}:{:>02}:{:>02}".format(h, m, s)

class Command(BaseCommand):
    args = '<project_id>'
    help = 'computes beta diversity for a project and saves to the database'

    def handle(self, *args, **options):
        calculation = 'Beta Diversity'
        alert('Searching for analysis data', color='BLUE')
        try: projectID = int(args[0])                                                        # unpack file and project ID arguments
        except: raise CommandError('Provide a project ID to compute '+calculation)      # report bad usage of command
        rows = Analysis.objects.filter(project=projectID)
        datasets = rows.values_list('dataset', flat=True).distinct()
        methods = rows.values_list('method', flat=True).distinct()
        categorys = rows.values_list('category', flat=True).distinct()
        samples = rows.values_list('sample', flat=True).distinct()
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

        expected_new_rows = ( len(datasets) * len(methods) * len(categorys) * ( ( len(samples) * ( len(samples) - 1 ) ) / 2 ) )
        alert('Starting '+calculation+' calculations ( estimating %d new rows )' %( expected_new_rows ) )

        newrows = 0
        start_time = time.time()
        for d in datasets:
          alert('\t%s' % d)
          for m in methods:
            alert('\t\t%s' % m)
            for c in categorys:
              entities = []
              datahash = {}
              alert('\t\t\t%s' % c)
              subset = rows.filter(dataset=d, method=m, category=c)
              subset.order_by('sample')
              samples = list(subset.values_list('sample', flat=True).distinct())
              samples.sort()
              f = open('tmp.txt', 'w')
              for s in subset:
                if s.entity not in entities:
                    entities.append(s.entity)
                if s.sample not in datahash:
                    datahash[s.sample] = {}
                datahash[s.sample][s.entity] = s.profile
              f.write("%d %d\n" %(len(samples), len(entities)))
              for sample in samples:
                  mycontent = sample
                  for taxa in entities:
                      mycontent+=','
                      if taxa in datahash[sample]: mycontent+=str(datahash[sample][taxa])
                      else: mycontent += str('0')
                  mycontent+='\n'
                  f.write(mycontent)
#              for i,s1 in enumerate(samples):
#                s1data = subset.filter(sample=s1)
#                for j in range(i+1, len(samples)):
#                  s2 = samples[j]
#                  s2data = subset.filter(sample=s2)
#                  sa = 0
#                  sb = 0
#                  min_sasb = 0
#                  seen = {}
#                  for s1_item in s1data:
#                      s2_item = s2data.filter(entity=s1_item.entity)
#                      seen[s1_item.entity] = 1
#                      sa += s1_item.profile
#                      if s2_item.exists():
#                          s2_item = s2_item[0]
#                          sb+=s2_item.profile
#                          min_sasb += min([s1_item.profile, s2_item.profile])
#                      else: continue
#                  for s2_item in s2data:
#                      if s2_item.entity in seen: continue
#                      else:
#                          sb+=s2_item.profile
#                  BC = 1 - (2 * ( ( 1.0 * min_sasb ) / ( sa+sb ) ) )
#                  obj = PairwiseCalculation(project = p,
#                                            sample1 = s1,
#                                            sample2 = s2,
#                                            dataset = d,
#                                            method = m,
#                                            category = c,
#                                            calculation = calculation,
#                                            value = BC)
#                  #obj.save()
#                  newrows+=1
#                  if newrows % 100 == 0: 
#                      elapsed_time = time.time() - start_time
#                      alert("\t\t\t\t%d of an estimated %d [%.02f%s] about %s remaining" %(newrows, expected_new_rows, (100.0*newrows)/expected_new_rows, '%', hms_string( (expected_new_rows - newrows)/(1.*newrows/elapsed_time) )))  
              f.close() 
              output_raw = myutils.runC('braycurtis_for_database', 'tmp.txt')
              output_lines = output_raw.split('\n')
              for result in output_lines:
                  if result == "": continue
                  s1, s2, BC = result.split('\t')
                  BC = float(BC)
                  obj = PairwiseCalculation(project = p,
                                            sample1 = s1,
                                            sample2 = s2,
                                            dataset = d,
                                            method = m,
                                            category = c,
                                            calculation = calculation,
                                            value = BC)
                  obj.save()
                  newrows+=1
                  if newrows % 10000 == 0: 
                      elapsed_time = time.time() - start_time
                      alert("\t\t\t\t%d of an estimated %d [%.02f%s] about %s remaining" %(newrows, expected_new_rows, (100.0*newrows)/expected_new_rows, '%', hms_string( (expected_new_rows - newrows)/(1.*newrows/elapsed_time) )))  
              elapsed_time = time.time() - start_time
              alert("\t\t\t\t%d of an estimated %d [%.02f%s] about %s remaining" %(newrows, expected_new_rows, (100.0*newrows)/expected_new_rows, '%', hms_string( (expected_new_rows - newrows)/(1.*newrows/elapsed_time) )))
        alert('Completed '+calculation+' calculations - created %d new rows' % newrows)
        alert('Upload time: %s ' % hms_string(time.time() - start_time))
