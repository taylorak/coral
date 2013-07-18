# Create your views here.
#from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from celery.result import AsyncResult
from models import InputForm,symTyperTask 
from tasks import handleForm
from django.conf import settings
import os
import time
import csv

###
def writeFile(origin,destination):
    with open(destination,'w') as dest:
        for chunk in origin.chunks():
            dest.write(chunk)

def searchTable(tablePath,site):
    with open(tablePath,'rb') as tsv:
        reader = csv.reader(tsv)

        headers = reader.next()
        keys = [header.split('_')[0] for header in headers[0].split()[1:]]

        for row in reader:
            row2 = row[0].split()
            if  row2[0] == str(site):
                values = row2[1:]
                return dict(zip(keys, values))
    return False
###

def InputFormDisplay(request):
    if request.method == 'POST':
        form = InputForm(request.POST, request.FILES)
        if form.is_valid():
            
            # create UID
            sym_task = symTyperTask.objects.create()
            sym_task.UID =  str(sym_task.id) + '.' + str(time.time()) 
            parentDir = os.path.join(settings.SYMTYPER_HOME,sym_task.UID)
            #os.makedirs(parentDir)

            dataDir = os.path.join(parentDir,'data')
            os.makedirs(dataDir)

            writeFile(request.FILES['fasta_File'],os.path.join(dataDir,"input.fasta"))
            writeFile(request.FILES['sample_File'],os.path.join(dataDir,"input.ids"))

# change later
#            with open(os.path.join(dataDir,"input.fasta"),'w') as dest:
#                for chunk in request.FILES['fasta_File'].chunks():
#                    dest.write(chunk)
 
#            with open(os.path.join(dataDir,"input.ids"),'w') as dest:
#                for chunk in request.FILES['sample_File'].chunks():
#                    dest.write(chunk)
                     

            task = handleForm.delay("data/input.fasta","data/input.ids",parentDir)

            sym_task.celeryUID = task.id
            sym_task.save()

            return HttpResponseRedirect(os.path.join("/hmmer/status/",sym_task.UID))
    else:
        form = InputForm()
    return render_to_response('upload.html',RequestContext(request, {'form':form}))

def status(request, id):
    sym_task = symTyperTask.objects.get(UID = id)
    result = AsyncResult(sym_task.celeryUID)
    dirs = headers = False
    if result.ready():
        if result.successful():
            message = "success!"
            dirs = os.walk(os.path.join(settings.SYMTYPER_HOME,str(id) + "/data/hmmer_parsedOutput/")).next()[1]
        else:
            message = "failure!"
    else:
        message = "pending..."
    return render_to_response('status.html',RequestContext(request, {'message':message,'dirs':dirs,'id':id}))
        
def chart(request,id,site):
    path = os.path.join(settings.SYMTYPER_HOME,str(id) + "/data/hmmer_parsedOutput/")
    dictionary = searchTable(os.path.join(path,'ALL_counts.tsv'),site)

# fix this
#    dictionary = False
#    with open(os.path.join(path,'ALL_counts.tsv'),'rb') as tsv:
#        reader = csv.reader(tsv)
#
#        headers = reader.next()
#        keys = [header.split('_')[0] for header in headers[0].split()[1:]]
#
#        for row in reader:
#            row2 = row[0].split()
#            if  row2[0] == str(site):
#                values = row2[1:]
#                dictionary = dict(zip(keys, values))

    return render_to_response('chart.html',RequestContext(request, {'dictionary':dictionary}))


