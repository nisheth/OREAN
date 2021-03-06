from OREAN.views.myutils import updateSampleCounts
from api.models import *
from biom import load_table
from collections import defaultdict
import re, sys, traceback, time
import datetime

# Check taxa file method
# Requires a filename and a taxonomy id #
# returns a dictionary of the following structure
# {'ok': True/False, 'msg': [], 'rows': rowcount}
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
    regex = re.compile('[^0-9a-zA-Z_.]') # this is a list of the valid characters
    for idx, line in enumerate(fh):
        count+=1

        line = prepareAnalysisLine(line)
        samples[line[0]] = samples.get(line[0], 0) + 1
        acceptedSamples = dict()

        # check for previous submission
        if line[0] not in acceptedSamples:
            s = line[0]
            if bool(regex.findall(s)):
                resp['msg'].append('Sample syntax is invalid at sample "%s", only alpha, numeric, underscore, and dot characters are allowed' %s)
                return resp
            if s[0].isdigit() or s[0] == "_":
                resp['msg'].append('Sample syntax is invalid at sample "%s", the first character must be a letter or a dot' %s)
                return resp
            if s[0] == "." and s[1].isdigit():
                resp['msg'].append('Sample syntax is invalid at sample "%s", the first character is a dot, so the second must be a letter' %s)
                return resp
            if Analysis.objects.filter(project = project, sample = s, dataset=line[1], method=line[2], category=line[3], entity=line[4]).exists():
                resp['msg'].append('Data exists for sample %s in project %s (%s). Aborting load...' %(s, projectID, project.name) )
                return resp
            acceptedSamples[line[0]] = True

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
                #tax_id = int(line[5])
                tax_id = line[5]
                if tax_id not in taxas:
                   taxas[tax_id] = TaxaTree.objects.get(taxonomy=taxonomy, tax_id=int(line[5]))
            except: 
                resp['msg'].append('File "%s" fails validation. Unable to find taxa. Line %d. Content: %s' % (filename, count, line))
                return resp
        else:
            #taxas[int(line[5])] = None
            taxas[line[5]] = None
        if (count % 10000 == 0): 
            elapsed = (datetime.datetime.now() - start).seconds
            if elapsed == 0: elapsed = 1
            print >> sys.stderr, "\t%d lines checked of %d [about %d seconds remaining]" % (count, num_lines, (num_lines - count)/(count/elapsed))

    print >> sys.stderr, "starting sample validation"
    # Check if entries for these samples already exist
    #regex = re.compile('[^0-9a-zA-Z_.]') # this is a list of the valid characters
    #for s in samples:
    #    if bool(regex.findall(s)): 
    #        resp['msg'].append('Sample syntax is invalid at sample "%s", only alpha, numeric, underscore, and dot characters are allowed' %s)
    #        return resp
    #    if s[0].isdigit() or s[0] == "_": 
    #        resp['msg'].append('Sample syntax is invalid at sample "%s", the first character must be a letter or a dot' %s)
    #        return resp
    #    if s[0] == "." and s[1].isdigit(): 
    #        resp['msg'].append('Sample syntax is invalid at sample "%s", the first character is a dot, so the second must be a letter' %s)
    #        return resp

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
                            #taxatree = taxas[int(data[5])],
                            taxatree = taxas[data[5]],
                            numreads = int(data[6]),
                            profile  = float(data[7]),
                            avgscore = float(data[8]),
                           )
        batch.append(analysis)
        if (count % 10000 == 0):
            Analysis.objects.bulk_create(batch)
            elapsed = (datetime.datetime.now() - start).seconds
            if elapsed == 0: elapsed = 1
            print >> sys.stderr, "\t%d rows added of %d [about %d seconds remaining]" % (count, num_lines, (num_lines - count)/(count/elapsed))
            batch = []
    if len(batch) > 0:
        Analysis.objects.bulk_create(batch)
    ok = updateSampleCounts(projectID)
    if len(resp['msg']) == 0: resp['ok']=True
    resp['rows'] = count
    fh.close()
    return resp

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

