from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect


from dostor.models import Tag

def index(request):
    tags = Tag.objects.all
    return render_to_response('index.html', {'tags':tags,},RequestContext(request))
    
    
def tag_detail(request, tag_slug):
    tag = get_object_or_404( Tag, slug=tag_slug )
    articles = tag.article_set.all()
    return render_to_response('tag_detail.html', {'tag':tag,'articles': articles,},RequestContext(request))
