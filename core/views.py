# This Python file uses the following encoding: utf-8
import os, sys

import Image
import logging
import subprocess

from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.utils import simplejson
from datetime import datetime
from django.db import connection
from decimal import Decimal

from diff_match import diff_match_patch
from django.contrib import auth
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from core.facebook.models import FacebookSession
from core.facebook import facebook_sdk
from sharek import settings

from django.db.models import Q, Count

from django.core.urlresolvers import reverse
from django.db.models.aggregates import Max
import cgi
import simplejson
import urllib
import random
import urllib2
import core, re
import os.path
from operator import attrgetter
from django.core.cache import cache
import memcache
from core.social_auth.models import UserSocialAuth
from core.twitter import twitter

from random import randint

#from django.conf import settings
from urllib import urlencode
from urllib2 import urlopen

from operator import itemgetter, attrgetter

from core.models import Info, User, Topic, Tag, ArticleDetails, ArticleHeader, ArticleRating


# get first memcached URI
mc = memcache.Client([settings.MEMCACHED_BACKEND])

def tmp(request):
    return HttpResponseRedirect(reverse('index'))

def index(request):
    user = None

    login(request)
    home = True
    if request.user.is_authenticated():
      user = request.user

    topics_tree = mc.get('topics_tree')
    if not topics_tree:
         topics_tree = Topic.objects.topics_tree()
         mc.set('topics_tree', topics_tree, settings.MEMCACHED_TIMEOUT)

    tags = mc.get('tags')
    if not tags:
         tags = Tag.objects.all()
         mc.set('tags', tags, settings.MEMCACHED_TIMEOUT)

    contributions = mc.get('contributions')
    if not contributions:
         contributions = Topic.total_contributions()
         mc.set('contributions', contributions, 900) # 15 Minutes
    
    top_users = mc.get('top_users')
    if not top_users:
         top_users = User.get_top_users(24)
         mc.set('top_users', top_users, settings.MEMCACHED_TIMEOUT)
    
    top_liked = mc.get('top_liked')
    if not top_liked:
         top_liked = ArticleDetails.objects.get_top_liked(5)
         mc.set('top_liked', top_liked, settings.MEMCACHED_TIMEOUT)

    top_commented = mc.get('top_commented')
    if not top_commented:
         top_commented = ArticleDetails.objects.get_top_commented(5)
         mc.set('top_commented', top_commented, settings.MEMCACHED_TIMEOUT)

    most_updated = mc.get('most_updated')
    if not most_updated:
         most_updated = ArticleDetails.objects.get_most_updated(5)
         mc.set('most_updated', most_updated, settings.MEMCACHED_TIMEOUT)

    template_context = {'settings':settings, 'request':request, 'top_users':top_users, 'home':home,'topics_tree':topics_tree,'settings': settings,'user':user,'contributions':contributions,'top_liked':top_liked, 'top_disliked':top_disliked, 'top_commented':top_commented,'most_updated':most_updated, 'tags':tags}

    return render_to_response('index.html', template_context ,RequestContext(request))
          
def facebook_comment(request):
    return render_to_response('facebook_comment.html', {},RequestContext(request))

def login(request):
    error = None

    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('index'))

    if request.GET:
        if 'code' in request.GET:
            args = {
                'client_id': settings.FACEBOOK_APP_ID,
                'redirect_uri': request.build_absolute_uri(request.path),
                'client_secret': settings.FACEBOOK_API_SECRET,
                'code': request.GET['code'],
            }

            url = 'https://graph.facebook.com/oauth/access_token?' + \
                    urllib.urlencode(args)
            print(args)
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
                    return HttpResponseRedirect(request.path)
                else:
                    error = 'AUTH_DISABLED'
            else:
                error = 'AUTH_FAILED'
        elif 'error_reason' in request.GET:
            error = 'AUTH_DENIED'

def search(request):

    user = None
    search = True
    login(request)

    if request.user.is_authenticated():
      user = request.user
    
    query = request.POST.get("q")
    if query == None:
        if request.GET.get("state"):
            query = request.GET.get("state")
        else:
            return HttpResponseRedirect(reverse('index'))
    if len(query.strip()) == 0:
        return HttpResponseRedirect(reverse('index'))

    arts = ArticleHeader.objects.search_articles('%'+query.strip()+'%')
    voted_articles = ArticleRating.objects.filter(user = user)

    count = len(arts)
    paginator = Paginator(arts, settings.paginator) 
    page = request.GET.get('page')

    try:
        arts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        arts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        arts = paginator.page(paginator.num_pages)

    return render_to_response('search.html',{'voted_articles':voted_articles, 'search':search,'request':request,'user':user,"articles":arts,'settings': settings,"query":query.strip(),"count":count},RequestContext(request))

def latest(request):
    user = None
    search = True

    if request.user.is_authenticated():
      user = request.user

    articles = ArticleDetails.objects.get_most_updated(20)
    return render_to_response('latest.html',{'request':request,'user':user,"articles":articles,'settings': settings},RequestContext(request))

def ajx_search(request):
    if request.method == 'GET':
        page =  request.GET.get("page")
        query = request.GET.get("q")

        articles = ArticleHeader.objects.search_articles('%'+query.strip()+'%')

        paginator = Paginator(articles, settings.paginator)
        try:
            articles = paginator.page(page)
            return render_to_response('include/next_articles.html',{'articles':articles} ,RequestContext(request))
        except PageNotAnInteger:
            return HttpResponse('')
        except EmptyPage:
            return HttpResponse('')