def insertMetadataFromFile(filename, projectID):
    resp = {'ok': False, 'msg': [], 'rows': 0}

    # Test File input
    try: 
        #inputdata = read_input(filename)
        fh = open(filename)
    except:
        resp['msg'].append('Error in accessing file "%s"' % (filename))
        return resp

    # Test project ID input
    try: 
        project = Project.objects.get(pk=int(projectID))                                           # attempt to find the project for the given ID
    except Project.DoesNotExist: 
        resp["msg"].append('Project "%s" does not exist' % projectID)      # report if the project ID does not exist
        return resp

    # Once usable data was input check validity of file contents
    #header = inputdata.pop(0)
    header = fh.next().strip().split('\t')
    count = 0
    typecheck = {}
    validsamples = {}
    #for idx, line in enumerate(inputdata):
    for line_str in fh:
        count+=1
        line = line_str.strip().split('\t')
	s = line[0]
        # attribute data has 4 columns
        if len(line) != 4: 
           resp["msg"].append('File "%s" fails validation. Must be 4 columns. Line: %d. Content: %s' % (filename, count, line_str))
           return resp
        #if line[3] not in typecheck: 
        #   typecheck[line[2]] = getfieldtype(line[3])
        #elif getfieldtype(line[3]) != typecheck[line[2]]: 
        #   resp["msg"].append('File "%s" fails validation. Field "%s" has inconsistent type. Expected a "%s" but found a "%s". Line: %d. Content: %s' % (filename, line[2], typecheck[line[2]], getfieldtype(line[3]), count, line))
        # Check if entries for these samples already exist and sample formatting
        #samples = list(set(zip(*inputdata)[0]))
        regex = re.compile('[^0-9a-zA-Z_.]') # this is a list of the valid characters
        #for s in samples:
        if s in validsamples: continue
        if bool(regex.findall(s)): 
            resp["msg"].append('Sample syntax is invalid at sample "%s", only alpha, numeric, underscore, and dot characters are allowed' %s)
        if s[0].isdigit() or s[0] == "_": 
            resp["msg"].append('Sample syntax is invalid at sample "%s", the first character must be a letter or a dot' %s)
        if s[0] == "." and s[1].isdigit(): 
            resp["msg"].append('Sample syntax is invalid at sample "%s", the first character is a dot, so the second must be a letter' %s)
        if Attributes.objects.filter(project = project, sample = s, field=line[3]).exists(): 
            resp["msg"].append('Data exists for field %s for sample %s in project %s (%s). Aborting load...' %(line[3], s, projectID, project.name) )
    if len(resp['msg']) != 0:
        return resp
    else: 
        resp['ok'] = True
        resp['rows'] = count
    fh.seek(0)
    fh.next()
    # Insert Validated Input into the database for the project
    for line in fh:
        data = line.strip().split('\t')
        data[3] = dateparse(data[3])
        if isinstance(data[3], datetime.datetime): data[3] = data[3].strftime('%Y-%m-%d')

        attributes = Attributes(project  = project,
                                sample   = data[0],
                                category = data[1],
                                field    = data[2],
                                value    = data[3],
                               )
        if not AttributeInfo.objects.filter(project=project, name=attributes.field).exists():
            newinfo = AttributeInfo(project   = project,
                                    name      = attributes.field,
                                    fieldtype = getfieldtype(attributes.value),
                                    values    = "",
                                   )
            newinfo.save()
        attributes.save()
    fh.close()
    ok = updateSampleCounts(projectID)
    return resp

