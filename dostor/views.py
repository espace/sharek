# This Python file uses the following encoding: utf-8
import os, sys

from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.utils import simplejson
from datetime import datetime
from django.db import connection


from django.contrib import auth

from dostor.models import Tag, Article, Feedback, Rating, Topic, Info, ArticleRating, User

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from dostor.facebook.models import FacebookSession
from dostor.facebook import facebook_sdk
from dostor_masr import settings

from django.db.models import Q, Count

from django.core.urlresolvers import reverse
from django.db.models.aggregates import Max
import cgi
import simplejson
import urllib

def tmp(request):
    return HttpResponseRedirect(reverse('index'))

def index(request):
    user = None

    login(request)
    home = True
    if request.user.is_authenticated():
      user = request.user
    topics = Topic.objects.all

    top_users = []
    temp_users = Feedback.objects.values('user').annotate(user_count=Count('user')).order_by('-user_count')[:18]
    for temp_user in temp_users:
        top_users.append(get_object_or_404( User, username=temp_user['user'] ))
	
    print top_users

    target = 500000
	
    feedback = Feedback.objects.all().count()
    feedback_ratings = Rating.objects.all().count()
    article_ratings = ArticleRating.objects.all().count()

    total = feedback + feedback_ratings + article_ratings
	
    top_liked = Article.get_top_liked(2)
    top_disliked = Article.get_top_disliked(2)
    top_commented = Article.get_top_commented(2)
    tags = Tag.objects.all
    
    percent = int((float(total)/target)*100)
    percent_draw = (float(total)/target)*10

    template_context = {'request':request, 'top_users':top_users, 'home':home,'topics':topics,'target':target,'settings': settings,'user':user,'total':total,'percent_draw':percent_draw, 'percent':percent, 'top_liked':top_liked, 'top_disliked':top_disliked, 'top_commented':top_commented, 'tags':tags}

    return render_to_response('index.html', template_context ,RequestContext(request))
        
def tag_detail(request, tag_slug):
    user = None

    login(request)
    if request.user.is_authenticated():
      user = request.user
    tags = Tag.objects.all
    tag = get_object_or_404( Tag, slug=tag_slug )
    #articles = tag.article_set.all()
    arts = tag.article_set.all().values('original').annotate(max_id=Max('id')).order_by()
    articles = []
    for art in arts:
        print art
        articles.append(get_object_or_404( Article, id=art['max_id'] ))
    articles = sorted(articles, key=lambda article: article.order)
    
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
        arts = topic.article_set.all().values('original').annotate(max_id=Max('id')).order_by()
        print arts.query
        articles = []
        for art in arts:
            print art
            articles.append(get_object_or_404( Article, id= art['max_id'] ))
            print get_object_or_404( Article, id= art['max_id'] ).order
        articles = sorted(articles, key=lambda article: article.order)
    else:
        topics = Topic.objects.filter()
        if len(topics) > 0:
            topic = topics[0]
            arts = topic.article_set.all().values('original').annotate(max_id=Max('id')).order_by()
            articles = []
            for art in arts:
                print art
                articles.append(get_object_or_404( Article, id=art['max_id'] ))
            articles = sorted(articles, key=lambda article: article.order)
        else:
            topic = None
            articles = None

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

    template_context = {'request':request, 'topics':topics,'topic':topic,'articles': articles,'settings': settings,'user':user,'voted_articles':voted_articles}
    return render_to_response('topic.html',template_context ,RequestContext(request))

