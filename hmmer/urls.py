'''
Created on Jul 8, 2013

@author: taylorak
'''
from django.conf.urls import patterns, url
urlpatterns = patterns('',
    url(r'^$', 'hmmer.views.inputFormDisplay', name="form"),
    url(r'^error/$', 'hmmer.views.errorPage', name="error"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/$', 'hmmer.views.status', name="status"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/clades$', 'hmmer.views.clades', name="clades"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/subtypes$', 'hmmer.views.subtypes', name="subtypes"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/resolvedMultiples$', 'hmmer.views.multiples', name="multiples"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/placementTree$', 'hmmer.views.tree', name="tree"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/(?P<site>[A-Za-z]+\d+)/$', 'hmmer.views.chart', name="chart"),

    # url(r'^status/(?P<id>\d+\.\d+\.\d+)/(?P<filename>[A-Z]+\_[a-z]+\.tsv)/download/$','hmmer.views.download',name="download"),
    # clades
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlClades/$', 'hmmer.views.dlClades', name="dlClades"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlAll/$', 'hmmer.views.dlAll', name="dlAll"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlDetailed/$', 'hmmer.views.dlDetailed', name="dlDetailed"),
    # subtypes
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlSubtypes/$', 'hmmer.views.dlSubtypes', name="dlSubtypes"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlPerfect/$', 'hmmer.views.dlPerfect', name="dlPerfect"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlShortnew/$', 'hmmer.views.dlShortnew', name="dlShortnew"),
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlUnique/$', 'hmmer.views.dlUnique', name="dlUnique"),
    # multiples
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlMultiples/$', 'hmmer.views.dlMultiples', name="dlMultiples"),
    ##url(r'^status/(?P<id>\d+\.\d+\.\d+)/(?P<dir>[A-Z])/dlMultiples/$','hmmer.views.dlMultiples',name="dlMultiples"),
    ##url(r'^status/(?P<id>\d+\.\d+\.\d+)/(?P<dir>[A-Z])/dlMultiples/$','hmmer.views.dlMultiples',name="dlMultiples"),
    # tree
    url(r'^status/(?P<id>\d+\.\d+\.\d+)/dlTree/$', 'hmmer.views.dlTree', name="dlTree"),
    ##url(r'^status/(?P<id>\d+\.\d+\.\d+)/(?P<dir>[A-Z])/dlTree/$','hmmer.views.dlTree',name="dlTree"),
)
