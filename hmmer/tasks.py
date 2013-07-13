'''
Created on Jul 5, 2013

@author: taylorak
'''
from celery.task import task
import os

@task(ignore_results=True)
def handleForm(fasta, sample, parentDir):
    os.chdir(parentDir)
    os.system("""cat %s > output.fasta""" %(fasta))
