from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from datetime import datetime

import cgi
import simplejson
import urllib
from dostor.facebook import facebook_sdk

from dostor.facebook.models import FacebookSession

from dostor_masr import settings

def welcome(request):
    fb_user = FacebookSession.objects.get(user = request.user)
    # GraphAPI is the main class from facebook_sdp.py
    graph = facebook_sdk.GraphAPI(fb_user.access_token)
    attachment = {}
    now = datetime.now()
    message = 'test message at ' + now.strftime("%Y-%m-%d %H:%M")
    caption = 'test caption'
    attachment['caption'] = caption
    attachment['name'] = 'test name'
    #attachment['link'] = 'link_to_picture'
    attachment['description'] = 'test description'
    graph.put_wall_post(message, attachment)
    #return 0

    template_context = {'user':request.user,}
    return render_to_response('facebook/welcome.html', template_context, context_instance=RequestContext(request))

def login(request):
    error = None

    if request.user.is_authenticated():
        return HttpResponseRedirect('/facebook/welcome/')

    if request.GET:
        if 'code' in request.GET:
            args = {
                'client_id': settings.FACEBOOK_APP_ID,
                'redirect_uri': settings.FACEBOOK_REDIRECT_URI,
                'client_secret': settings.FACEBOOK_API_SECRET,
                'code': request.GET['code'],
            }

            url = 'https://graph.facebook.com/oauth/access_token?' + \
                    urllib.urlencode(args)
            response = cgi.parse_qs(urllib.urlopen(url).read())
            access_token = response['access_token'][0]
            expires = response['expires'][0]

            facebook_session = FacebookSession.objects.get_or_create(
                access_token=access_token,
            )[0]

            facebook_session.expires = expires
            facebook_session.save()

            user = auth.authenticate(token=access_token)
            if user:
                if user.is_active:
                    auth.login(request, user)
                    return HttpResponseRedirect('/facebook/welcome/')
                else:
                    error = 'AUTH_DISABLED'
            else:
                error = 'AUTH_FAILED'
        elif 'error_reason' in request.GET:
            error = 'AUTH_DENIED'

    template_context = {'settings': settings, 'error': error}
    return render_to_response('facebook/login.html', template_context, context_instance=RequestContext(request))

def logout(request):
    template_context = {}
    auth.logout(request)
    return render_to_response('facebook/logout.html', template_context, context_instance=RequestContext(request))