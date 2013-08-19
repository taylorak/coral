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
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt


### MOVE LATER
def writeFile(origin,destination):
    with open(destination,'w') as dest:
        for chunk in origin.chunks():
            dest.write(chunk)

"""
def searchTable(tablePath,site):
    site = str(site)
    with open(tablePath) as reader:
        try:
            headers = reader.next()
            keys = [header.split('_')[0] for header in headers.split()[1:]]
            for row in reader:
                row2 = row.split()
                if row2[0] == site:
                    return dict(zip(keys, row2[1:]))
        except:
            pass
    return {}

def listTable(tablePath):
    with open(tablePath) as tsv:
        return [i.strip().split() for i in tsv]
"""

def csv2list(csvPath):
    try:
        with open(csvPath) as tsv:
            counts = []
            all = [line.strip().split() for line in tsv]
            headers = all[0]

            if len(headers) > 1:
                for row in all[1:]:
                    counts.append(dict(zip(headers, row)))
                return counts,headers
    except:
        pass
    return None,None

def servFile(request, ready, filename, fPath, fsize):
    response = HttpResponse(mimetype='application/force-download')
    #if(not Status.SUCCESS):
    #    return response
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


#class Status:
#    SUCCESS = 1
#    FAILURE = 2 
#    PENDING = 3

def taskReady(celeryID, redirect = "error"):
    task = AsyncResult(celeryID)

    if task.ready():
        if task.successful():
            return True, None
        else:
            return False, HttpResponseRedirect(reverse(redirect))
    else:
        return False, None


###

def errorPage(request):
    # fix me with the correct page to display
    return render_to_response('upload.html',RequestContext(request, {'form':form}))


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

            task = handleForm.delay(os.path.join("data","input.fasta"),os.path.join("data","input.ids"),parentDir)

            sym_task.celeryUID = task.id
            sym_task.save()

            return HttpResponseRedirect(reverse("status",args=[sym_task.UID]))
    else:
        form = InputForm()
    return render_to_response('upload.html',RequestContext(request, {'form':form}))

@csrf_exempt
def clades(request,id):
    dirs = all_counts = detailed_counts = all_headers = detailed_headers = None
    try: 
        sym_task = symTyperTask.objects.get(UID = id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    output = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "hmmer_parsedOutput")
    ready,redirect = taskReady(sym_task.celeryUID)
    if ready == True:
        dirs = [d for d in os.listdir(output) if os.path.isdir(os.path.join(output,d))]

        with open(os.path.join(output,"ALL_counts.tsv")) as tsv:
            all_counts = {}
            all = [line.strip().split() for line in tsv]
            all_headers = all[0][1:]

            for row in all[1:]:
                total = hit = no_hit = low = ambiguous = percentages = 0
                site = row[0]
                for column in row[1:]:
                    total += int(column)

                if total != 0:
                    hit = round(float(row[1])/total * 100,2)
                    no_hit = round(float(row[2])/total * 100,2)
                    low = round(float(row[3])/total * 100,2)
                    ambiguous = round(float(row[4])/total * 100,2)
                percentages = [hit,no_hit,low,ambiguous]
                all_counts[site] = dict(zip(all_headers,percentages))


        with open(os.path.join(output,"DETAILED_counts.tsv")) as tsv:
            detailed_counts = {}

            all = [line.strip().split() for line in tsv]
            detailed_headers = all[0][1:]

            for row in all[1:]:
                data = []
                site = row[0]
                for column in row[1:]:
                    data.append(column)
                detailed_counts[site] = dict(zip(detailed_headers, data))


#        ALL_dict = searchTable(os.path.join(path,'ALL_counts.tsv'),site)
#        DETAILED_dict = searchTable(os.path.join(path,'DETAILED_counts.tsv'),site)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status",args=[sym_task.UID]))
    return render_to_response('clades.html',RequestContext(request, {'dirs':dirs,'id':id,'all_counts':all_counts,'detailed_counts':detailed_counts,'all_headers':all_headers,'detailed_headers':detailed_headers}))

