# This Python file uses the following encoding: utf-8
import os, sys

from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.utils import simplejson
from datetime import datetime
from django.db import connection

from diff_match import diff_match_patch
from django.contrib import auth

from core.models import Tag, ArticleDetails, ArticleHeader, Feedback, Rating, Topic, Info, ArticleRating, User

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
import core
import os.path
from operator import attrgetter

from core.social_auth.models import UserSocialAuth

def tmp(request):
    return HttpResponseRedirect(reverse('index'))

def index(request):
    user = None

    login(request)
    home = True
    if request.user.is_authenticated():
      user = request.user
	  
    topics = Topic.objects.with_counts
    
    top_users = User.get_top_users(12)
    total = Topic.total_contributions

    top_liked 	  = ArticleDetails.objects.get_top_liked(5)
    top_commented = ArticleDetails.objects.get_top_commented(5)

    tags = Tag.objects.all

    template_context = {'settings':settings, 'request':request, 'top_users':top_users, 'home':home,'topics':topics,'settings': settings,'user':user,'total':total,'top_liked':top_liked, 'top_disliked':top_disliked, 'top_commented':top_commented, 'tags':tags}

    return render_to_response('index.html', template_context ,RequestContext(request))
        
def tag_detail(request, tag_slug):
    user = None

    login(request)
    if request.user.is_authenticated():
      user = request.user
    tags = Tag.objects.all
    tag = get_object_or_404( Tag, slug=tag_slug )
    
    articles = tag.get_articles()

    voted_articles = ArticleRating.objects.filter(user = user)

    paginator = Paginator(articles, settings.paginator) 
    articles = paginator.page(1)

    template_context = {'voted_articles':voted_articles,'request':request, 'tags':tags,'tag':tag,'articles': articles,'settings': settings,'user':user,}
    return render_to_response('tag.html',template_context ,RequestContext(request))

def tag_next_articles(request):

    user = None
    if request.user.is_authenticated():
      user = request.user

    if request.method == 'POST':
        page =  request.POST.get("page")
        tag_slug =  request.POST.get("tag")

        offset = settings.paginator * int(page)
        limit = settings.paginator

        tag = get_object_or_404( Tag, slug=tag_slug )
        articles = tag.get_articles_limit(offset, offset + limit)
        
        if(len(articles) > 0):
             return render_to_response('include/next_articles.html',{'articles':articles} ,RequestContext(request))
        else: 
             return HttpResponse('')

def topic_detail(request, topic_slug=None):
    user = None

    login(request)
    if request.user.is_authenticated():
      user = request.user
    if topic_slug:
        topics = Topic.objects.filter(parent_id = None)
        topic = get_object_or_404( Topic, slug=topic_slug )
        all_articles = topic.get_articles()
    else:
        topics = Topic.objects.filter()
        if topics.count() > 0:
            topic = topics[0]
            all_articles = topic.get_articles()
        else:
            topic = None
            all_articles = None

    voted_articles = ArticleRating.objects.filter(user = user)

    paginator = Paginator(all_articles, settings.paginator) 
    articles = paginator.page(1)

    template_context = {'topic_page':True, 'all_articles':all_articles, 'request':request, 'topics':topics,'topic':topic,'articles': articles,'settings': settings,'user':user,'voted_articles':voted_articles}
    return render_to_response('topic.html',template_context ,RequestContext(request))

def topic_next_articles(request):

    user = None
    if request.user.is_authenticated():
      user = request.user

    if request.method == 'POST':
        page =  request.POST.get("page")
        topic_slug =  request.POST.get("topic")

        offset = settings.paginator * int(page)
        limit = settings.paginator

        topic = get_object_or_404( Topic, slug=topic_slug )
        articles = topic.get_articles_limit(offset, limit)
        
        if(len(articles) > 0):
             return render_to_response('include/next_articles.html',{'articles':articles} ,RequestContext(request))
        else: 
             return HttpResponse('')

def article_diff(request, article_slug):
    
    user = None
    login(request)

    if request.user.is_authenticated():
      user = request.user

    lDiffClass = diff_match_patch()

    topics = Topic.objects.all

    article = get_object_or_404( ArticleDetails, slug=article_slug )
    tmp_versions = article.header.articledetails_set.all().order_by('id')

    previous = ''
    versions = []
    for temp in tmp_versions:
        article_info = {}

        article_info['current'] = temp.current
        article_info['name'] = temp.header.name
        article_info['slug'] = temp.slug
        article_info['date'] = temp.mod_date
        article_info['topic_absolute_url'] = temp.header.topic.get_absolute_url

        if previous == "":
           article_info['text'] = previous = temp.summary.raw
        else:
           lDiffs = lDiffClass.diff_main(previous, temp.summary.raw)
           lDiffClass.diff_cleanupSemantic(lDiffs)
           lDiffHtml = lDiffClass.diff_prettyHtml(lDiffs)
           article_info['text'] = lDiffHtml

        versions.append(article_info)

    template_context = {'article': article, 'topics':topics, 'topic':article.header.topic, 'versions': versions, 'request':request, 'user':user,'settings': settings}
    return render_to_response('article_diff.html',template_context ,RequestContext(request))

