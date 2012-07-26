from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseNotFound
from django.utils import simplejson
from datetime import datetime

from dostor.models import Tag, Article, Feedback, Rating, Topic

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from dostor.facebook.models import FacebookSession
from dostor.facebook import facebook_sdk
from dostor_masr import settings


def index(request):
    user = None
    if request.user.is_authenticated():
      user = request.user
    tags = Tag.objects.all
    feedback_count = len(Feedback.objects.all())
    perecent = int(feedback_count/5000)
    home = True
    template_context = {'home':home,'tags':tags,'settings': settings,'user':user,'count':feedback_count,'perecent':perecent}
    return render_to_response('index.html', template_context ,RequestContext(request))
    
    
def tag_detail(request, tag_slug):
    user = None
    if request.user.is_authenticated():
      user = request.user
    tags = Tag.objects.all
    tag = get_object_or_404( Tag, slug=tag_slug )
    articles = tag.article_set.all()

    template_context = {'tags':tags,'tag':tag,'articles': articles,'settings': settings,'user':user,}
    return render_to_response('tag.html',template_context ,RequestContext(request))

def topics(request):
    user = None
    if request.user.is_authenticated():
      user = request.user
    topics = Topic.objects.filter()
    topic = topics[0]
    articles = topic.article_set.all()

    template_context = {'topics':topics,'topic':topic,'articles': articles,'settings': settings,'user':user,}
    return render_to_response('topic.html',template_context ,RequestContext(request))

def topic_detail(request, topic_slug=None):
    user = None
    if request.user.is_authenticated():
      user = request.user
    if topic_slug:
        topics = Topic.objects.all
        topic = get_object_or_404( Topic, slug=topic_slug )
    else:
        topics = Topic.objects.filter()
        topic = topics[0]

    articles = topic.article_set.all()

    template_context = {'topics':topics,'topic':topic,'articles': articles,'settings': settings,'user':user,}
    return render_to_response('topic.html',template_context ,RequestContext(request))

def article_detail(request, classified_by, class_slug, article_slug, order_by="latest"):
    user = None
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

    if order_by == "latest":
        feedbacks = Feedback.objects.filter(article_id = article.id).order_by('-date')
    else:
        feedbacks = Feedback.objects.filter(article_id = article.id).order_by('-order')

    paginator = Paginator(feedbacks, settings.paginator) 
    page = request.GET.get('page')


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
        template_context = {'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'p_votes': p_votes,'n_votes': n_votes,'tags':tags,'tag':tag}
    elif classified_by == "topics":
        template_context = {'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'p_votes': p_votes,'n_votes': n_votes,'topics':topics,'topic':topic}      
    
    return render_to_response('article.html',template_context ,RequestContext(request))


def modify(request):
    if request.method == 'POST':
        Feedback(user = request.POST.get("user_id"),article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.user.email, name = request.user.first_name + " " + request.user.last_name).save()
        feedback = Feedback.objects.filter(article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.user.email, name = request.user.first_name + " " + request.user.last_name)

        fb_user = FacebookSession.objects.get(user = request.user)
        # GraphAPI is the main class from facebook_sdp.py
        graph = facebook_sdk.GraphAPI(fb_user.access_token)
        attachment = {}
        attachment['link'] = settings.domain+request.POST.get("class_slug")+"/"+request.POST.get("article_slug")
        attachment['picture'] = settings.domain+settings.STATIC_URL+"images/facebook-thumb.jpg"
        message = request.POST.get("suggestion").encode('utf8') 
        graph.put_wall_post(message, attachment)


        return HttpResponse(simplejson.dumps({'date':str(feedback[0].date),'id':feedback[0].id ,'suggestion':request.POST.get("suggestion")}))


def vote(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            feedback =  request.POST.get("modification")
            user =  request.user

            record = Rating.objects.filter(feedback_id = feedback, user = user )

            vote = False
            print request.POST.get("type")
            if request.POST.get("type") == "1" :
              vote = True
            
            if record:
                record[0].vote = vote
                record[0].save()
            else:
                Rating(user = user, vote = vote, feedback_id = feedback,article_id = request.POST.get("article")).save()
            
            mod = Feedback.objects.get(id=feedback)
            if request.POST.get("type") == "1" :
                temp = 1
            else:
                temp = -1
            mod.order = mod.order + temp
            mod.save()

            votes = Rating.objects.filter(feedback_id = feedback)
            p = 0
            n = 0
            for v in votes:
              if v.vote == True:
                p += 1
              else:
                n += 1            
            return HttpResponse(simplejson.dumps({'modification':request.POST.get("modification"),'p':p,'n':n}))
          
def facebook_comment(request):
    return render_to_response('facebook_comment.html', {},RequestContext(request))
