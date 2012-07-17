from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    #Facebook
    url(r'facebook/login', 'dostor.facebook.views.login'),
    url(r'facebook/logout', 'dostor.facebook.views.logout'),
    url(r'facebook/welcome/', 'dostor.facebook.views.welcome'),
    
    #Home  Tags index
    url(r'^$', 'dostor.views.index'),
    
    url(r'^admin/', include(admin.site.urls)),

    url(r'^(?P<tag_slug>[-\w]+)/$', 'dostor.views.tag_detail'),


    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    
)