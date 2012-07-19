from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils import simplejson
from datetime import datetime

from dostor.models import Tag, Article, Feedback

from dostor.facebook.models import FacebookSession
from dostor.facebook import facebook_sdk
from dostor_masr import settings


def index(request):
    user = None
    if request.user.is_authenticated():
      user = request.user
    print
    print request.path
    tags = Tag.objects.all
    template_context = {'tags':tags,'settings': settings,'user':user,}
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
    template_context = {'feedbacks':feedbacks,'tags':tags,'tag':tag,'article': article,'user':user,'settings': settings,}
    return render_to_response('article.html',template_context ,RequestContext(request))


def modify(request):
    if request.method == 'POST':
        Feedback(user = request.POST.get("user_id"),article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.user.email, name = request.user.first_name + " " + request.user.last_name).save()
        feedback = Feedback.objects.filter(article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.user.email, name = request.user.first_name + " " + request.user.last_name)

        fb_user = FacebookSession.objects.get(user = request.user)
        # GraphAPI is the main class from facebook_sdp.py
        graph = facebook_sdk.GraphAPI(fb_user.access_token)
        attachment = {}
        attachment['link'] = 'http://www.google.com'
        attachment['picture'] = 'https://www.facebook.com/app_full_proxy.php?app=2231777543&v=1&size=z&cksum=70b5d7cc30cfba37533c713f0929b221&src=http%3A%2F%2Fespace.com.eg%2Fimages%2Frotator%2Felections.jpg'
        message = request.POST.get("suggestion")
        graph.put_wall_post(message, attachment)


        return HttpResponse(simplejson.dumps({'date':str(feedback[0].date),'id':feedback[0].id ,'suggestion':request.POST.get("suggestion")}))
