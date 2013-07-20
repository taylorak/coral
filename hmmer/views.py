# Create your views here.
#from django.contrib.auth.decorators import login_required
from django.template import RequestContext 
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render_to_response
from celery.result import AsyncResult
from models import InputForm,symTyperTask 
from tasks import handleForm
from django.conf import settings
from django.utils.encoding import smart_str
import os
import time
import csv
import urllib

### MOVE LATER
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

def listTable(tablePath):
    table = []
    with open(tablePath,'rb') as tsv:
        reader = csv.reader(tsv)
    
        for row in reader:         
            row2 = row[0].split()
            table.append(table)
    return table

def servFile(request, ready, filename, fPath, fsize):
    response = HttpResponse(mimetype='application/force-download')
    if(not Status.SUCCESS):
        return response
    #response['Content-Type'] = contentType
    response['Content-Disposition'] = 'attachment; filename=%s' %(smart_str( filename  ) ) 
    response['X-Sendfile'] = urllib.quote(fPath)
    response['Content-Transfer-Encoding'] = "binary"
    response['Expires'] = 0
    response['Accept-Ranges'] = 'bytes'
    response['Cache-Control'] = "private"
    response['Pragma'] = 'private'
    httprange = request.META.get("HTTP_RANGE", None)
    if(httprange):
        rng = httprange.split("=")
        cnt = rng[-1].split("-")
        response['Content-Length'] = fsize - int(cnt[0])
        response['Content-Range'] = str(httprange) + str(response['Content-Length']) + "/" + str(fsize)
    else:
        response['Content-Length'] = fsize
    with open(fPath) as outfile:
        buf = outfile.read(4096)
        while len(buf) == 4096:
            response.write(buf)
            buf = outfile.read(4096)
        if(len(buf) != 0):
            response.write(buf) 
    return response


class Status:
    SUCCESS = 1
    FAILURE = 2 
    PENDING = 3

def taskReady(task):
    if task.ready():
        if task.successful():
            return Status.SUCCESS
        else:
            return Status.FAILURE
    else:
        return Status.PENDING


###

def inputFormDisplay(request):
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

            task = handleForm.delay("data/input.fasta","data/input.ids",parentDir)

            sym_task.celeryUID = task.id
            sym_task.save()

            return HttpResponseRedirect(os.path.join("/hmmer/status/",sym_task.UID))
    else:
        form = InputForm()
    return render_to_response('upload.html',RequestContext(request, {'form':form}))

def status(request, id):
    sym_task = symTyperTask.objects.get(UID = id)
    task = AsyncResult(sym_task.celeryUID)

    dirs = headers = False
    downloads = ['ALL_counts.tsv','DETAILED_counts.tsv']
    
    ready = taskReady(task)
    if ready == Status.SUCCESS:
        message = "success!"
        dirs = os.walk(os.path.join(settings.SYMTYPER_HOME,str(id) + "/data/hmmer_parsedOutput/")).next()[1]
    elif ready == Status.FAILURE:
        message = "failure!"
    else:
        message = "pending..."

    return render_to_response('status.html',RequestContext(request, {'message':message,'dirs':dirs,'downloads':downloads,'id':id}))

"""
    if result.ready():
        if result.successful():
            message = "success!"
            dirs = os.walk(os.path.join(settings.SYMTYPER_HOME,str(id) + "/data/hmmer_parsedOutput/")).next()[1]
        else:
            message = "failure!"
    else:
        message = "pending..."
"""
        
def chart(request,id,site):
    path = os.path.join(settings.SYMTYPER_HOME,str(id) + "/data/hmmer_parsedOutput/")
    ALL_dict = searchTable(os.path.join(path,'ALL_counts.tsv'),site)
    DETAILED_dict = searchTable(os.path.join(path,'DETAILED_counts.tsv'),site)
    return render_to_response('chart.html',RequestContext(request, {'ALL_dict':ALL_dict,'DETAILED_dict':DETAILED_dict}))

def download(request, id, filename):
    sym_task = symTyperTask.objects.get(UID=id)
    task = AsyncResult(sym_task.celeryUID)
    ready = taskReady(task)

    fPath = os.path.join(settings.SYMTYPER_HOME,str(id) + "/data/hmmer_parsedOutput/" + str(filename))
    fsize = os.stat(fPath).st_size
    return servFile(request, ready, filename, fPath, fsize)