def article_diff(request, article_slug):
    
    user = None
    login(request)

    if request.user.is_authenticated():
      user = request.user

    article = get_object_or_404( Article, slug=article_slug )
    versions = Article.objects.filter(original = article.original.id).order_by('id')

    template_context = {'article': article,'versions': versions, 'request':request}
    return render_to_response('article_diff.html',template_context ,RequestContext(request))


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

    versions = []
    arts = Article.objects.filter(original = article.original).order_by('-id')

    related_tags = article.tags.all

    top_ranked = None
    size = len(Feedback.objects.filter(article_id = article.id, parent_id = None).order_by('-id'))
    if size > 3:
        top_ranked = Feedback.objects.filter(article_id = article.id, parent_id = None).order_by('-order')[:3]
    else:
        top_ranked = None

    if order_by == "latest":
        if size > 3:
            feedbacks = Feedback.objects.filter(article_id = article.id, parent_id = None).order_by('-id').exclude(id=top_ranked[0].id).exclude(id=top_ranked[1].id).exclude(id=top_ranked[2].id)
        else:
            feedbacks = Feedback.objects.filter(article_id = article.id, parent_id = None).order_by('-id')
    elif order_by == "order":
        if size > 3:
            feedbacks = Feedback.objects.filter(article_id = article.id, parent_id = None).order_by('-order').exclude(id=top_ranked[0].id).exclude(id=top_ranked[1].id).exclude(id=top_ranked[2].id)
        else:
            feedbacks = Feedback.objects.filter(article_id = article.id, parent_id = None).order_by('-order')
    elif order_by == "def":
        if size > 3:
            feedbacks = Feedback.objects.filter(article_id = article.id, parent_id = None).order_by('-id').exclude(id=top_ranked[0].id).exclude(id=top_ranked[1].id).exclude(id=top_ranked[2].id)
        else:
            feedbacks = Feedback.objects.filter(article_id = article.id, parent_id = None).order_by('-id')
    
    

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
        template_context = {'arts':arts,'article_rate':article_rate,'order_by':order_by,'voted_fb':voted_fb,'top_ranked':top_ranked,'request':request, 'related_tags':related_tags,'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'p_votes': p_votes,'n_votes': n_votes,'tags':tags,'tag':tag}
    elif classified_by == "topics":
        template_context = {'arts':arts,'article_rate':article_rate,'order_by':order_by,'voted_fb':voted_fb,'top_ranked':top_ranked,'request':request, 'related_tags':related_tags,'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'p_votes': p_votes,'n_votes': n_votes,'topics':topics,'topic':topic}      
    
    return render_to_response('article.html',template_context ,RequestContext(request))


def remove_feedback(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            feedback_id = request.POST.get("feedback")
            feedback = Feedback.objects.get(id=feedback_id)
            replys = Feedback.objects.filter(parent_id = request.POST.get("feedback"))
            reply_ids = []
            for reply in replys:
                reply_ids.append(reply.id)
            #the user has to be the feedback owner to be able to remove it
            if feedback.user == request.user.username or request.user.username == "admin":
                feedback.delete()
                return HttpResponse(simplejson.dumps({'feedback_id':request.POST.get("feedback"),'reply_ids':reply_ids}))

def modify(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            sug = str(request.POST.get("suggestion").encode('utf-8'))
            feedbacks = Feedback.objects.filter(article_id = request.POST.get("article"), email= request.POST.get("email"), name = request.POST.get("name"))
            for feedback in feedbacks:
                if feedback.suggestion.raw.encode('utf-8') in sug:
                    return HttpResponse(simplejson.dumps({'duplicate':True,'name':request.POST.get("name")}))
            else:
                Feedback(user = request.POST.get("user_id"),article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email = request.POST.get("email"), name = request.POST.get("name")).save()
                feedback = Feedback.objects.filter(article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.POST.get("email"), name = request.POST.get("name"))
            
            fb_user = FacebookSession.objects.get(user = request.user)
            # GraphAPI is the main class from facebook_sdp.py
            graph = facebook_sdk.GraphAPI(fb_user.access_token)
            attachment = {}
            attachment['link'] = settings.domain+"sharek/"+request.POST.get("class_slug")+"/"+request.POST.get("article_slug")
            attachment['picture'] = settings.domain+settings.STATIC_URL+"images/facebook.png"
            message = 'لقد شاركت في كتابة #دستور_مصر وقمت بالتعليق على '+get_object_or_404(Article, id=request.POST.get("article")).name.encode('utf-8')+" من الدستور"
            graph.put_wall_post(message, attachment)
            
            return HttpResponse(simplejson.dumps({'date':str(feedback[0].date),'id':feedback[0].id ,'suggestion':request.POST.get("suggestion")}))

def reply_feedback(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            sug = str(request.POST.get("suggestion").encode('utf-8'))
            feedbacks = Feedback.objects.filter(article_id = request.POST.get("article"), email= request.POST.get("email"), name = request.POST.get("name"))
            for feedback in feedbacks:
                if feedback.suggestion.raw.encode('utf-8') in sug:
                    return HttpResponse(simplejson.dumps({'duplicate':True,'name':request.POST.get("name")}))
            Feedback(user = request.POST.get("user_id"),article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email = request.POST.get("email"), name = request.POST.get("name"), parent_id = request.POST.get("parent")).save()
            reply = Feedback.objects.filter(user = request.POST.get("user_id"),article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.POST.get("email"), name = request.POST.get("name"), parent_id= request.POST.get("parent"))
            return HttpResponse(simplejson.dumps({'date':str(reply[0].date),'id':reply[0].id ,'suggestion':request.POST.get("suggestion"),'parent':request.POST.get("parent")}))

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
            action = 'برفض '
			
            if request.POST.get("type") == "1" :
              vote = True
              action = 'بالموافقة على '
            
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
            message = 'لقد شاركت في كتابة #دستور_مصر وقمت ' + action + art.name.encode('utf-8') + " من الدستور"
            #graph.put_wall_post(message, attachment)

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

    arts = Article.objects.filter(Q(summary__contains=query.strip()) | Q(name__contains=query.strip())).values('original').annotate(max_id=Max('id')).order_by()
    
    articles = []
    for art in arts:
        print art
        articles.append(get_object_or_404( Article, id= art['max_id'] ))
        print get_object_or_404( Article, id= art['max_id'] ).order
    
    articles = sorted(articles, key=lambda article: article.order)

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
    news = Article.objects.order_by('?')[:3]
    return render_to_response('slider.html',{'news':news} ,RequestContext(request))

def latest_comments(request):

    user = None
    if request.user.is_authenticated():
      user = request.user

    if request.method == 'POST':
        page =  request.POST.get("page")
        article =  request.POST.get("article")

        offset = settings.paginator * int(page)
        limit = settings.paginator

        obj_article = get_object_or_404( Article, id=article )

        votes = obj_article.get_votes()
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

        feedbacks = Feedback.objects.filter(article_id = article).order_by('-id')[offset:offset + limit]
        voted_fb = Rating.objects.filter(article_id = article, user = user)
        
        if(len(feedbacks) > 0):
             return render_to_response('latest_comments.html',{'p_votes': p_votes,'n_votes': n_votes,'feedbacks':feedbacks,'article':article,'page':page} ,RequestContext(request))
        else: 
             return HttpResponse('')

def total_contribution(request):
    feedback = Feedback.objects.all().count()
    feedback_ratings = Rating.objects.all().count()
    article_ratings = ArticleRating.objects.all().count()

    total = feedback + feedback_ratings + article_ratings

    return render_to_response('contribution.html',{'total':total,'feedback':feedback,'feedback_ratings':feedback_ratings,'article_ratings':article_ratings} ,RequestContext(request))


def top_liked(request):
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse('index'))
    articles = Article.get_top_liked(20)
    title = 'الأكثر قبولا'
    return render_to_response('statistics.html', {'articles': articles, 'title': title} ,RequestContext(request))

def top_disliked(request):
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse('index'))
    articles = Article.get_top_disliked(20)
    title = 'الأكثر رفضا'
    return render_to_response('statistics.html', {'articles': articles, 'title': title} ,RequestContext(request))

def top_commented(request):
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse('index'))
    articles = Article.get_top_commented(20)
    title = 'الأكثر مناقشة'
    return render_to_response('statistics.html', {'articles': articles, 'title': title} ,RequestContext(request))