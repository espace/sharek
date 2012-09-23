from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse

from core.models import Tag, ArticleDetails
from core.models import Feedback, Rating, Topic
from core.models import Info, ArticleRating
from core.views import login

from wkhtmltopdf.views import render_to_pdf

from operator import attrgetter


def pdf(request):
    context.update({'objects': ModelA.objects.filter(p_id=100)})

    kwargs = {}
    if request.GET and request.GET.get('as', '') == 'html':
        render_to = render_to_response
    else:
        render_to = render_to_pdf
        kwargs.update(dict(
            filename='model-a.pdf',
            margin_top=0,
            margin_right=0,
            margin_bottom=0,
            margin_left=0))

    return render_to('pdf.html', context, **kwargs)



def export_feedback(request, article_slug):
    
    user = None
    login(request)

    
    if request.user.is_authenticated():# and request.user.is_staff:
      user = request.user
    else:
      return HttpResponseRedirect(reverse('index'))
    
    #Retrieve data or whatever you need
    articles = ArticleDetails.objects.all()
    articles =  sorted(articles,  key=attrgetter('header.topic.id','header.order','id'))
    article = get_object_or_404( ArticleDetails, slug=article_slug )
    feedback = Feedback.objects.filter(articledetails_id = article.id)

    template_context = {'article':article, 'articles':articles, 'feedbacks':feedback}
    return render_to_response('reports/export_feedback.html', template_context ,RequestContext(request))