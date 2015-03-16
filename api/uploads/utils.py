from api.models import *
import re, sys, traceback, time
import datetime

# Check taxa file method
# Requires a filename and a taxonomy id #
# returns a dictionary of the following structure
# {'ok': True/False, 'msgs': [], 'rows': rowcount}
# input file format:
#Taxa_id	parent_taxa_id	taxa_name	taxa_level
def checkTaxaFile(file, taxonomy):
    resp = {'ok': False, 'msg': [], 'rows': 0}
    try:
       taxonomy = Taxonomy.objects.get(pk=taxonomy)
    except: 
       resp['msg'].append('Unable to find the taxonomy metadata entry for %d' % taxonomy)
       return resp
    if TaxaTree.objects.filter(taxonomy=taxonomy).exists():
       resp['msg'].append('Taxonomy tree data already exists in database for taxonomy named "%s". Aborting.' % taxonomy.name)
       return resp
    try:
        fh = open(file, 'U')
    except:
        resp['msg'].append('Unable to open taxa tree file for reading')
        return resp
    seen_taxa = {}
    count = 0
    for count,line in enumerate(fh, start=1):
        line = line.strip()
        row = line.split('\t')
        if len(row) != 4:
            resp['msg'].append('Line %d: does not contain 4 columns' % ( count ))
            continue
        tax_id,parent_id,taxa_name,taxa_level = row
        if count > 1 and parent_id not in seen_taxa:
            resp['msg'].append('Line %d: parent taxa ID was not seen previously - parent taxa must appear before child taxa' % ( count ))
        if tax_id in seen_taxa:
            resp['msg'].append('Line %d: taxa ID was seen previously - must be unique' % ( count ))
        seen_taxa[tax_id] = True
        if count % 1000 == 0: print >> sys.stderr, 'processed %d rows' % ( count )
    fh.close()
    print >> sys.stderr, 'processed %d rows' % ( count )
    resp['rows'] = count
    if len(resp['msg']) == 0: resp['ok'] = True
    return resp

# inserts rows from a taxa file
# assumes file was validated previously by
# running the 'checkTaxaFile' method above
# returns dictionary in the following format
# {'ok': True/False, 'rows': NewRowCount, 'msg': None or 'Unexpected error'}
def insertTaxaFromFile(file, taxonomy, total):
    start = time.time()
    resp = {'ok': False, 'rows': 0, 'msg': None}
    try:
        taxonomy = Taxonomy.objects.get(pk=taxonomy)
        fh = open(file, 'U')
        for line in fh:
            line = line.strip()
            row = line.split('\t')
            tax_id,parent_id,taxa_name,taxa_level = row
            full_tree = None
            if resp['rows'] == 0: 
                parent_id = None
                full_tree = taxa_name
            else: 
                parent_id = TaxaTree.objects.get(taxonomy=taxonomy, tax_id = int(parent_id))
                full_tree = parent_id.full_tree + '|'+taxa_name
            tt = TaxaTree(tax_id=tax_id,
                          parent_id = parent_id,
                          tax_name=taxa_name,
                          tax_level=taxa_level,
                          taxonomy = taxonomy,
                          full_tree=full_tree,
                         )
            tt.save()
            resp['rows'] += 1
            if resp['rows'] % 1000 == 0: print >> sys.stderr, 'processed %d rows out of %d [%.02f seconds remaining]' % ( resp['rows'], total, ((time.time() - start)/resp['rows'])*(total-resp['rows']) )
        fh.close()
        print >> sys.stderr, 'processed %d rows out of %d [%.02f seconds remaining]' % ( resp['rows'], total, ((time.time() - start)/resp['rows'])*(total-resp['rows']) )
        resp['ok'] = True
    except:
        resp['msg'] = 'Unexpected error, please run verification on file. Traceback: %s' % traceback.format_exc()
    return resp    

def prepareAnalysisLine(line):
    row = line.strip("\n").split("\t")
    for idx,val in enumerate(row[1:3], start=1): row[idx] = val.replace('.', '-')
    return row

