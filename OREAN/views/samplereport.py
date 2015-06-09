from django.shortcuts import render, redirect
from OREAN.decorators import *
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from api.models import * 
from api import internal
import json
from lxml import etree

@login_required
@activeproject
def main(request):
    params = dict()
    params['samples'] = Analysis.objects.filter(project=request.session['projectID']).values_list('sample', flat=True).distinct()
    return render(request, 'sampleReport.html', params)

@login_required
@activeproject
def fetchdata(request):
    resp=dict()
    resp['error'] = False
    resp['msg'] = ""
    
    sample = request.GET.get('sample', None)    
    if not sample: 
        resp['error'] = True
        resp['msg'] = "No sample was included in the request"
    else:
        resp['metadata'] = list(Attributes.objects.filter(project=request.session['projectID'], sample=sample).values('category', 'field', 'value').order_by('category', 'field'))
    return HttpResponse(json.dumps(resp), content_type="application/json")



def buildXML(tree,node, childHash, valueHash):
   nodename=node.split('|')[1]
   newNode = etree.SubElement(tree, "node", name=nodename)
   count = etree.SubElement(newNode, "count")
   countval = etree.SubElement(count, "val").text = str(valueHash[node].numreads)
   score = etree.SubElement(newNode, "score")
   scoreval = etree.SubElement(score, "val").text = str(valueHash[node].avgscore)
   rank = etree.SubElement(newNode, "rank")
   rankval = etree.SubElement(rank, "val").text = str(valueHash[node].category)
   if node in childHash:
     for child in childHash[node]:
       tree = buildXML(newNode, child, childHash, valueHash)
   return tree

@login_required
@activeproject
def krona(request):
   params = dict()
   sample = request.GET.get('sample', None)
   if sample:
       valueHash = dict()
       childHash = dict()
       levelList = []
       array=Analysis.objects.filter(project=request.session['projectID'], sample=sample).order_by('taxatree').select_related()
       root = None
       for row in array:
         if row.taxatree:
           ft = row.taxatree.full_tree
           taxaArray = ft.split('|')
         else:
           taxaArray=["root", row.entity]
           root="1|root"
           childHash[root] = {}
         level = len(taxaArray)
         key="%d|%s" % (level, taxaArray[-1])
         if level >= 2:
           parent = taxaArray[level-2]
           parentkey = "%d|%s" % (level-1,parent)
           if parentkey in childHash: childHash[parentkey][key] = True
           else: childHash[parentkey] = {key: True}
         else:
           root = key
           childHash[key] = {}
         valueHash[key] = row
       krona=etree.Element("krona")
       attributes = etree.SubElement(krona, "attributes", magnitude="count")
       memberselement = etree.SubElement(attributes, "attribute", display="Count").text = "count"
       #unassignedelement = etree.SubElement(attributes, "attribute", display="Unassigned").text = "unassigned"
       memberselement = etree.SubElement(attributes, "attribute", display="Avg. % Confidence").text = "score"
       memberselement = etree.SubElement(attributes, "attribute", display="Rank").text = "rank"
       #datasetsElement = etree.SubElement(krona, 'datasets')
       #dataset = etree.SubElement(datasetsElement, 'dataset').text = "Taxonomy"
       #colorelement = etree.SubElement(krona, "color" ,default="true", valueend="1", valuestart="0", hueend="120", huestart="0", attribute="score")
       xml = buildXML(krona, root, childHash, valueHash)
       params['xml'] = etree.tostring(krona, pretty_print=True)
   return render(request, 'showKrona.html', params)
