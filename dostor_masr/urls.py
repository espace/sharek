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
    
    url(r'^modify/', 'dostor.views.modify'),
    #Tag detail URL
    url(r'^(?P<tag_slug>[-\w]+)/$', 'dostor.views.tag_detail'),
    #Article detail URL
    url(r'^(?P<tag_slug>[-\w]+)/(?P<article_slug>[-\w]+)/$', 'dostor.views.article_detail'),
    
)