from django.conf.urls import patterns, include, url
from wkhtmltopdf.views import PDFTemplateView
import core

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'sharek/auto_post/$', 'core.facebook.views.auto_post', name='auto_post'),
	
	url(r'sharek/index/$', PDFTemplateView.as_view(template_name='reports/template.html',filename=core.__path__[0] + '/static/new_pdf.pdf'), name='pdf'),
	
    url(r'sharek/latest-comments/$', 'core.views.latest_comments', name='latest_comments'),
	url(r'sharek/topic_next_articles/$', 'core.views.topic_next_articles', name='topic_next_articles'),
	url(r'sharek/tag_next_articles/$', 'core.views.tag_next_articles', name='tag_next_articles'),
    
    #Facebook
    url(r'sharek/facebook/login', 'core.facebook.views.login', name='facebook_login'),
    url(r'sharek/facebook/logout', 'core.facebook.views.logout', name='facebook_logout'),


    #Reports
    url(r'sharek/reports/feedback/(?P<article_slug>[-\w]+)/$', 'core.reports.views.export_feedback', name='feedback_report'),
     
    url(r'^sharek/admin/', include(admin.site.urls)),

    url(r'^sharek/slider/$', 'core.views.slider', name='slider'),
    url(r'^sharek/search/$', 'core.views.search', name='search'),
    
    url(r'^sharek/vote/', 'core.views.vote', name='vote'),
    url(r'^sharek/article_vote/', 'core.views.article_vote', name='article_vote'),
    url(r'^sharek/modify/', 'core.views.modify', name='modify'),
    url(r'^sharek/reply_feedback/', 'core.views.reply_feedback', name='reply_feedback'),
    url(r'^sharek/remove_feedback/', 'core.views.remove_feedback', name='remove_feedback'),
    url(r'^sharek/facebook/', 'core.views.facebook_comment', name='facebook_comment'),
	url(r'^sharek/logout', 'core.views.logout', name='logout'),
	
    url(r'^sharek/info/(?P<info_slug>[-\w]+)/$', 'core.views.info_detail', name='info'),

    #ArticleDetails detail URL    
    url(r'^sharek/(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/(?P<order_by>[-\w]+)/$', 'core.views.article_detail'),
    url(r'^sharek/(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/$', 'core.views.article_detail', name='article_detail'),

    #Tag detail URL
    url(r'^sharek/tags/(?P<tag_slug>[-\w]+)/$', 'core.views.tag_detail', name='tag'),
	
    #Topic detail URL    
    url(r'^sharek/topics/$', 'core.views.topic_detail', name='topics'),
    url(r'^sharek/topic/(?P<topic_slug>[-\w]+)/$', 'core.views.topic_detail', name='topic'),
    
    url(r'^sharek/article_versions/(?P<article_slug>[-\w]+)/$', 'core.views.article_diff', name='article_diff'),

	url(r'^sharek/map/', 'core.views.top_users_map', name='top_users_map'),
	url(r'^sharek/total_contributions/', 'core.views.total_contribution', name='total_contributions'),
	
    # statistics pages
    url(r'^sharek/top_liked/', 'core.views.top_liked', name='top_liked'),
    url(r'^sharek/top_disliked/', 'core.views.top_disliked', name='top_disliked'),
    url(r'^sharek/top_commented/', 'core.views.top_commented', name='top_commented'),
    url(r'sharek/statistics/$', 'core.views.statistics', name='statistics'),
    
    url(r'^sharek/$', 'core.views.index', name='index'),
	
	url(r'^sharek/', include('social_auth.urls')),
	
    url(r'$', 'core.views.tmp'),
      
)