def article_detail(request, classified_by, class_slug, article_slug, order_by="def"):
    user = None

    login(request)

    if request.user.is_authenticated():
      user = request.user

    article = get_object_or_404( ArticleDetails, slug=article_slug )
    topic = get_object_or_404( Topic, slug=article.header.topic.slug )

    next = ArticleHeader.objects.get_next(article.header.topic.id, article.header.order)
    prev = ArticleHeader.objects.get_prev(article.header.topic.id, article.header.order)

    if classified_by == "tags":  
        tags = Tag.objects.all
        tag = get_object_or_404( Tag, slug=class_slug )
    elif classified_by == "topics":
        topics = Topic.objects.all
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')

    
    versions = []
    arts = article.header.articledetails_set.all()

    related_tags = article.header.tags.all

    top_ranked = []
    inactive_users = User.get_inactive
    size = len(Feedback.objects.filter(articledetails_id = article.id, parent_id = None).order_by('-id').exclude(user__in=inactive_users))
    if size > 3:
        top_ranked = Feedback.objects.filter(articledetails_id = article.id, parent_id = None).order_by('-order').exclude(user__in=inactive_users)[:3]
    else:
        top_ranked = []

    if order_by == "latest" or order_by == "def":
        if len(top_ranked) == 3:
            feedbacks = Feedback.objects.filter(articledetails_id = article.id, parent_id = None).order_by('-id').exclude(id=top_ranked[0].id).exclude(id=top_ranked[1].id).exclude(id=top_ranked[2].id).exclude(user__in=inactive_users)
        else:
            feedbacks = Feedback.objects.filter(articledetails_id = article.id, parent_id = None).order_by('-id').exclude(user__in=inactive_users)
    elif order_by == "order":
        if len(top_ranked) == 3:
            feedbacks = Feedback.objects.filter(articledetails_id = article.id, parent_id = None).order_by('-order').exclude(id=top_ranked[0].id).exclude(id=top_ranked[1].id).exclude(id=top_ranked[2].id).exclude(user__in=inactive_users)
        else:
            feedbacks = Feedback.objects.filter(articledetails_id = article.id, parent_id = None).order_by('-order').exclude(user__in=inactive_users)

    paginator = Paginator(feedbacks, settings.paginator) 
    page = request.GET.get('page')

    voted_fb = Rating.objects.filter(articledetails_id = article.id, user = user)
    voted_article = ArticleRating.objects.filter(articledetails_id = article.id, user = user)

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

    if classified_by == "tags":  
        template_context = {'prev':prev,'next':next,'arts':arts,'voted_articles':voted_article, 'article_rate':article_rate,'order_by':order_by,'voted_fb':voted_fb,'top_ranked':top_ranked,'request':request, 'related_tags':related_tags,'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'tags':tags,'tag':tag}
    elif classified_by == "topics":
        template_context = {'topic_page':True,'prev':prev,'next':next,'arts':arts,'voted_articles':voted_article, 'article_rate':article_rate,'order_by':order_by,'voted_fb':voted_fb,'top_ranked':top_ranked,'request':request, 'related_tags':related_tags,'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'topics':topics,'topic':topic}      
    
    return render_to_response('article.html',template_context ,RequestContext(request))

def latest_comments(request):

    user = None
    if request.user.is_authenticated():
      user = request.user

    if request.method == 'POST':
        page =  request.POST.get("page")
        article =  request.POST.get("article")
        order_by =  request.POST.get("order_by")

        offset = settings.paginator * int(page)
        limit = settings.paginator

        inactive_users = User.get_inactive
        obj_article = get_object_or_404( ArticleDetails, id=article )

        top_ranked = []
        inactive_users = User.get_inactive
        size = len(Feedback.objects.filter(articledetails_id = obj_article.id, parent_id = None).order_by('-id').exclude(user__in=inactive_users))
        if size > 3:
            top_ranked = Feedback.objects.filter(articledetails_id = obj_article.id, parent_id = None).order_by('-order').exclude(user__in=inactive_users)[:3]
        else:
            top_ranked = []

        if order_by == "latest" or order_by == "def":
            if len(top_ranked) == 3:
                feedbacks = Feedback.objects.filter(articledetails_id = obj_article.id, parent_id = None).order_by('-id').exclude(user__in=inactive_users).exclude(id=top_ranked[0].id).exclude(id=top_ranked[1].id).exclude(id=top_ranked[2].id)
            else:
                feedbacks = Feedback.objects.filter(articledetails_id = obj_article.id, parent_id = None).order_by('-id').exclude(user__in=inactive_users)
        elif order_by == "order":
            if len(top_ranked) == 3:
                feedbacks = Feedback.objects.filter(articledetails_id = obj_article.id, parent_id = None).order_by('-order').exclude(user__in=inactive_users).exclude(id=top_ranked[0].id).exclude(id=top_ranked[1].id).exclude(id=top_ranked[2].id)
            else:
                feedbacks = Feedback.objects.filter(articledetails_id = obj_article.id, parent_id = None).order_by('-order').exclude(user__in=inactive_users)

        voted_fb = Rating.objects.filter(articledetails_id = obj_article.id, user = user)
        voted_article = ArticleRating.objects.filter(articledetails_id = obj_article.id, user = user)

        paginator = Paginator(feedbacks, settings.paginator)
        try:
            feedbacks = paginator.page(page)
            return render_to_response('include/latest_comments.html',{'voted_fb':voted_fb,'voted_articles':voted_article,'feedbacks':feedbacks,'article':article,'page':page} ,RequestContext(request))
        except PageNotAnInteger:
            return HttpResponse('')
        except EmptyPage:
            return HttpResponse('')

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
            if feedback.user == request.user.username or request.user.is_staff:
                feedback.articledetails.feedback_count = feedback.articledetails.feedback_count - 1
                feedback.articledetails.save()
                feedback.delete()
                return HttpResponse(simplejson.dumps({'feedback_id':request.POST.get("feedback"),'reply_ids':reply_ids}))

def modify(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            sug = str(request.POST.get("suggestion").encode('utf-8'))
            article = get_object_or_404( ArticleDetails, id=request.POST.get("article"))
            feedbacks = Feedback.objects.filter(articledetails_id = request.POST.get("article"), email= request.POST.get("email"), name = request.POST.get("name"))
            for feedback in feedbacks:
                if feedback.suggestion.raw.encode('utf-8') == sug:
                    return HttpResponse(simplejson.dumps({'duplicate':True,'name':request.POST.get("name")}))

            Feedback(user = request.POST.get("user_id"),articledetails_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email = request.POST.get("email"), name = request.POST.get("name")).save()
            feedback = Feedback.objects.filter(articledetails_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.POST.get("email"), name = request.POST.get("name"))
            article.feedback_count = article.feedback_count + 1
            article.save()
                    
            
            if request.user.username != "admin":
                # post on twitter or facebook
                if UserSocialAuth.auth_provider(request.user.username) == 'facebook':
                    fb_user = FacebookSession.objects.get(user = request.user)
                    # GraphAPI is the main class from facebook_sdp.py
                    graph = facebook_sdk.GraphAPI(fb_user.access_token)
                    attachment = {}
                    attachment['link'] = settings.domain+"sharek/"+request.POST.get("class_slug")+"/"+request.POST.get("article_slug")+"/"
                    attachment['picture'] = settings.domain + settings.STATIC_URL + "images/facebook.png"
                    message = 'لقد شاركت في كتابة #دستور_مصر وقمت بالتعليق على '+get_object_or_404(ArticleDetails, id=request.POST.get("article")).header.name.encode('utf-8')+" من الدستور"
                    graph.put_wall_post(message, attachment)
                
                if UserSocialAuth.auth_provider(request.user.username) == 'twitter':
                    print 'posting to twitter ....'
                    
            return HttpResponse(simplejson.dumps({'date':str(feedback[0].date),'id':feedback[0].id ,'suggestion':request.POST.get("suggestion")}))

def reply_feedback(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            sug = str(request.POST.get("suggestion").encode('utf-8'))
            feedbacks = Feedback.objects.filter(articledetails_id = request.POST.get("article"), email= request.POST.get("email"), name = request.POST.get("name"))
            for feedback in feedbacks:
                if feedback.suggestion.raw.encode('utf-8') == sug:
                    return HttpResponse(simplejson.dumps({'duplicate':True,'name':request.POST.get("name")}))
            Feedback(user = request.POST.get("user_id"),articledetails_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email = request.POST.get("email"), name = request.POST.get("name"), parent_id = request.POST.get("parent")).save()
            reply = Feedback.objects.filter(user = request.POST.get("user_id"),articledetails_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.POST.get("email"), name = request.POST.get("name"), parent_id= request.POST.get("parent"))
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
            
            mod = Feedback.objects.get(id=feedback)

            p = mod.likes
            n = mod.dislikes
            
            if record:
                if record[0].vote != vote:
                    if vote == True:
                      p += 1
                      n -= 1
                    else:
                      n += 1
                      p -= 1
                record[0].vote = vote
                record[0].save()
            else:
                Rating(user = user, vote = vote, feedback_id = feedback,articledetails_id = request.POST.get("article")).save()
                if vote == True:
                  p += 1
                else:
                  n += 1

            mod.likes = p
            mod.dislikes = n
            mod.order = mod.likes - mod.dislikes
            mod.save()

            return HttpResponse(simplejson.dumps({'modification':request.POST.get("modification"),'p':p,'n':n,'vote':request.POST.get("type")}))

def article_vote(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            article =  request.POST.get("article")
            user =  request.user

            vote = False
			
            if request.POST.get("type") == "1" :
              vote = True

            art = ArticleDetails.objects.get(id = article)

            p = art.likes
            n = art.dislikes

            record = ArticleRating.objects.filter(articledetails_id = article, user = user )
            
            if record:
                if record[0].vote != vote:
                    if vote == True:
                      p += 1
                      n -= 1
                    else:
                      n += 1
                      p -= 1
                record[0].vote = vote
                record[0].save()
            else:
                ArticleRating(user = user, vote = vote,articledetails_id = article).save()
                if vote == True:
                  p += 1
                else:
                  n += 1

            art.likes = p
            art.dislikes = n
            art.save()

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
    
    query = request.POST.get("q")
    if query == None:
        if request.GET.get("state"):
            query = request.GET.get("state")
        else:
            return HttpResponseRedirect(reverse('index'))
    if len(query.strip()) == 0:
        return HttpResponseRedirect(reverse('index'))

    arts = ArticleDetails.objects.filter(Q(summary__contains=query.strip()) | Q(header__name__contains=query.strip()) , current = True)
    arts = sorted(arts,  key=attrgetter('header.topic.id','header.order','id'))
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

def ajx_search(request):
    if request.method == 'GET':
        page =  request.GET.get("page")
        query = request.GET.get("q")

        articles = ArticleDetails.objects.filter(Q(summary__contains=query.strip()) | Q(header__name__contains=query.strip()) , current = True)
        articles =  sorted(articles,  key=attrgetter('header.topic.id','header.order','id'))

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
    articles = ArticleDetails.get_top_commented(settings.paginator)
    title = 'الأكثر مناقشة'
    return render_to_response('statistics.html', {'type':"comments",'settings': settings,'user':user,'articles': articles, 'title': title} ,RequestContext(request))

def statistics(request):
        if request.method == 'POST':
            page =  request.POST.get("page")
            stat_type = request.POST.get("type")

            if stat_type == "likes":
                articles = ArticleDetails.objects.filter(current = True).order_by('-likes')
            elif stat_type == "dislikes":
                articles = ArticleDetails.objects.filter(current = True).order_by('-dislikes')
            elif stat_type == "comments":
                articles = ArticleDetails.objects.filter(current = True).annotate(num_feedbacks=Count('feedback')).order_by('-num_feedbacks')
            

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
    if request.user.is_authenticated():
      user = request.user

    top_users = []
    inactive_users = User.get_inactive
    counter = 0
    if user == None:
        temp_users = Feedback.objects.values('user').annotate(user_count=Count('user')).order_by('?').exclude(user__in=inactive_users)[:2000]
    else:
        temp_users = Feedback.objects.values('user').annotate(user_count=Count('user')).order_by('?').exclude(user__in=inactive_users).exclude(user__in=inactive_users).exclude(user=user.username)[:2000]
        feedback = Feedback.objects.filter(user = user).count()
        feedback_ratings = Rating.objects.filter(user = user).count()
        article_ratings = ArticleRating.objects.filter(user = user).count()
        counter = feedback + feedback_ratings + article_ratings

    bound_h = random.randint(210,235)
    bound_v = random.randint(1,25)*41
    bound = bound_h+bound_v

    for temp in temp_users:
        try:
            top_user = User.objects.get(username=temp['user'])
        except Exception:
            top_user = None
        
        if top_user:
            top_users.append(top_user)

    return render_to_response('map.html', {'counter':counter,'bound':bound,'settings': settings,'user':user,'top_users': top_users} ,RequestContext(request))