# insert analysis data
# validates first then inserts
# returns dictionary of status
def insertAnalysisFromFile(filename, projectID, taxonomy=None):
    resp = {'ok': False, 'msg': [], 'rows': 0}
    samples = dict()

    # Test File input
    try: 
        fh = fh = open(filename, 'rU')
        num_lines = sum(1 for line in fh)
        fh.seek(0)
    except: 
        resp['msg'].append('Error in accessing file "%s"' % (filename))
        return resp

    print >> sys.stderr, "file contains %d lines" % num_lines
    
    # Test project ID input
    try: project = Project.objects.get(pk=int(projectID))                                     # attempt to find the project for the given ID
    except Project.DoesNotExist: 
        resp['msg'].append('Project "%s" does not exist' % projectID)			      # report if the project ID does not exist
	return resp

    # test taxonomy input
    if taxonomy:
        try: 
           taxonomy = Taxonomy.objects.get(pk=int(taxonomy))
        except: 
            resp['msg'].append('Unable to determine the taxonomy information (%s)' % taxonomy)
            return resp

    # Once usable data was input check validity of file contents
    header = fh.next()
    count = 0
    taxas = dict()

    print >> sys.stderr, "starting line validation"
    start = datetime.datetime.now()
    for idx, line in enumerate(fh):
        count+=1

        line = prepareAnalysisLine(line)
        samples[line[0]] = samples.get(line[0], 0) + 1

        # analysis data has 9 columns
        if len(line) != 9: 
            resp['msg'].append('File "%s" fails validation. Must be 9 columns. Line: %d. Content: %s' % (filename, count, line))
            return resp

        # Num of reads must be integer
        #try: inputdata[idx][6] = int(line[6])
        try: int(line[6])
        except: 
            resp['msg'].append('File "%s" fails validation. Column 7 must be an integer. Line: %d. Content: %s' % (filename, count, line))
            return resp

        # profile must be a float
        #try: inputdata[idx][7] = float(line[7])
        try: float(line[7])
        except:  
            resp['msg'].append('File "%s" fails validation. Column 8 must be a float. Line: %d. Content: %s' % (filename, count, line))
            return resp

        # average score must be a float
        #try: inputdata[idx][8] =float(line[8])
        try: float(line[8])
        except: 
            resp['msg'].append('File "%s" fails validation. Column 9 must be a float. Line: %d. Content: %s' % (filename, count, line))
            return resp

        # try to find taxa if applicable
        if taxonomy:
            try: 
                tax_id = int(line[5])
                if tax_id not in taxas:
                   taxas[tax_id] = TaxaTree.objects.get(taxonomy=taxonomy, tax_id=int(line[5]))
            except: 
                resp['msg'].append('File "%s" fails validation. Unable to find taxa. Line %d. Content: %s' % (filename, count, line))
                return resp
        if (count % 10000 == 0): 
            elapsed = (datetime.datetime.now() - start).seconds
            print >> sys.stderr, "\t%d lines checked of %d [about %d seconds remaining]" % (count, num_lines, (num_lines - count)/(count/elapsed))

    print >> sys.stderr, "starting sample validation"
    # Check if entries for these samples already exist
    regex = re.compile('[^0-9a-zA-Z_.]') # this is a list of the valid characters
    for s in samples:
        if bool(regex.findall(s)): 
            resp['msg'].append('Sample syntax is invalid at sample "%s", only alpha, numeric, underscore, and dot characters are allowed' %s)
            return resp
        if s[0].isdigit() or s[0] == "_": 
            resp['msg'].append('Sample syntax is invalid at sample "%s", the first character must be a letter or a dot' %s)
            return resp
        if s[0] == "." and s[1].isdigit(): 
            resp['msg'].append('Sample syntax is invalid at sample "%s", the first character is a dot, so the second must be a letter' %s)
            return resp
        if Analysis.objects.filter(project = project, sample = s).exists(): 
            resp['msg'].append('Data exists for sample %s in project %s (%s). Aborting load...' %(s, projectID, project.name) )
            return resp

    # Insert Validated Input into the database for the project
    fh.seek(0)
    fh.next() # skip header
    print >> sys.stderr, "inserting data"
    count= 0
    batch = []
    start = datetime.datetime.now()
    for line in fh:
        count+=1
        data = prepareAnalysisLine(line)
        analysis = Analysis(project  = project,
                            sample   = data[0],
                            dataset  = data[1],
                            method   = data[2],
                            category = data[3],
                            entity   = data[4],
                            taxatree = taxas[int(data[5])],
                            numreads = int(data[6]),
                            profile  = float(data[7]),
                            avgscore = float(data[8]),
                           )
        batch.append(analysis)
        if (count % 10000 == 0):
            Analysis.objects.bulk_create(batch)
            elapsed = (datetime.datetime.now() - start).seconds
            print >> sys.stderr, "\t%d rows added of %d [about %d seconds remaining]" % (count, num_lines, (num_lines - count)/(count/elapsed))
            batch = []
    if len(batch) > 0:
        Analysis.objects.bulk_create(batch)
    if len(resp['msg']) == 0: resp['ok']=True
    resp['rows'] = count
    fh.close()
    return resp
