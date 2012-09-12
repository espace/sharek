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


    #Reports
    url(r'sharek/reports/feedback/(?P<article_slug>[-\w]+)/$', 'dostor.reports.views.export_feedback', name='feedback_report'),
    
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
	url(r'^sharek/logout', 'dostor.views.logout', name='logout'),
    url(r'^sharek/info/(?P<info_slug>[-\w]+)/$', 'dostor.views.info_detail', name='info'),

    #Article detail URL    
    url(r'^sharek/(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/(?P<order_by>[-\w]+)/$', 'dostor.views.article_detail'),
    url(r'^sharek/(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/$', 'dostor.views.article_detail', name='article_detail'),

    #Tag detail URL
    url(r'^sharek/tags/(?P<tag_slug>[-\w]+)/$', 'dostor.views.tag_detail', name='tag'),
	
    #Topic detail URL    
    url(r'^sharek/topics/$', 'dostor.views.topic_detail', name='topics'),
    url(r'^sharek/topic/(?P<topic_slug>[-\w]+)/$', 'dostor.views.topic_detail', name='topic'),
	
    
    url(r'^sharek/article_versions/(?P<article_slug>[-\w]+)/$', 'dostor.views.article_diff', name='article_diff'),

	url(r'^sharek/total_contributions/', 'dostor.views.total_contribution', name='total_contributions'),
	
    # statistics pages
    url(r'^sharek/top_liked/', 'dostor.views.top_liked', name='top_liked'),
    url(r'^sharek/top_disliked/', 'dostor.views.top_disliked', name='top_disliked'),
    url(r'^sharek/top_commented/', 'dostor.views.top_commented', name='top_commented'),
    
    url(r'^sharek/$', 'dostor.views.index', name='index'),
	
	url(r'^sharek/', include('social_auth.urls')),
	
    url(r'$', 'dostor.views.tmp'),
      
)