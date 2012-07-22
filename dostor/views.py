from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils import simplejson
from datetime import datetime

from dostor.models import Tag, Article, Feedback, Rating

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

def article_detail(request, tag_slug, article_slug):
    user = None
    if request.user.is_authenticated():
      user = request.user
    tags = Tag.objects.all
    tag = get_object_or_404( Tag, slug=tag_slug )
    article = get_object_or_404( Article, slug=article_slug )
    feedbacks = Feedback.objects.filter(article_id = article.id)
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
    template_context = {'feedbacks':feedbacks,'tags':tags,'tag':tag,'article': article,'user':user,'settings': settings,'p_votes': p_votes,'n_votes': n_votes,}
    return render_to_response('article.html',template_context ,RequestContext(request))


def modify(request):
    if request.method == 'POST':
        Feedback(user = request.POST.get("user_id"),article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.user.email, name = request.user.first_name + " " + request.user.last_name).save()
        feedback = Feedback.objects.filter(article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.user.email, name = request.user.first_name + " " + request.user.last_name)

        fb_user = FacebookSession.objects.get(user = request.user)
        # GraphAPI is the main class from facebook_sdp.py
        graph = facebook_sdk.GraphAPI(fb_user.access_token)
        attachment = {}
        print settings.domain
        print request.POST.get("tag_slug")
        print request.POST.get("article_slug")
        print settings.domain+request.POST.get("tag_slug")+"/"+request.POST.get("article_slug")
        attachment['link'] = settings.domain+request.POST.get("tag_slug")+"/"+request.POST.get("article_slug")
        attachment['picture'] = 'https://www.facebook.com/app_full_proxy.php?app=2231777543&v=1&size=z&cksum=70b5d7cc30cfba37533c713f0929b221&src=http%3A%2F%2Fespace.com.eg%2Fimages%2Frotator%2Felections.jpg'
        message = request.POST.get("suggestion")
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

            votes = Rating.objects.filter(feedback_id = feedback)
            p = 0
            n = 0
            for v in votes:
              if v.vote == True:
                p += 1
              else:
                n += 1            
            return HttpResponse(simplejson.dumps({'modification':request.POST.get("modification"),'p':p,'n':n}))
          
