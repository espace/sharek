from django.conf.urls.defaults import *
from core.social_auth.views import auth, complete, disconnect
#from wkhtmltopdf.views import PDFTemplateView
import core, mobile
from mobile import urls

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^idf/$', 'core.analysis.tfidf.idf', name='idf'),
    url(r'^rename/$', 'core.entities.article.views.rename_articles', name='rename'),
    url(r'^recalculate_last_comment/$', 'core.analysis.tfidf.recalculate_last_comment', name='recalculate_last_comment'),
	
    url(r'auto_post/$', 'core.facebook.views.auto_post', name='auto_post'),
	
    url(r'^chaining/', include('smart_selects.urls')),
    
    url(r'^profile/(?P<browsing_data>[-\w]+)/$', 'core.profiles.views.profile', name='profile'),
    url(r'^user/(?P<username>\w+[-\.\w]*)/(?P<browsing_data>[-\w]+)/$', 'core.profiles.views.user', name='user_profile'),
    url(r'^user/(?P<username>\w+[-\.\w]*)/$', 'core.profiles.views.user', name='user'),
	
	#Generate PDF
    url(r'^pdf/bills/$', 'core.reports.views.topics_pdf', name='topics_pdf'),
	url(r'^pdf/bill/(?P<topic_slug>[-\w]+)/$', 'core.reports.views.topic_pdf', name='topic_pdf'),
	url(r'^pdf/comments/(?P<article_slug>[-\w]+)/$', 'core.reports.views.comments_pdf', name='comments_pdf'),
	
    url(r'latest-comments/$', 'core.entities.feedback.views.latest_comments', name='latest_comments'),
	url(r'bill_next_items/$', 'core.entities.topic.views.topic_next_articles', name='topic_next_articles'),
	url(r'tag_next_items/$', 'core.entities.tag.views.tag_next_articles', name='tag_next_articles'),
    
    #Facebook
    url(r'facebook/login', 'core.facebook.views.login', name='facebook_login'),
    url(r'facebook/logout', 'core.facebook.views.logout', name='facebook_logout'),


    #Reports & Charts
    url(r'reports/feedback/(?P<article_slug>[-\w]+)/$', 'core.reports.views.export_feedback', name='feedback_report'),
	url(r'clustering/(?P<article_slug>[-\w]+)/$', 'core.reports.views.feedback_clustering'),
	url(r'charts/comments/$', 'core.reports.views.comments_chart', name='comments_chart'),
    url(r'charts/users/$', 'core.reports.views.users_chart', name='users_chart'),
    url(r'charts/acceptance/$', 'core.reports.views.articles_acceptance', name='acceptance_chart'),
    url(r'charts/item_history/(?P<header_id>[-\w]+)/(?P<order>[-\w]+)/$', 'core.reports.views.article_history', name='article_history'),
    url(r'charts/item_history/$', 'core.reports.views.article_history'),

    url(r'^m/', include(mobile.urls)),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^slider/$', 'core.views.slider', name='slider'),
    url(r'^latest/$', 'core.views.latest', name='latest'),
    url(r'^search/$', 'core.views.search', name='search'),
    url(r'^ajx_search/$', 'core.views.ajx_search', name='ajx_search'),

    
    url(r'^vote/', 'core.entities.feedback.views.vote', name='vote'),
    url(r'^suggestion_vote/', 'core.entities.article.views.suggestion_vote', name='suggestion_vote'),
    url(r'^poll_select/', 'core.entities.article.views.poll_select', name='poll_select'),
    url(r'^modify/', 'core.entities.feedback.views.modify', name='modify'),
    url(r'^reply_feedback/', 'core.entities.feedback.views.reply_feedback', name='reply_feedback'),
    url(r'^remove_feedback/', 'core.entities.feedback.views.remove_feedback', name='remove_feedback'),
    url(r'^facebook/', 'core.views.facebook_comment', name='facebook_comment'),
	url(r'^logout', 'core.views.logout', name='logout'),
	
    url(r'^info/(?P<info_slug>[-\w]+)/$', 'core.views.info_detail', name='info'),

    #ArticleDetails detail URL    
    url(r'^(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/summarize/$', 'core.entities.article.views.article_summarization', name='article_summerization'),
    url(r'^(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/(?P<order_by>[-\w]+)/$', 'core.entities.article.views.article_detail', name='article_detail_ordered'),
    url(r'^(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/$', 'core.entities.article.views.article_detail', name='article_detail'),
    url(r'^(?P<classified_by>[-\w]+)/(?P<class_slug>[-\w]+)/(?P<article_slug>[-\w]+)/comment/(?P<comment_no>[-\w]+)/$', 'core.entities.article.views.article_detail', name='comment_detail'),
    
    #Tag detail URL
    url(r'^tags/(?P<tag_slug>[-\w]+)/$', 'core.entities.tag.views.tag_detail', name='tag'),
	
    #Topic detail URL    
    url(r'^bills/$', 'core.entities.topic.views.topic_detail', name='topics'),
    url(r'^bill/(?P<topic_slug>[-\w]+)/$', 'core.entities.topic.views.topic_detail', name='topic'),
    url(r'^history/(?P<article_slug>[-\w]+)/$', 'core.entities.article.views.article_diff', name='article_diff'),

	url(r'^map/', 'core.views.top_users_map', name='top_users_map'),
	url(r'^total_contributions/', 'core.views.total_contribution', name='total_contributions'),
	
    # statistics pages
    url(r'^top_liked/', 'core.views.top_liked', name='top_liked'),
    url(r'^top_disliked/', 'core.views.top_disliked', name='top_disliked'),
    url(r'^top_commented/', 'core.views.top_commented', name='top_commented'),
    url(r'^statistics/$', 'core.views.statistics', name='statistics'),

    url(r'^$', 'core.views.index', name='index'),
    url(r'^about_us$', 'core.views.about_us', name='about_us'),
    url(r'^contact_us$', 'core.views.contact_us', name='contact_us'),
	
    url(r'^', include('core.social_auth.urls')),
    url(r'^login/', auth, name='login'), # by Amr to overwrite a url rule in social_auth
    
    url(r'$', 'core.views.tmp'),
      
)