def info_detail(request, info_slug):
    user = None

    login(request)
    if request.user.is_authenticated():
      user = request.user
    
    info = get_object_or_404( Info, slug=info_slug )
    
    template_context = {'request':request, 'info':info,'settings': settings,'user':user,}
    return render_to_response('info.html',template_context ,RequestContext(request))

def slider(request):
    news = ArticleDetails.objects.order_by('?')[:3]
    return render_to_response('slider.html',{'news':news} ,RequestContext(request))

def total_contribution(request):
    feedback = Feedback.objects.all().count()
    feedback_ratings = Rating.objects.all().count()
    article_ratings = ArticleRating.objects.all().count()

    total = feedback + feedback_ratings + article_ratings

    return render_to_response('contribution.html',{'total':total,'feedback':feedback,'feedback_ratings':feedback_ratings,'article_ratings':article_ratings} ,RequestContext(request))

def top_liked(request):

    user = None
    if request.user.is_authenticated():
      user = request.user

    if not request.user.is_staff:
        return HttpResponseRedirect(reverse('index'))
    articles = ArticleDetails.objects.get_top_liked(settings.paginator)
    title = 'الأكثر قبولا'
    return render_to_response('statistics.html', {'type':"likes",'settings': settings,'user':user,'articles': articles, 'title': title} ,RequestContext(request))

def top_disliked(request):

    user = None
    if request.user.is_authenticated():
      user = request.user

    if not request.user.is_staff:
        return HttpResponseRedirect(reverse('index'))
    articles = ArticleDetails.objects.get_top_disliked(settings.paginator)
    title = 'الأكثر رفضا'
    return render_to_response('statistics.html', {'type':"dislikes",'settings': settings,'user':user,'articles': articles, 'title': title} ,RequestContext(request))

def top_commented(request):

    user = None
    if request.user.is_authenticated():
      user = request.user

    if not request.user.is_staff:
        return HttpResponseRedirect(reverse('index'))
    articles = ArticleDetails.objects.get_top_commented(settings.paginator)
    title = 'الأكثر مناقشة'
    return render_to_response('statistics.html', {'type':"comments",'settings': settings,'user':user,'articles': articles, 'title': title} ,RequestContext(request))

def statistics(request):
        if request.method == 'POST':
            page =  request.POST.get("page")
            stat_type = request.POST.get("type")

            if stat_type == "likes":
                articles = ArticleDetails.objects.get_top_liked(1000) #ArticleDetails.objects.filter(current = True).order_by('-likes')
            elif stat_type == "dislikes":
                articles = ArticleDetails.objects.get_top_disliked(1000) #ArticleDetails.objects.filter(current = True).order_by('-dislikes')
            elif stat_type == "comments":
                articles = ArticleDetails.objects.get_top_commented(1000) #ArticleDetails.objects.filter(current = True).annotate(num_feedbacks=Count('feedback')).order_by('-num_feedbacks')
            

            paginator = Paginator(articles, settings.paginator)
            try:
                articles = paginator.page(page)
                return render_to_response('include/next_articles.html',{'articles':articles} ,RequestContext(request))
            except PageNotAnInteger:
                return HttpResponse('')
            except EmptyPage:
                return HttpResponse('')

def logout(request):
    template_context = {}
    auth.logout(request)
    return HttpResponseRedirect(reverse('index'))

def top_users_map(request):
    user = None

    login(request)
    if request.user.is_authenticated():
      user = request.user

    members_map = mc.get('members_map')
    if not members_map:
         generate_members_map(request)
         mc.set('members_map', 'members_map_generated', 604800) # Cached for 7 Days
    
    return render_to_response('map.html', {'request': request, 'user': user,} ,RequestContext(request))

def generate_members_map(request):

    margin = 2
    images = 38 # Images per Row

    width = 23 # Image Width
    height = 23 # Images Height
    size = width, height # Images Size

    new_x = new_y = gen_width = gen_height = 0

    out_image = os.path.dirname(os.path.realpath(__file__)) + "/static/members_map.jpg"
    blank_image = Image.open(os.path.dirname(os.path.realpath(__file__)) + "/static/blank.jpg")

    top_users = User.get_top_users(1500)

    for top_user in top_users:

       gen_width += width + margin

       if gen_width > (images * (width + margin)):
             new_x = 0
             new_y += width + margin
             gen_width = width + margin

       image_file = os.path.dirname(os.path.realpath(__file__)) + "/static/photos/profile/%s" % (top_user.username)

       if os.path.exists(image_file):
            image = Image.open(image_file)
       else:
            image = Image.open(os.path.dirname(os.path.realpath(__file__)) + "/static/images/google_user.gif")

       image.thumbnail(size, Image.ANTIALIAS)

       blank_image.paste(image, (new_x, new_y))
        
       new_x += width + margin

    blank_image.save(out_image)

def shorten_url(long_url):
    username = settings.BITLY_USERNAME 
    password = settings.BITLY_APIKEY
    bitly_url = "http://api.bit.ly/v3/shorten?login={0}&apiKey={1}&longUrl={2}&format=txt"
    req_url = bitly_url.format(username, password, long_url)
    short_url = urlopen(req_url).read()
    return short_url
