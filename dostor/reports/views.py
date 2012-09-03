
from django.template import Context, loader, RequestContext
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from django.shortcuts  import render_to_response, get_object_or_404, redirect

from dostor.models import Tag, Article, Feedback, Rating, Topic, Info, ArticleRating


def export_feedback(request, article_slug):

    #Retrieve data or whatever you need
    articles = Article.objects.all
    article = get_object_or_404( Article, slug=article_slug )
    feedback = Feedback.objects.filter(article_id = article.id)

    template_context = {'article':article, 'articles':articles, 'feedbacks':feedback}
    return render_to_response('reports/export_feedback.html', template_context ,RequestContext(request))