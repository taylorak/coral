'''
Created on Jul 5, 2013

@author: taylorak
'''
from celery.task import task
import os
#from subprocess import call

@task(ignore_results=True)
def handleForm(fasta, sample, parentDir):
    os.chdir(parentDir)
    os.system("""python /home/taylor/symTyper/symTyper.py --threads 12 clade --i %s -s %s""" %(fasta,sample))
    os.system("""python /home/taylor/symTyper/symTyper.py  -t 3 subtype -H data/hmmer_hits/ -s %s -b data/blast_output/ -r data/blastResults/ -f data/fasta"""%(sample))

