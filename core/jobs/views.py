from django.db import models
from django.contrib.auth.models import User

import json, urllib2

from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect

def update_user_info(request):
    users_list = User.objects.filter(gender = 'na')

    for usr in users_list:
        try:
             user_info = json.load(urllib2.urlopen('https://graph.facebook.com/' + usr.username))
             print user_info['gender']
             usr.gender = user_info['gender']
             usr.save()
        except:
             print "error"

    text = len(users_list)

    return render_to_response('jobs/update_user_info.html',{'text':text} ,RequestContext(request))