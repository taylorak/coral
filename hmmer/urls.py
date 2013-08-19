'''
Created on Jul 8, 2013

@author: taylorak
'''
from django.conf.urls import patterns, url
urlpatterns = patterns('',
    url(r'^$', 'hmmer.views.inputFormDisplay',name="form"),
#    url(r'main$','hmmer.views.tabs',name='tabs'),
    url(r'^error/$', 'hmmer.views.errorPage',name="error"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/$','hmmer.views.status',name="status"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/clades$','hmmer.views.clades',name="clades"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/blast$','hmmer.views.blast',name="blast"),
#    url(r'^status/(?P<id>\d+\.\d+\.\d+)/(?P<site>[A-Za-z]+\d+)/$','hmmer.views.chart',name="chart"),
#    url(r'^status/(?P<id>\d+\.\d+\.\d+)/(?P<filename>[A-Z]+\_[a-z]+\.tsv)/$','hmmer.views.preview',name="preview"),
#    url(r'^status/(?P<id>\d+\.\d+\.\d+)/(?P<filename>[A-Z]+\_[a-z]+\.tsv)/download/$','hmmer.views.download',name="download"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlAll/$','hmmer.views.dlAll',name="dlAll"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlDetailed/$','hmmer.views.dlDetailed',name="dlDetailed"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlPerfect/$','hmmer.views.dlPerfect',name="dlPerfect"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlShortnew/$','hmmer.views.dlShortnew',name="dlShortnew"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlUnique/$','hmmer.views.dlUnique',name="dlUnique"),
)
