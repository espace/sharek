from django.template import Context, loader, RequestContext
from django.shortcuts  import render_to_response, get_object_or_404, redirect


from dostor.models import Tag, Article

from dostor.facebook.models import FacebookSession
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
    template_context = {'tags':tags,'tag':tag,'article': article,'user':user,'settings': settings,}
    return render_to_response('article.html',template_context ,RequestContext(request))


def modify(request):
    if request.method == 'POST':
        feedback = Feedback(article_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.user.email, name = request.user.name).save()
        return HttpResponse(simplejson.dumps({'id':feedback.id ,'suggestion':request.POST.get("suggestion")}))
