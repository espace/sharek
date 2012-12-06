from django.conf.urls import patterns, include, url
import mobile

urlpatterns = patterns('',
	
    url(r'^topic/(?P<topic_slug>[-\w]+)/$', 'mobile.views.topic', name='topic_mobile'),
    url(r'article/(?P<article_slug>[-\w]+)/$', 'mobile.views.article', name='article_mobile'),
    
	url(r'$', 'mobile.views.index'),
	
)