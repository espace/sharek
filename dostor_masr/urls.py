from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    
	
    url(r'sharek/latest-comments/$', 'dostor.views.latest_comments', name='latest_comments'),


    #Facebook
    url(r'sharek/facebook/login', 'dostor.facebook.views.login', name='facebook_login'),
    url(r'sharek/facebook/logout', 'dostor.facebook.views.logout', name='facebook_logout'),
    url(r'sharek/facebook/welcome/', 'dostor.facebook.views.welcome', name='facebook_welcome'),
    
    #Home  Tags List
    
    url(r'^sharek/admin/', include(admin.site.urls)),
    
    url(r'^sharek/slider/$', 'dostor.views.slider', name='slider'),
    url(r'^sharek/search/$', 'dostor.views.search', name='search'),
    
    url(r'^sharek/vote/', 'dostor.views.vote', name='vote'),
    url(r'^sharek/article_vote/', 'dostor.views.article_vote', name='article_vote'),
    url(r'^sharek/modify/', 'dostor.views.modify', name='modify'),
    url(r'^sharek/reply_feedback/', 'dostor.views.reply_feedback', name='reply_feedback'),
    url(r'^sharek/remove_feedback/', 'dostor.views.remove_feedback', name='remove_feedback'),
    url(r'^sharek/facebook/', 'dostor.views.facebook_comment', name='facebook_comment'),

    url(r'^sharek/info/(?P<info_slug>[-\w]+)/$', 'dostor.views.info_detail', name='info'),

    #Article detail URL    
    url(r'^sharek/(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/(?P<order_by>[-\w]+)/$', 'dostor.views.article_detail'),
    url(r'^sharek/(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/$', 'dostor.views.article_detail', name='article_detail'),

    #Tag detail URL
    url(r'^sharek/tags/(?P<tag_slug>[-\w]+)/$', 'dostor.views.tag_detail', name='tag'),
	
    #Topic detail URL    
    url(r'^sharek/topics/$', 'dostor.views.topic_detail', name='topics'),
    url(r'^sharek/topic/(?P<topic_slug>[-\w]+)/$', 'dostor.views.topic_detail', name='topic'),
	
	url(r'^sharek/total_contributions/', 'dostor.views.total_contribution', name='total_contributions'),
	
    url(r'^sharek/$', 'dostor.views.index', name='index'),
	
    url(r'$', 'dostor.views.tmp'),
      
)