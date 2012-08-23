# This Python file uses the following encoding: utf-8
import os, sys

from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.utils import simplejson
from datetime import datetime

from django.contrib import auth

from dostor.models import Tag, Article, Feedback, Rating, Topic, Info, ArticleRating

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from dostor.facebook.models import FacebookSession
from dostor.facebook import facebook_sdk
from dostor_masr import settings

from django.db.models import Q

from django.core.urlresolvers import reverse

import cgi
import simplejson
import urllib


def index(request):
    user = None

    login(request)
    home = True
    if request.user.is_authenticated():
      user = request.user
    tags = Tag.objects.all
    target = 150
    feedback_count = len(Feedback.objects.all())
    percent = int((float(feedback_count)/target)*100)
    template_context = {'request':request, 'home':home,'tags':tags,'target':target,'settings': settings,'user':user,'count':feedback_count,'percent':percent}
    return render_to_response('index.html', template_context ,RequestContext(request))
        
def tag_detail(request, tag_slug):
    user = None

    login(request)
    if request.user.is_authenticated():
      user = request.user
    tags = Tag.objects.all
    tag = get_object_or_404( Tag, slug=tag_slug )
    articles = tag.article_set.all()

    voted_articles = ArticleRating.objects.filter(user = user)

    paginator = Paginator(articles, settings.paginator) 
    page = request.GET.get('page')


    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        articles = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        articles = paginator.page(paginator.num_pages)

    template_context = {'voted_articles':voted_articles,'request':request, 'tags':tags,'tag':tag,'articles': articles,'settings': settings,'user':user,}
    return render_to_response('tag.html',template_context ,RequestContext(request))

def topic_detail(request, topic_slug=None):
    user = None

    login(request)
    if request.user.is_authenticated():
      user = request.user
    if topic_slug:
        topics = Topic.objects.all
        topic = get_object_or_404( Topic, slug=topic_slug )
        articles = topic.article_set.all()
    else:
        topics = Topic.objects.filter()
        if len(topics) > 0:
            topic = topics[0]
            articles = topic.article_set.all()
        else:
            topic = None
            articles = None

    paginator = Paginator(articles, settings.paginator) 
    page = request.GET.get('page')


    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        articles = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        articles = paginator.page(paginator.num_pages)

    template_context = {'request':request, 'topics':topics,'topic':topic,'articles': articles,'settings': settings,'user':user,}
    return render_to_response('topic.html',template_context ,RequestContext(request))

