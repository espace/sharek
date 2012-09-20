from django.contrib import auth
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from datetime import datetime

import cgi
import json
import simplejson
import urllib
import urllib2
import core
import os.path
from core.facebook import facebook_sdk

from core.models import ArticleDetails

from core.facebook.models import FacebookSession
from django.core.urlresolvers import reverse
from sharek import settings

def login(request):
    error = None

    if request.user.is_authenticated():
        return HttpResponse("<script type='text/javascript'> window.close(); window.opener.refreshPage(); </script>");

    if request.GET:

       if 'cancel' in request.GET:
            return HttpResponse("<script type='text/javascript'> window.close(); </script>");

       if 'auth_token' in request.GET:
            return render_to_response('facebook/relogin.html', {'settings': settings}, context_instance=RequestContext(request))

       if 'session' in request.GET:

            user_obj = json.loads(request.GET['session'])

            facebook_session = FacebookSession.objects.get_or_create(
                access_token = user_obj['access_token'],
            )[0]

            facebook_session.expires = user_obj['expires']
            facebook_session.save()

            user = auth.authenticate(token=user_obj['access_token'])
            if user and user.is_active and request.GET['loginsucc']:
                auth.login(request, user)
                # copy the profile image
                picture_page = "https://graph.facebook.com/"+user.username+"/picture?type=square"
                
                opener1 = urllib2.build_opener()
                page1 = opener1.open(picture_page)
                my_picture = page1.read()
                filename = core.__path__[0] + '/static/photos/profile/'+ user.username
                fout = open(filename, "wb")
                fout.write(my_picture)
                fout.close()
                
                #return HttpResponseRedirect(request.path)
                return HttpResponse("<script type='text/javascript'> window.close(); window.opener.refreshPage(); </script>");
            else:
                error = True

    template_context = {'settings': settings, 'error': error}
    return render_to_response('facebook/login.html', template_context, context_instance=RequestContext(request))

def logout(request):
    template_context = {}
    auth.logout(request)
    return HttpResponseRedirect(reverse('index'))

def auto_post(request):

    # GraphAPI is the main class from facebook_sdp.py
    graph = facebook_sdk.GraphAPI(settings.FACEBOOK_PAGE_TOKEN)

    articles = ArticleDetails.objects.order_by('?')[:1]

    for article in articles:

        message = article.header.topic.name.encode('utf-8') + " - " + article.header.name.encode('utf-8') + "&rlm; \n" + article.summary.raw

        attachment = {}
        attachment['name'] = article.header.topic.name.encode('utf-8') + " - " + article.header.name.encode('utf-8') + "&rlm;"
        #attachment['link'] = article.get_absolute_url
        attachment['link'] = settings.domain + "sharek/" + article.header.topic.slug + "/" + article.slug + "/"
        attachment['description'] = article.summary
        attachment['picture'] = "http://dostour.eg/sharek/static/images/facebook.png"

        graph.put_wall_post(message, attachment, '246121898775580')

    return HttpResponse(message)