from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect


from dostor.models import Tag, Article

def index(request):
    tags = Tag.objects.all
    return render_to_response('index.html', {'tags':tags,},RequestContext(request))
    
    
def tag_detail(request, tag_slug):
    tags = Tag.objects.all
    tag = get_object_or_404( Tag, slug=tag_slug )
    articles = tag.article_set.all()
    return render_to_response('tag.html', {'tags':tags,'tag':tag,'articles': articles,},RequestContext(request))

def article_detail(request, tag_slug, article_slug):
    tags = Tag.objects.all
    tag = get_object_or_404( Tag, slug=tag_slug )
    article = get_object_or_404( Article, slug=article_slug )
    return render_to_response('article.html', {'tags':tags,'tag':tag,'article': article,},RequestContext(request))
