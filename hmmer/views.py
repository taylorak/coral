# Create your views here.
#from django.contrib.auth.decorators import login_required
#from django.shortcuts import render_to_response,get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from celery.result import AsyncResult
from models import InputForm,symTyperTask 
from tasks import handleForm
from django.conf import settings
import os
import time


def InputFormDisplay(request):
    if request.method == 'POST':
        form = InputForm(request.POST, request.FILES)
        if form.is_valid():

            sym_task = symTyperTask.objects.create()
            sym_task.UID =  str(sym_task.id) + '.' + str(time.time())

            parentDir = os.path.join(settings.SYMTYPER_HOME,sym_task.UID)
            os.makedirs(parentDir)

            with open(os.path.join(parentDir,"input.fasta"),'w') as dest:
                for chunk in request.FILES['fasta_File'].chunks():
                    dest.write(chunk)
 
            with open(os.path.join(parentDir,"input.id"),'w') as dest:
                for chunk in request.FILES['sample_File'].chunks():
                    dest.write(chunk)
                     

            task = handleForm.delay("input.fasta","input.id",parentDir)

            sym_task.celeryUID = task.id
            sym_task.save()

            return HttpResponseRedirect(os.path.join("/hmmer/status/",sym_task.UID))
    else:
        form = InputForm()
    return render_to_response('upload.html',RequestContext(request, {'form':form}))

def status(request, id):
    sym_task = symTyperTask.objects.get(UID = id)
    result = AsyncResult(sym_task.celeryUID)
    dirs = False
    if result.ready():
        if result.successful():
            message = "success!"
            dirs = os.walk(os.path.join(settings.SYMTYPER_HOME,str(id) + "/data/hmmer_parsedOutput/")).next()[1]
        else:
            message = "failure!"
    else:
        message = "pending..."
    return render_to_response('status.html',RequestContext(request, {'message':message}))
        
def chart(request,id,site):
    return render_to_response('chart.html',RequestContext(request, {'message':message}))