def article_detail(request, classified_by, class_slug, article_slug, order_by="def"):
    user = None

    login(request)

    if request.user.is_authenticated():
      user = request.user

    if classified_by == "tags":  
        tags = Tag.objects.all
        tag = get_object_or_404( Tag, slug=class_slug )
    elif classified_by == "topics":
        topics = Topic.objects.all
        topic = get_object_or_404( Topic, slug=class_slug )
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')

    article = get_object_or_404( Article, slug=article_slug )
    related_tags = article.tags.all
    top_ranked = None
    size = len(Feedback.objects.filter(article_id = article.id).order_by('-id'))
    top_ranked = Feedback.objects.filter(article_id = article.id).order_by('-order')[:3]
    if order_by == "latest":
        if size >= 3:
            feedbacks = Feedback.objects.filter(article_id = article.id).order_by('-id').exclude(id=top_ranked[0].id).exclude(id=top_ranked[1].id).exclude(id=top_ranked[2].id)
        else:
            feedbacks = Feedback.objects.filter(article_id = article.id).order_by('-id')
    elif order_by == "order":
        if size >= 3:
            feedbacks = Feedback.objects.filter(article_id = article.id).order_by('-order').exclude(id=top_ranked[0].id).exclude(id=top_ranked[1].id).exclude(id=top_ranked[2].id)
        else:
            feedbacks = Feedback.objects.filter(article_id = article.id).order_by('-order')
    elif order_by == "def":
        if size >= 3:
            feedbacks = Feedback.objects.filter(article_id = article.id).order_by('-id').exclude(id=top_ranked[0].id).exclude(id=top_ranked[1].id).exclude(id=top_ranked[2].id)
        else:
            feedbacks = Feedback.objects.filter(article_id = article.id).order_by('-id')
    
    

    paginator = Paginator(feedbacks, settings.paginator) 
    page = request.GET.get('page')

    voted_fb = Rating.objects.filter(article_id = article.id, user = user)
    voted_article = ArticleRating.objects.filter(article_id = article.id, user = user)

    article_rate = None
    for art in voted_article:
        if art.vote == True:
            article_rate = 1
        else:
            article_rate = -1

    try:
        feedbacks = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        feedbacks = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        feedbacks = paginator.page(paginator.num_pages)
    
    votes = article.get_votes()
    p_votes = {}
    n_votes = {}
    for vote in votes:
      if vote.vote == True:
        if p_votes.__contains__(vote.feedback_id):
          p_votes[vote.feedback_id] += 1
        else:
          p_votes[vote.feedback_id] = 1
      else:
        if n_votes.__contains__(vote.feedback_id):
          n_votes[vote.feedback_id] += 1
        else:
          n_votes[vote.feedback_id] = 1
          
    if classified_by == "tags":  
        template_context = {'article_rate':article_rate,'order_by':order_by,'voted_fb':voted_fb,'top_ranked':top_ranked,'request':request, 'related_tags':related_tags,'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'p_votes': p_votes,'n_votes': n_votes,'tags':tags,'tag':tag}
    elif classified_by == "topics":
        template_context = {'article_rate':article_rate,'order_by':order_by,'voted_fb':voted_fb,'top_ranked':top_ranked,'request':request, 'related_tags':related_tags,'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'p_votes': p_votes,'n_votes': n_votes,'topics':topics,'topic':topic}      
    
    return render_to_response('article.html',template_context ,RequestContext(request))

def remove_feedback(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            feedback_id = request.POST.get("feedback")
            feedback = Feedback.objects.get(id=feedback_id)
            #the user has to be the feedback owner to be able to remove it
            if feedback.user == request.user.username or request.user.username == "admin":
                feedback.delete()
                return HttpResponse(simplejson.dumps({'feedback_id':request.POST.get("feedback")}))

def modify(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            Feedback(user = request.POST.get("user_id"),article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.user.email, name = request.user.first_name + " " + request.user.last_name).save()
            feedback = Feedback.objects.filter(article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.user.email, name = request.user.first_name + " " + request.user.last_name)

            fb_user = FacebookSession.objects.get(user = request.user)
            # GraphAPI is the main class from facebook_sdp.py
            graph = facebook_sdk.GraphAPI(fb_user.access_token)
            attachment = {}
            attachment['link'] = settings.domain+"sharek/"+request.POST.get("class_slug")+"/"+request.POST.get("article_slug")
            attachment['picture'] = settings.domain+settings.STATIC_URL+"images/facebook.png"
            message = 'لقد شاركت في كتابة دستور مصر وقمت بالتعليق على '+get_object_or_404(Article, id=request.POST.get("article")).name.encode('utf-8')+" من الدستور"
            graph.put_wall_post(message, attachment)

            return HttpResponse(simplejson.dumps({'date':str(feedback[0].date),'id':feedback[0].id ,'suggestion':request.POST.get("suggestion")}))

def vote(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            feedback =  request.POST.get("modification")
            user =  request.user

            record = Rating.objects.filter(feedback_id = feedback, user = user )

            vote = False
            if request.POST.get("type") == "1" :
              vote = True
            
            if record:
                record[0].vote = vote
                record[0].save()
            else:
                Rating(user = user, vote = vote, feedback_id = feedback,article_id = request.POST.get("article")).save()
            
            mod = Feedback.objects.get(id=feedback)

            votes = Rating.objects.filter(feedback_id = feedback)
            p = 0
            n = 0
            for v in votes:
              if v.vote == True:
                p += 1
              else:
                n += 1

            mod.order = p - n
            mod.save()
            return HttpResponse(simplejson.dumps({'modification':request.POST.get("modification"),'p':p,'n':n,'vote':request.POST.get("type")}))

def article_vote(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            article =  request.POST.get("article")
            user =  request.user

            record = ArticleRating.objects.filter(article_id = article, user = user )

            vote = False
            if request.POST.get("type") == "1" :
              vote = True
            
            if record:
                record[0].vote = vote
                record[0].save()
            else:
                ArticleRating(user = user, vote = vote,article_id = article).save()
            
            votes = ArticleRating.objects.filter(article_id = article)
            p = 0
            n = 0
            for v in votes:
              if v.vote == True:
                p += 1
              else:
                n += 1

            art = Article.objects.get(id = article)
            art.likes = p
            art.dislikes = n
            art.save()

            fb_user = FacebookSession.objects.get(user = request.user)
            graph = facebook_sdk.GraphAPI(fb_user.access_token)
            attachment = {}
            attachment['link'] = settings.domain+"sharek/topics/"+art.topic.slug+"/"+art.slug
            attachment['picture'] = settings.domain+settings.STATIC_URL+"images/facebook.png"
            message = 'لقد شاركت في كتابة دستور مصر وقمت بالتصويت على ' + art.name.encode('utf-8') + " من الدستور"
            graph.put_wall_post(message, attachment)

            return HttpResponse(simplejson.dumps({'article':article,'p':p,'n':n,'vote':request.POST.get("type")}))
          
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
    
    '''if def_query == None:
        query = request.POST.get("q")        
    else:'''
    query = request.POST.get("q")
    if query == None:
        if request.GET.get("state"):
            query = request.GET.get("state")
        else:
            return HttpResponseRedirect(reverse('index'))
    if len(query.strip()) == 0:
        return HttpResponseRedirect(reverse('index'))

    articles = Article.objects.filter(Q(summary__contains=query.strip()) | Q(name__contains=query.strip()))
    count = len(articles)
    paginator = Paginator(articles, settings.paginator) 
    page = request.GET.get('page')

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        articles = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        articles = paginator.page(paginator.num_pages)

    return render_to_response('search.html',{'search':search,'request':request,'user':user,"articles":articles,'settings': settings,"query":query.strip(),"count":count},RequestContext(request))

def info_detail(request, info_slug):
    user = None

    login(request)
    if request.user.is_authenticated():
      user = request.user
    
    info = get_object_or_404( Info, slug=info_slug )
    
    template_context = {'request':request, 'info':info,'settings': settings,'user':user,}
    return render_to_response('info.html',template_context ,RequestContext(request))

def slider(request):
    news = Article.objects.order_by('?')[:5]
    return render_to_response('slider.html',{'news':news} ,RequestContext(request))