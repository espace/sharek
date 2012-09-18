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

from core.facebook.models import FacebookSession

from sharek import settings

from django.core.urlresolvers import reverse

def welcome(request):
    print request.user
    fb_user = FacebookSession.objects.get(user = request.user)
    # GraphAPI is the main class from facebook_sdp.py
    graph = facebook_sdk.GraphAPI(fb_user.access_token)
    attachment = {}
    now = datetime.now()
    message = 'test message at ' + now.strftime("%Y-%m-%d %H:%M")
    caption = 'test caption'
    attachment['caption'] = caption
    attachment['name'] = 'test name'
    attachment['link'] = 'link_to_picture'
    attachment['description'] = 'test description'
    #graph.put_wall_post(message, attachment)
    #return 0

    template_context = {'user':request.user,}
    return render_to_response('facebook/welcome.html', template_context, context_instance=RequestContext(request))

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
                filename = core.__path__[0] + '/static/images/profile_images/'+ user.username
                print filename  # test
                fout = open(filename, "wb")
                fout.write(my_picture)
                fout.close()
                print "done"
                
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