def insertMetadataFromTable(filename, projectID):
    resp = {'ok': False, 'msg': [], 'rows': 0}

    # Test File input
    try:
        fh = open(filename, 'U')
    except:
        resp['msg'].append('Error in accessing file "%s"' % (filename))
        return resp

    # Test project ID input
    try:
        project = Project.objects.get(pk=int(projectID))                                           # attempt to find the project for the given ID
    except Project.DoesNotExist:
        resp["msg"].append('Project "%s" does not exist' % projectID)      # report if the project ID does not exist
        return resp

    # Once usable data was input check validity of file contents
    header = fh.next().strip().split('\t') 
    
    ctr = 0
    typecheck = dict()
    regex = re.compile('[^0-9a-zA-Z_.]') # this is a list of the valid characters
    for row in fh:
        ctr+=1
        line = row.strip().split('\t')
        s = line[0]
        if len(line) != len(header):
            resp["msg"].append('Data row "%d" has a length "%d", which does not match the header length "%d"' % ( ctr, len(line), len(header) ))
        if bool(regex.findall(s)):
            resp["msg"].append('Sample syntax is invalid at sample "%s", only alpha, numeric, underscore, and dot characters are allowed' %s)
        if s[0].isdigit() or s[0] == "_":
            resp["msg"].append('Sample syntax is invalid at sample "%s", the first character must be a letter or a dot' %s)
        if s[0] == "." and s[1].isdigit():
            resp["msg"].append('Sample syntax is invalid at sample "%s", the first character is a dot, so the second must be a letter' %s)
        if Attributes.objects.filter(project = project, sample = s, field__in=line[1:]).exists():
            resp["msg"].append('Field data exists for sample %s in project %s (%s). Aborting load...' %(line[3], s, projectID, project.name) )
        for i in range(1, len(line)):
            field = header[i]
            value = line[i]
            if field not in typecheck:
                typecheck[field] = getfieldtype(value)
            elif getfieldtype(value) != typecheck[field]:
                resp["msg"].append('File "%s" fails validation. Field "%s" has inconsistent type. Expected a "%s" but found a "%s". Line: %d. Column %d' % (filename, field, typecheck[field], getfieldtype(value), ctr, i+1))

    if len(resp['msg']) != 0:
        return resp
    else:
        resp['ok'] = True
        resp['rows'] = ctr 
    fh.seek(0)
    fh.next()
    for row in fh:
      line = row.strip().split('\t')
      s = line[0]
      for i in range(1, len(line)):
          field = header[i]
          value = line[i]
          value = dateparse(value)
          if isinstance(value, datetime.datetime): value = value.strftime('%Y-%m-%d')
          attributes = Attributes(project  = project,
                                  sample   = s,
                                  category = 'metadata',
                                  field    = field,
                                  value    = value,
                                 )
          if not AttributeInfo.objects.filter(project=project, name=attributes.field).exists():
              newinfo = AttributeInfo(project   = project,
                                      name      = attributes.field,
                                      fieldtype = getfieldtype(attributes.value),
                                      values    = "",
                                     )
              newinfo.save()
          attributes.save()
    fh.close()
    ok = updateSampleCounts(projectID)
    return resp

def insertAnalysisFromTable(filename,projectID,**kw):
    resp = {'ok': False, 'msg': [], 'rows': 0}

    # Test for needed arguments
    try:
        dataset = kw['dataset']
        method  = kw['method']
        category= kw['category']
    except:
        resp['msg'].append('Missing arguments. The "dataset", "method", and "category" information is required.')
        return resp

    # Test File input
    try:
        fh = open(filename, 'U')
    except:
        resp['msg'].append('Error in accessing file "%s"' % (filename))
        return resp

    # Test project ID input
    try:
        project = Project.objects.get(pk=int(projectID))                                           # attempt to find the project for the given ID
    except Project.DoesNotExist:
        resp["msg"].append('Project "%s" does not exist' % projectID)      # report if the project ID does not exist
        return resp

    header = fh.next().strip().split('\t')
    ctr = 0
    regex = re.compile('[^0-9a-zA-Z_.]') # this is a list of the valid characters
    for row in fh:
        ctr+=1
        line = row.strip().split('\t')
        s = line[0]
        if len(line) != len(header):
            resp["msg"].append('Data row "%d" has a length "%d", which does not match the header length "%d"' % ( ctr, len(line), len(header) ))
        if bool(regex.findall(s)):
            resp["msg"].append('Sample syntax is invalid at sample "%s", only alpha, numeric, underscore, and dot characters are allowed' %s)
        if s[0].isdigit() or s[0] == "_":
            resp["msg"].append('Sample syntax is invalid at sample "%s", the first character must be a letter or a dot' %s)
        if s[0] == "." and s[1].isdigit():
            resp["msg"].append('Sample syntax is invalid at sample "%s", the first character is a dot, so the second must be a letter' %s)
        for i in range(1, len(line)):
            try:
                float(line[i])
            except:
                resp["msg"].append('File "%s" fails validation. Field "%s" contains non-numeric data. Line: %d. Column %d' % (filename, field, ctr, i+1))
    if len(resp['msg']) != 0:
        return resp
    else:
        resp['ok'] = True
        resp['rows'] = ctr
    fh.seek(0)
    fh.next()
    for row in fh:
      line = row.strip().split('\t')
      s = line[0]
      for i in range(1, len(line)):
          entity = header[i]
          value = float(line[i])
          analysis = Analysis(project  = project,
                              sample   = s,
                              dataset  = dataset,
                              method   = method,
                              category = category,
                              entity   = entity,
                              numreads = int(round(value)),
                              profile  = value,
                              avgscore = 1.0,
                             )
          analysis.save()
    ok = updateSampleCounts(projectID)
    return resp

