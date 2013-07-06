'''
Created on Jul 5, 2013

@author: taylorak
'''
from celery import task

@task()
def hmmer(x, y):
    return x + y