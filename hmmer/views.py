from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

#from celery.result import AsyncResult

from general import writeFile, searchTable, csv2list, treeCsv, multiplesCsv, servFile, taskReady, servZip
from models import InputForm, symTyperTask
from tasks import handleForm

import os
import time

# Create your views here.


def errorPage(request):
    # fix me with the correct page to display
    return render_to_response('upload.html', RequestContext(request, {'form': form}))


def inputFormDisplay(request):
    """Displays input form that takes fasta and ids files."""
    if request.method == 'POST':
        form = InputForm(request.POST, request.FILES)
        if form.is_valid():

            # create UID
            sym_task = symTyperTask.objects.create()
            sym_task.UID = str(sym_task.id) + '.' + str(time.time())
            parentDir = os.path.join(settings.SYMTYPER_HOME, sym_task.UID)

            dataDir = os.path.join(parentDir, 'data')
            os.makedirs(dataDir)

            writeFile(request.FILES['fasta_File'],
                      os.path.join(dataDir, "input.fasta"))
            writeFile(request.FILES['sample_File'],
                      os.path.join(dataDir, "samples.ids"))

            task = handleForm.delay(os.path.join("data", "input.fasta"),
                                    os.path.join("data", "samples.ids"),
                                    parentDir)

            sym_task.celeryUID = task.id
            sym_task.save()

            return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))
    else:
        form = InputForm()

    context = {
        'form': form,
    }

    return render_to_response('upload.html', context, context_instance=RequestContext(request))


def clades(request, id):
    """Displays clade results."""
    dirs = all_counts = detailed_counts = all_headers = detailed_headers = None

    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    output = os.path.join(settings.SYMTYPER_HOME, str(id),
                          "data", "hmmer_parsedOutput")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        dirs = [d for d in os.listdir(output)
                if os.path.isdir(os.path.join(output, d))]

        with open(os.path.join(output, "ALL_counts.tsv")) as tsv:
            all_counts = {}
            all = [line.strip().split() for line in tsv]
            all_headers = all[0][1:]

            for row in all[1:]:
                total = hit = no_hit = low = ambiguous = percentages = 0
                site = row[0]
                for column in row[1:]:
                    total += int(column)

                if total != 0:
                    hit = round(float(row[1])/total * 100, 2)
                    no_hit = round(float(row[2])/total * 100, 2)
                    low = round(float(row[3])/total * 100, 2)
                    ambiguous = round(float(row[4])/total * 100, 2)
                percentages = [hit, no_hit, low, ambiguous]
                all_counts[site] = dict(zip(all_headers, percentages))

        with open(os.path.join(output, "DETAILED_counts.tsv")) as tsv:
            detailed_counts = {}

            all = [line.strip().split() for line in tsv]
            detailed_headers = all[0][1:]

            for row in all[1:]:
                data = []
                site = row[0]
                for column in row[1:]:
                    data.append(column)
                detailed_counts[site] = dict(zip(detailed_headers, data))

    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))

    context = {
        'id': id,
        'dirs': dirs,
        'id': id,
        'all_counts': all_counts,
        'detailed_counts': detailed_counts,
        'all_headers': all_headers,
        'detailed_headers': detailed_headers
    }

    return render_to_response('clades.html', context, context_instance=RequestContext(request))


def subtypes(request, id):
    """Displays subtypes results."""
    unique_counts = None

    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    output = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        unique_counts, unique_headers = csv2list(os.path.join(output, "UNIQUE_subtypes_count.tsv"))
        shortnew_counts, shortnew_headers = csv2list(os.path.join(output, "SHORTNEW_subtypes_count.tsv"))
        perfect_counts, perfect_headers = csv2list(os.path.join(output, "PERFECT_subtypes_count.tsv"))
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))
    return render_to_response('subtypes.html', RequestContext(request, {'shortnew_counts': shortnew_counts, 'shortnew_headers': shortnew_headers, 'unique_counts': unique_counts, 'unique_headers': unique_headers, 'perfect_counts': perfect_counts, 'perfect_headers': perfect_headers, 'id': id}))


