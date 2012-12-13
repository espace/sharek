from django.conf.urls import patterns, include, url
import mobile

urlpatterns = patterns('',
	
    url(r'^topics/$', 'mobile.views.topics', name='topics_mobile'),
    url(r'topic/(?P<topic_slug>[-\w]+)/$', 'mobile.views.articles', name='articles_mobile'),
    
	url(r'$', 'mobile.views.index', name='index_mobile'),
	
)