def insertFromBiomFile(filename, projectID, **kw):
    resp = {'ok': False, 'msg': [], 'rows': 0}

    # Test for needed arguments
    try:
        dataset = kw['dataset']
        method  = kw['method']
        category= kw['category']
    except:
        resp['msg'].append('Missing arguments. The "dataset", "method", and "category" information is required.')
        return resp

    # taxa mapping
    taxa_names = {'k': 'kingdom',
                  'p': 'phylum',
                  'c': 'class',
                  'o': 'order',
                  'f': 'family',
                  'g': 'genus',
                  's': 'species',
                  'u': 'unclassified'}

    # regexes for taxonomy information ( if applicable )
    un_taxa = re.compile(r'^\w__$')
    ok_taxa = re.compile(r'^\w__') 

    # Test project ID input
    try:
        project = Project.objects.get(pk=int(projectID))                                           # attempt to find the project for the given ID
    except Project.DoesNotExist:
        resp["msg"].append('Project "%s" does not exist' % projectID)      # report if the project ID does not exist
        return resp

    # read the file
    try:
        table = load_table(filename)
    except:
        resp['msg'].append('Unable to parse the biom file.')
        return resp

    samples = table.ids()
    sample_totals = table.sum(axis='sample')
    observations = table.ids(axis='observation') 
    observation_metadata = table.metadata(axis='observation') 

    for n, row in enumerate(table):
        valid_taxa = True
        measurements, sample_name, sample_metadata = row

        if Analysis.objects.filter(project = project, sample = sample_name, dataset = dataset, method = method, category = category).exists(): 
            continue

        abundance = defaultdict(int)

        if sample_metadata:
            #print "metadata -- "
            for key, value in sample_metadata.items():
                #print sample_name, key, value
                attributes, created = Attributes.objects.get_or_create(project  = project,
                                        sample   = sample_name,
                                        category = 'metadata',
                                        field    = key,
                                        defaults={'value': value},
                                       )
                attributes.value = value
                newinfo, created = AttributeInfo.objects.get_or_create(project   = project,
                                        name      = key,
                                        fieldtype = getfieldtype(value),
                                        values    = "",
                                       )
                newinfo.save()
                attributes.save()
        #print "profile -- "
        for i, value in enumerate(measurements):
            if value == 0: continue
            obs = observations[i]
            try:
                obs_md = observation_metadata[i]
            except:
                obs_md = {}
            if 'taxonomy' in obs_md and valid_taxa:
                for t in obs_md['taxonomy']:
                    if t.lower() != 'unclassified':
                        if not ok_taxa.match(t):
                            valid_taxa = False
                            print i, obs_md['taxonomy'], t
                            abundance = defaultdict(int)
                            break
                        if un_taxa.match(t):
                            t += 'unclassified'
                    else:
                        t = t.lower()
                    abundance[t] += value
            else:
                valid_taxa = False
            #print sample_name, dataset, method, category, obs, value, 100.0*value/sample_totals[n], obs_md
            new_obj, created = Analysis.objects.get_or_create(project = project, sample = sample_name, dataset = dataset, method = method, 
                                                     category = category, entity = obs, taxatree = None, numreads = value, 
                                                     profile = 100.0*value/sample_totals[n], avgscore = 1.0)
        if valid_taxa and abundance:
            #print "taxonomy -- "
            for taxa in sorted(abundance):
                #print sample_name, dataset, method, taxa_names[taxa[0]], taxa, abundance[taxa], 100.0*abundance[taxa]/sample_totals[n]
                new_obj, created = Analysis.objects.get_or_create(project = project, sample = sample_name, dataset = dataset, method = method,
                                                                  category = taxa_names[taxa[0]], entity = taxa, taxatree = None, numreads = abundance[taxa],
                                                                  profile = 100.0*abundance[taxa]/sample_totals[n], avgscore = 1.0)
    if len(resp['msg']) != 0:
        return resp
    else:
        resp['ok'] = True
        resp['rows'] = len(table.ids()) 
    return resp


