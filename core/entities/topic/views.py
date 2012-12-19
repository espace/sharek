from sharek import settings

from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts  import render_to_response, get_object_or_404, redirect

from core.views import login,mc

from core.models import Topic, SuggestionVotes

def topic_detail(request, topic_slug=None):
    user = None

    login(request)
    if request.user.is_authenticated():
      user = request.user

    topics = mc.get('topics_list')
    if not topics:
         topics = Topic.objects.with_counts()
         mc.set('topics_list', topics, settings.MEMCACHED_TIMEOUT)


    if topic_slug:
    
        topic = mc.get('topic_' + str(topic_slug))
        if not topic:
             topic = get_object_or_404( Topic, slug=topic_slug )
             mc.set('topic_' + str(topic_slug), topic, settings.MEMCACHED_TIMEOUT)
    
        all_articles = mc.get(str(topic_slug) + '_articles')
        if not all_articles:
             all_articles = topic.get_articles()
             mc.set(str(topic_slug) + '_articles', all_articles, settings.MEMCACHED_TIMEOUT)

    else:

        if len(topics) > 0:

            topic = topics[0]
    
            all_articles = mc.get(str(topic.slug) + '_articles')
            if not all_articles:
                 all_articles = topic.get_articles()
                 mc.set(str(topic.slug) + '_articles', all_articles, settings.MEMCACHED_TIMEOUT)
        else:
            topic = None
            all_articles = None

    voted_suggestion = []

    if user:
        voted_suggestion = mc.get('voted_suggestion_'+ str(user.id))
        if not voted_suggestion:
           voted_suggestion = SuggestionVotes.objects.filter(user = user)
           mc.set('voted_suggestion_'+ str(user.id), voted_suggestion, 900) # 15 Minutes

    template_context = {'all_articles':all_articles, 'request':request, 'topics':topics,'topic':topic,'settings': settings,'user':user,'voted_suggestions':voted_suggestion}

    return render_to_response('topic_new.html',template_context ,RequestContext(request))

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