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


def inputFormDisplay(request, template='upload.html'):
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

            return HttpResponseRedirect(reverse("index", args=[sym_task.UID]))
    else:
        form = InputForm()

    context = {
        'form': form,
    }

    return render_to_response(template, context, RequestContext(request))


def clades(request, id, template='clades.html'):
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
        #dirs = [d for d in os.listdir(output)
                #if os.path.isdir(os.path.join(output, d))]

        with open(os.path.join(output, "ALL_counts.tsv")) as tsv:
            all_counts = []
            all = [line.strip().split() for line in tsv]
            all_headers = all[0]

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
                percentages = [site, hit, no_hit, low, ambiguous]
                all_counts.append(dict(zip(all_headers, percentages)))

        with open(os.path.join(output, "DETAILED_counts.tsv")) as tsv:
            detailed_counts = []

            all = [line.strip().split() for line in tsv]
            detailed_headers = all[0][1:]

            for row in all[1:]:
                data = []
                site = row[0]
                for column in row[1:]:
                    data.append(column)
                detailed_counts.append(dict(zip(detailed_headers, data)))

    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("index", args=[sym_task.UID]))

    context = {
        'id': id,
        'title': "Clades",
        'dirs': dirs,
        'all_headers': all_headers,
        'all_counts': all_counts,
        'detailed_counts': detailed_counts,
        'detailed_headers': detailed_headers,
    }

    return render_to_response(template, context, RequestContext(request))


##
# Subtypes
##

def unique(request, id, template='subtypes.html'):
    """Displays subtypes results."""

    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    output = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        counts, headers = csv2list(os.path.join(output, "UNIQUE_subtypes_count.tsv"))
        #shortnew_counts, shortnew_headers = csv2list(os.path.join(output, "SHORTNEW_subtypes_count.tsv"))
        #perfect_counts, perfect_headers = csv2list(os.path.join(output, "PERFECT_subtypes_count.tsv"))
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("index", args=[sym_task.UID]))

    context = {
        #'shortnew_counts': shortnew_counts,
        #'shortnew_headers': shortnew_headers,
        #'unique_counts': unique_counts,
        #'unique_headers': unique_headers,
        #'perfect_counts': perfect_counts,
        #'perfect_headers': perfect_headers,
        'counts': counts,
        'headers': headers,
        'title': "Unique Subtypes",
        'id': id,
    }

    return render_to_response(template, context, RequestContext(request))


def shortnew(request, id, template='subtypes.html'):
    """Displays subtypes results."""

    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    output = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        counts, headers = csv2list(os.path.join(output, "SHORTNEW_subtypes_count.tsv"))
        #perfect_counts, perfect_headers = csv2list(os.path.join(output, "PERFECT_subtypes_count.tsv"))
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("index", args=[sym_task.UID]))

    context = {
        'title': "Short New Subtypes",
        'counts': counts,
        'headers': headers,
        'id': id,
    }

    return render_to_response(template, context, RequestContext(request))


def perfect(request, id, template='subtypes.html'):
    """Displays subtypes results."""

    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    output = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "blastResults")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        counts, headers = csv2list(os.path.join(output, "PERFECT_subtypes_count.tsv"))
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("index", args=[sym_task.UID]))

    context = {
        'title': "Perfect Subtypes",
        'counts': counts,
        'headers': headers,
        'id': id,
    }

    return render_to_response(template, context, RequestContext(request))


def multiplesCorrected(request, id, file):
    """Displays resolved multiples results."""

    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    corrected = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "resolveMultiples", "correctedMultiplesHits", "corrected")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        corrected_counts, corrected_headers, corrected_breakdown, corrected_subtypes = multiplesCsv(os.path.join(corrected, file))
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))

    context = {
        'counts': corrected_counts,
        'headers': corrected_headers,
        'breakdown': corrected_breakdown,
        'subtypes': corrected_subtypes,
        'id': id,
        'file': file,
    }

    return render_to_response('multiples.html', context, RequestContext(request))


def multiplesResolved(request, id, file):
    """Displays resolved multiples results."""

    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    resolved = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "resolveMultiples", "correctedMultiplesHits", "resolved")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        resolved_counts, resolved_headers, resolved_breakdown, resolved_subtypes = multiplesCsv(os.path.join(resolved, file))
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))

    context = {
        'file': file,
        'counts': resolved_counts,
        'headers': resolved_headers,
        'breakdown': resolved_breakdown,
        'subtypes': resolved_subtypes,
        'id': id,
    }

    return render_to_response('multiples.html', context, RequestContext(request))


def tree(request, id, file, template='tree.html'):
    """Displays treenode results."""
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    output = os.path.join(settings.SYMTYPER_HOME, str(id), "data", "placementInfo")
    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
            counts, headers = treeCsv(os.path.join(output, file, "treenodeCladeDist.tsv"))
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))

    context = {
        'counts': counts,
        'headers': headers,
        'id': id,
        'file': file,
    }

    return render_to_response(template, context, RequestContext(request))


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


def index(request, id):
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
    return render_to_response('index.html', RequestContext(request, {'done': done, 'id': id}))


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

def dlEverything(request, id):
    try:
        sym_task = symTyperTask.objects.get(UID=id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse("form"))

    ready, redirect = taskReady(sym_task.celeryUID)
    if ready:
        path = os.path.join(settings.SYMTYPER_HOME, str(id), "data")
        return servZip(request, path)
    elif redirect:
        return redirect
    else:
        return HttpResponseRedirect(reverse("status", args=[sym_task.UID]))


