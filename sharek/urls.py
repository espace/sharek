from django.conf.urls.defaults import *

#from wkhtmltopdf.views import PDFTemplateView
import core, mobile
from mobile import urls

from core.api import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

entry_resource = TopicsResource()

urlpatterns = patterns('',

    url(r'^logged-in/$', 'core.profiles.views.profile', name='profile'),
	url(r'^sharek/api/', include(entry_resource.urls)),
    url(r'^sharek/rename/$', 'core.entities.article.views.rename_articles', name='rename'),
	
    url(r'sharek/auto_post/$', 'core.facebook.views.auto_post', name='auto_post'),
	
    url(r'^sharek/chaining/', include('smart_selects.urls')),
    
    url(r'^sharek/profile/(?P<browsing_data>[-\w]+)/$', 'core.profiles.views.profile', name='profile'),
    url(r'^sharek/user/(?P<username>\w+[-\.\w]*)/(?P<browsing_data>[-\w]+)/$', 'core.profiles.views.user', name='user_profile'),
    url(r'^sharek/user/(?P<username>\w+[-\.\w]*)/$', 'core.profiles.views.user', name='user'),
	
	#Generate PDF
    url(r'^sharek/pdf/topics/$', 'core.reports.views.topics_pdf', name='topics_pdf'),
	url(r'^sharek/pdf/topic/(?P<topic_slug>[-\w]+)/$', 'core.reports.views.topic_pdf', name='topic_pdf'),
	url(r'^sharek/pdf/comments/(?P<article_slug>[-\w]+)/$', 'core.reports.views.comments_pdf', name='comments_pdf'),
	
    url(r'sharek/latest-comments/$', 'core.entities.feedback.views.latest_comments', name='latest_comments'),
	url(r'sharek/topic_next_articles/$', 'core.entities.topic.views.topic_next_articles', name='topic_next_articles'),
	url(r'sharek/tag_next_articles/$', 'core.entities.tag.views.tag_next_articles', name='tag_next_articles'),
    
    #Facebook
    url(r'sharek/facebook/login', 'core.facebook.views.login', name='facebook_login'),
    url(r'sharek/facebook/logout', 'core.facebook.views.logout', name='facebook_logout'),


    #Reports & Charts
    url(r'sharek/reports/feedback/(?P<article_slug>[-\w]+)/$', 'core.reports.views.export_feedback', name='feedback_report'),
	url(r'sharek/clustering/(?P<article_slug>[-\w]+)/$', 'core.reports.views.feedback_clustering'),
	url(r'sharek/charts/comments/$', 'core.reports.views.comments_chart', name='comments_chart'),
    url(r'sharek/charts/users/$', 'core.reports.views.users_chart', name='users_chart'),
    url(r'sharek/charts/acceptance/$', 'core.reports.views.articles_acceptance', name='acceptance_chart'),
    url(r'sharek/charts/article_history/(?P<header_id>[-\w]+)/(?P<order>[-\w]+)/$', 'core.reports.views.article_history', name='article_history'),
    url(r'sharek/charts/article_history/$', 'core.reports.views.article_history'),

    url(r'^sharek/m/', include(mobile.urls)),
    url(r'^sharek/admin/', include(admin.site.urls)),

    url(r'^sharek/slider/$', 'core.views.slider', name='slider'),
    url(r'^sharek/latest/$', 'core.views.latest', name='latest'),
    url(r'^sharek/search/$', 'core.views.search', name='search'),
    url(r'^sharek/ajx_search/$', 'core.views.ajx_search', name='ajx_search'),

    
    url(r'^sharek/vote/', 'core.entities.feedback.views.vote', name='vote'),
    url(r'^sharek/suggestion_vote/', 'core.entities.article.views.suggestion_vote', name='suggestion_vote'),
    url(r'^sharek/poll_select/', 'core.entities.article.views.poll_select', name='poll_select'),
    url(r'^sharek/modify/', 'core.entities.feedback.views.modify', name='modify'),
    url(r'^sharek/reply_feedback/', 'core.entities.feedback.views.reply_feedback', name='reply_feedback'),
    url(r'^sharek/remove_feedback/', 'core.entities.feedback.views.remove_feedback', name='remove_feedback'),
    url(r'^sharek/facebook/', 'core.views.facebook_comment', name='facebook_comment'),
	url(r'^sharek/logout', 'core.views.logout', name='logout'),
	
    url(r'^sharek/info/(?P<info_slug>[-\w]+)/$', 'core.views.info_detail', name='info'),

    #ArticleDetails detail URL    
    url(r'^sharek/(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/(?P<order_by>[-\w]+)/$', 'core.entities.article.views.article_detail'),
    url(r'^sharek/(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/$', 'core.entities.article.views.article_detail', name='article_detail'),
    url(r'^sharek/(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/comment/(?P<comment_no>[-\w]+)/$', 'core.entities.article.views.article_detail', name='comment_detail'),
	
    #Tag detail URL
    url(r'^sharek/tags/(?P<tag_slug>[-\w]+)/$', 'core.entities.tag.views.tag_detail', name='tag'),
	
    #Topic detail URL    
    url(r'^sharek/topics/$', 'core.entities.topic.views.topic_detail', name='topics'),
    url(r'^sharek/topic/(?P<topic_slug>[-\w]+)/$', 'core.entities.topic.views.topic_detail', name='topic'),
    url(r'^sharek/article_versions/(?P<article_slug>[-\w]+)/$', 'core.entities.article.views.article_diff', name='article_diff'),

	  url(r'^sharek/map/', 'core.views.top_users_map', name='top_users_map'),
	  url(r'^sharek/total_contributions/', 'core.views.total_contribution', name='total_contributions'),
	
    # statistics pages
    url(r'^sharek/top_liked/', 'core.views.top_liked', name='top_liked'),
    url(r'^sharek/top_disliked/', 'core.views.top_disliked', name='top_disliked'),
    url(r'^sharek/top_commented/', 'core.views.top_commented', name='top_commented'),
    url(r'sharek/statistics/$', 'core.views.statistics', name='statistics'),

    url(r'^sharek/$', 'core.views.index', name='index'),
	
    url(r'^sharek/', include('core.social_auth.urls')),
	
    #url(r'$', 'core.views.tmp'),
      
)
