from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    #Facebook
    url(r'facebook/login', 'dostor.facebook.views.login'),
    url(r'facebook/logout', 'dostor.facebook.views.logout'),
    url(r'facebook/welcome/', 'dostor.facebook.views.welcome'),
    
    #Home  Tags List
    url(r'^$', 'dostor.views.index'),
    
    url(r'^admin/', include(admin.site.urls)),
    
    #url(r'^search/(?P<def_query>[-\w]+)/$', 'dostor.views.search'),
    url(r'^search/$', 'dostor.views.search'),
    
    url(r'^vote/', 'dostor.views.vote'),
    url(r'^modify/', 'dostor.views.modify'),
    url(r'^facebook/', 'dostor.views.facebook_comment'),

    url(r'^info/(?P<info_slug>[-\w]+)/$', 'dostor.views.info_detail'),

    #url(r'^(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/(?P<order_by>[-\w]+)/$', 'dostor.views.article_detail'), 

    #Article detail URL
    
    url(r'^(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/(?P<order_by>[-\w]+)/$', 'dostor.views.article_detail'),
    url(r'^(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/$', 'dostor.views.article_detail'),

    #Tag detail URL
    url(r'^tags/(?P<tag_slug>[-\w]+)/$', 'dostor.views.tag_detail'),
    #Topc detail URL
    
    url(r'^topics/$', 'dostor.views.topic_detail'),
    url(r'^topic/(?P<topic_slug>[-\w]+)/$', 'dostor.views.topic_detail'),
	
       
)