def multiples(request, id):
    """Displays resolved multiples results."""
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    corrected = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "resolveMultiples","correctedMultiplesHits","corrected")
    resolved = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "resolveMultiples","correctedMultiplesHits","resolved")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        files = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        correctedTable = {}
        resolvedTable = {}

        for f in files:
            if os.path.exists(os.path.join(corrected, f)):
                correctedTable[f] = multiplesCsv(os.path.join(corrected, f))
            else:
                correctedTable[f] = None

            if os.path.exists(os.path.join(resolved, f)):
                resolvedTable[f] = multiplesCsv(os.path.join(resolved, f))
            else:
                resolvedTable[f] = None
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))
    return render_to_response('multiples.html', RequestContext(request,
        {"files":files,"correctedTable":correctedTable,"resolvedTable":resolvedTable, 'id': id}))


def tree(request, id):
    """Displays treenode results."""
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    output = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "placementInfo")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        files = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        tables = {}
        for f in files:
            if os.path.exists(os.path.join(output, f, "treenodeCladeDist.tsv")):
                tables[f] = treeCsv(os.path.join(output, f, "treenodeCladeDist.tsv"))
            else:
                tables[f] = None
        #dirs = [d for d in os.listdir(output) if os.path.isdir(os.path.join(output,d))]
        #A_counts, A_headers = csv2list2(os.path.join(output,"A","treenodeCladeDist.tsv"))
        #B_counts, B_headers = csv2list2(os.path.join(output,"B","treenodeCladeDist.tsv"))
        #C_counts, C_headers = csv2list2(os.path.join(output,"C","treenodeCladeDist.tsv"))
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))
    return render_to_response('tree.html', RequestContext(request, {"files": files, "tables": tables, 'id': id}))


def chart(request, id, site):
    """Displays pie chart"""
    detailed_counts = None
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    output = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "hmmer_parsedOutput")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        detailed_counts = searchTable(os.path.join(output, 'DETAILED_counts.tsv'),site)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))
    return render_to_response('chart.html', RequestContext(request, {'id': id, 'site': site, 'detailed_counts': detailed_counts}))


def status(request, id):
    """Displays main page."""
    done = False

    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    #output = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "hmmer_parsedOutput")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        done = True
    elif redirect:
        return redirect
    else:
        pass
        #message = "pending..."
    return render_to_response('main.html', RequestContext(request, {'done': done, 'id': id}))


def dlAll(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        fPath = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "hmmer_parsedOutput","ALL_counts.tsv")
        fsize = os.stat(fPath).st_size
        filename = "ALL_counts.tsv"
        return servFile(request, ready, filename, fPath, fsize)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))


def dlDetailed(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        fPath = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "hmmer_parsedOutput","DETAILED_counts.tsv")
        fsize = os.stat(fPath).st_size
        filename = "DETAILED_counts.tsv"
        return servFile(request, ready, filename, fPath, fsize)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))


def dlPerfect(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        fPath = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults","PEFECT_subtypes_count.tsv")
        fsize = os.stat(fPath).st_size
        filename = "PERFECT_subtypes_counts.tsv"
        return servFile(request, ready, filename, fPath, fsize)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))


def dlUnique(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        fPath = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults","UNIQUE_subtypes_count.tsv")
        fsize = os.stat(fPath).st_size
        filename = "UNIQUE_subtypes_count.tsv"
        return servFile(request, ready, filename, fPath, fsize)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))


def dlShortnew(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        fPath = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults","SHORTNEW_subtypes_count.tsv")
        fsize = os.stat(fPath).st_size
        filename = "SHORTNEW_subtypes__count.tsv"
        return servFile(request, ready, filename, fPath, fsize)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))


def dlClades(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        path = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "hmmer_parsedOutput")
        return servZip(request, path)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))


def dlSubtypes(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        path = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults")
        return servZip(request, path)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))


def dlMultiples(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        path = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "resolveMultiples", "correctedMultiplesHits")
        return servZip(request, path)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))


def dlTree(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        path = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "placementInfo")
        return servZip(request, path)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))
