from django.core.management.base import BaseCommand, CommandError
from api.uploads.utils import *

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
    args = '<taxa_tree_file taxonomy_id>'
    help = 'adds tree data for taxonomy'

    def handle(self, *args, **options):

        # Unpack the input arguments
        try: filename, taxonomy = args								# unpack file and project ID arguments
        except: raise CommandError('Provide a taxa tree file and a taxonomy ID.')               # report bad usage of command

        alert('Validating file', color='BLUE') 

        # Test File input
        validation = checkTaxaFile(filename, taxonomy)
        rowcount = validation['rows']

        # if validated run the insert function
        # otherwise report the errors found
        if validation['ok']:
            alert('Inserting taxa from validated file (%d rows)' % rowcount, color='BLUE') 
            resp = insertTaxaFromFile(filename, taxonomy, rowcount) 
            # this should always be ok since the validation passed, but check anyways
            if resp['ok']: 
                alert('Taxa data added successfully. Added %d taxa rows.' % resp['rows'])
            else:      
                alert(resp['msg'], color='FAIL')
        else: 
            alert('The file failed to validate', color='FAIL') 
            for m in validation['msg']:
                alert("\t"+m, color='FAIL')       
            
