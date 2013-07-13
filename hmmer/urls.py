'''
Created on Jul 8, 2013

@author: taylorak
'''
from django.conf.urls import patterns, url
urlpatterns = patterns('',
    url(r'^$', 'hmmer.views.InputFormDisplay'),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/$','hmmer.views.status'),
)