@csrf_exempt
def blast(request,id):
    #downloads = ['ALL_counts.tsv','DETAILED_counts.tsv']
    downloads = {}
    unique_counts = None
    try: 
        sym_task = symTyperTask.objects.get(UID = id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    output = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults")
    ready,redirect = taskReady(sym_task.celeryUID)
    if ready == True:
        downloads = {}
        """
        try:
            with open(os.path.join(output,"UNIQUE_subtypes_count.tsv")) as tsv:
                unique_counts = []
                all = [line.strip().split() for line in tsv]
                unique_headers = all[0]

                if len(unique_headers) > 1:
                    for row in all[1:]:
                        unique_counts.append(dict(zip(unique_headers, row)))
        except:
            pass
        """
        downloads["UNIQUE_subtypes_count.tsv"] = csv2list(os.path.join(output,"UNIQUE_subtypes_count.tsv"))
        downloads["SHORTNEW_subtypes_count.tsv"] = csv2list(os.path.join(output,"SHORTNEW_subtypes_count.tsv"))
        downloads["PERFECT_subtypes_count.tsv"] = csv2list(os.path.join(output,"PERFECT_subtypes_count.tsv"))
        unique_counts,unique_headers = csv2list(os.path.join(output,"UNIQUE_subtypes_count.tsv"))
        shortnew_counts,shortnew_headers = csv2list(os.path.join(output,"SHORTNEW_subtypes_count.tsv"))
        perfect_counts, perfect_headers = csv2list(os.path.join(output,"PERFECT_subtypes_count.tsv"))
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status",args=[sym_task.UID]))
    return render_to_response('blast.html',RequestContext(request, {'shortnew_counts':shortnew_counts,'shortnew_headers':shortnew_headers, 'unique_counts':unique_counts, 'unique_headers':unique_headers,'perfect_counts':perfect_counts,'perfect_headers':perfect_headers,'downloads':downloads,'id':id}))

def status(request,id):
    #    dirs = ALLtable = DETAILEDtable = headers = message = None
    dirs = None
    downloads = ['ALL_counts.tsv','DETAILED_counts.tsv']

    output = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "hmmer_parsedOutput")
    try: 
        sym_task = symTyperTask.objects.get(UID = id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready,redirect = taskReady(sym_task.celeryUID)
    if ready == True:
        dirs = [d for d in os.listdir(output) if os.path.isdir(os.path.join(output,d))]
#        ALLtable = listTable(os.path.join(output,"ALL_counts.tsv"))        
#        DETAILEDtable = listTable(os.path.join(output,"DETAILED_counts.tsv"))
    elif redirect:
        return redirect
    else:
        message = "pending..."

    return render_to_response('main.html',RequestContext(request,{'dirs': dirs,'id':id}))
#    return render_to_response('tabs.html',RequestContext(request,{'dirs': dirs,'id':id}))
#    return render_to_response('status.html',RequestContext(request, {'message':message,'dirs':dirs,'downloads':downloads,'id':id,'ALLtable':ALLtable,'DETAILEDtable':DETAILEDtable}))

def dlAll(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready,redirect = taskReady(sym_task.celeryUID)
    if ready == True:
        fPath = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "hmmer_parsedOutput","ALL_counts.tsv")
        fsize = os.stat(fPath).st_size
        filename = "ALL_counts.tsv"
        return servFile(request, ready, filename, fPath, fsize)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status",args=[sym_task.UID]))

def dlDetailed(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready,redirect = taskReady(sym_task.celeryUID)
    if ready == True:
        fPath = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "hmmer_parsedOutput","DETAILED_counts.tsv")
        fsize = os.stat(fPath).st_size
        filename = "DETAILED_counts.tsv"
        return servFile(request, ready, filename, fPath, fsize)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status",args=[sym_task.UID]))


def dlPerfect(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready,redirect = taskReady(sym_task.celeryUID)
    if ready == True:
        fPath = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults","PEFECT_subtypes_count.tsv")
        fsize = os.stat(fPath).st_size
        filename = "PERFECT_subtypes_counts.tsv"
        return servFile(request, ready, filename, fPath, fsize)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status",args=[sym_task.UID]))


def dlUnique(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready,redirect = taskReady(sym_task.celeryUID)
    if ready == True:
        fPath = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults","UNIQUE_subtypes_count.tsv")
        fsize = os.stat(fPath).st_size
        filename = "UNIQUE_subtypes_count.tsv"
        return servFile(request, ready, filename, fPath, fsize)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status",args=[sym_task.UID]))


def dlShortnew(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready,redirect = taskReady(sym_task.celeryUID)
    if ready == True:
        fPath = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults","SHORTNEW_subtypes_count.tsv")
        fsize = os.stat(fPath).st_size
        filename = "SHORTNEW_subtypes__count.tsv"
        return servFile(request, ready, filename, fPath, fsize)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status",args=[sym_task.UID]))



"""
def chart(request,id,site):
    path = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "hmmer_parsedOutput")
    try:
        sym_task = symTyperTask.objects.get(UID = id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready,redirect = taskReady(sym_task.celeryUID)

    if ready == True:
        ALL_dict = searchTable(os.path.join(path,'ALL_counts.tsv'),site)
        DETAILED_dict = searchTable(os.path.join(path,'DETAILED_counts.tsv'),site)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status",args=[sym_task.UID]))
    return render_to_response('chart.html',RequestContext(request, {'ALL_dict':ALL_dict,'DETAILED_dict':DETAILED_dict}))

def preview(request, id, filename):
    try:
        sym_task = symTyperTask.objects.get(UID = id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready,redirect = taskReady(sym_task.celeryUID)
    if ready == True:
        table = listTable(os.path.join(settings.SYMTYPER_HOME, str(id), "data", "hmmer_parsedOutput",str(filename)))         
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status",args=[sym_task.UID]))
    return render_to_response('preview.html',RequestContext(request, {'table':table}))
"""

