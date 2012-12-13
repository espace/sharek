# Create your views here.

import mobile, memcache

from sharek import settings
from core.models import Topic, ArticleHeader

from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect

# get first memcached URI
mc = memcache.Client([settings.MEMCACHED_BACKEND])

def index(request):

    template_context = {}

    return render_to_response('mobile/index.html', template_context ,RequestContext(request))

def topics(request):

    topics = mc.get('topics_tree')
    if not topics:
         topics = Topic.objects.with_counts()
         mc.set('topics_tree', topics, settings.MEMCACHED_TIMEOUT)

    template_context = {'topics':topics,}

    return render_to_response('mobile/topics.html', template_context ,RequestContext(request))


def articles(request, topic_slug=None):

    topic = mc.get('topic_' + str(topic_slug))
    if not topic:
         topic = get_object_or_404( Topic, slug=topic_slug )
         mc.set('topic_' + str(topic_slug), topic, settings.MEMCACHED_TIMEOUT)
    
    articles = mc.get(str(topic_slug) + '_articles')
    if not articles:
         articles = topic.get_articles()
         mc.set(str(topic_slug) + '_articles', articles, settings.MEMCACHED_TIMEOUT)

    template_context = {'topic':topic,'articles':articles,}

    return render_to_response('mobile/articles.html', template_context ,RequestContext(request))