def insertTimeseriesFromTable(filename, projectID):
    resp = {'ok': False, 'msg': [], 'rows': 0}

    # Test File input
    try:
        fh = open(filename, 'U')
    except:
        resp['msg'].append('Error in accessing file "%s"' % (filename))
        return resp

    # Test project ID input
    try:
        project = Project.objects.get(pk=int(projectID))                                           # attempt to find the project for the given ID
    except Project.DoesNotExist:
        resp["msg"].append('Project "%s" does not exist' % projectID)      # report if the project ID does not exist
        return resp

    # Once usable data was input check validity of file contents
    header = fh.next().strip().split('\t')
    if len(header) != 3:
        resp["msg"].append("Input file must have 3 tab-delimited columns. The provided file has %d" % len(header))

    ctr = 0
    typecheck = dict()
    for row in fh:
        ctr+=1
        line = row.strip().split('\t')
        if len(line) != len(header):
            resp["msg"].append('Data row "%d" has a length "%d", which does not match the header length "%d"' % ( ctr, len(line), len(header) ))
        subject, sample, timepoint = line 
	if not Attributes.objects.filter(sample=sample).exists():
            resp["msg"].append('No existing metadata was found for sample "%s" in the timeseries file. Metadata must be provided before timeseries data' % ( sample ))
        #if not Analysis.objects.filter(sample=sample).exists():
        #    resp["msg"].append('No existing analysis data was found for sample "%s" in the timeseries file. Analysis data must be provided before timeseries data' % ( sample ))
        try:
            timepoint = float(timepoint)
        except:
            resp["msg"].append("Timepoints must be numeric. Therefore the timepoint value '%s' on row '%d' of the file is not valid" % (timepoint, c))
    if len(resp['msg']) != 0:
        return resp
    else:
        resp['ok'] = True
        resp['rows'] = ctr
    fh.seek(0)
    fh.next()

    tssubjectinfoObj, created = AttributeInfo.objects.get_or_create(project   = project,
                                                                    name      = 'tssubject.',
                                                                    fieldtype = 'STRING',
                                                                    values    = "",
                                                                   )
    #tstypeinfoObj, created = AttributeInfo.objects.get_or_create(project   = project,
    #                                                             name      = 'tstype.',
    #                                                             fieldtype = 'STRING',
    #                                                             values    = "",
    #                                                            )
    tstimepointinfoObj, created = AttributeInfo.objects.get_or_create(project   = project,
                                                                      name      = 'tstimepoint.',
                                                                      fieldtype = 'DECIMAL',
                                                                      values    = "",
                                                                     )

    for row in fh:
      line = row.strip().split('\t')
      subject, sample, timepoint = line 
      tssubjectObj = Attributes(project  = project,
                                sample   = sample,
                                category = 'Timeseries Data',
                                field    = 'tssubject.',
                                value    = subject,
                               )
      #tstypeObj = Attributes(project  = project,
      #                       sample   = sample,
      #                       category = 'Timeseries Data',
      #                       field    = 'tstype.',
      #                       value    = tstype,
      #                      )
      tstimepointObj = Attributes(project  = project,
                                  sample   = sample,
                                  category = 'Timeseries Data',
                                  field    = 'tstimepoint.',
                                  value    = timepoint,
                                 )
      tssubjectObj.save()
      #tstypeObj.save()
      tstimepointObj.save()
    fh.close()
    project.timeseries_data = True
    project.save()
    return resp
