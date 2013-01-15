from sharek import settings
from django.core.paginator import Paginator, PageNotAnInteger

from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts  import render_to_response, get_object_or_404, redirect

from core.views import login,mc

from core.models import Tag, ArticleRating

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