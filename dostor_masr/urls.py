from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    #Facebook
    url(r'sharik/facebook/login', 'dostor.facebook.views.login', name='facebook_login'),
    url(r'sharik/facebook/logout', 'dostor.facebook.views.logout', name='facebook_logout'),
    url(r'sharik/facebook/welcome/', 'dostor.facebook.views.welcome', name='facebook_welcome'),
    
    #Home  Tags List
    url(r'^sharik/$', 'dostor.views.index', name='index'),
    
    url(r'^sharik/admin/', include(admin.site.urls)),
    
    url(r'^sharik/slider/$', 'dostor.views.slider', name='slider'),
    url(r'^sharik/search/$', 'dostor.views.search', name='search'),
    
    url(r'^sharik/vote/', 'dostor.views.vote', name='vote'),
    url(r'^sharik/modify/', 'dostor.views.modify', name='modify'),
    url(r'^sharik/facebook/', 'dostor.views.facebook_comment', name='facebook_comment'),

    url(r'^sharik/info/(?P<info_slug>[-\w]+)/$', 'dostor.views.info_detail', name='info'),

    #Article detail URL
    
    url(r'^sharik/(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/(?P<order_by>[-\w]+)/$', 'dostor.views.article_detail'),
    url(r'^sharik/(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/$', 'dostor.views.article_detail', name='article_detail'),

    #Tag detail URL
    url(r'^sharik/tags/(?P<tag_slug>[-\w]+)/$', 'dostor.views.tag_detail', name='tag'),
    #Topc detail URL
    
    url(r'^sharik/topics/$', 'dostor.views.topic_detail', name='topics'),
    url(r'^sharik/topic/(?P<topic_slug>[-\w]+)/$', 'dostor.views.topic_detail', name='topic'),
	
       
)