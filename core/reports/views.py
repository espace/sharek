import sys
import os
import core
import os.path
import subprocess
import mimetypes
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from core.models import Tag, ArticleDetails, ArticleHeader
from core.models import Feedback, Rating, Topic
from core.models import Info, ArticleRating, User
from core.views import login

import time
import memcache
from datetime import datetime
from operator import attrgetter
from sharek import settings

# get first memcached URI
mc = memcache.Client([settings.MEMCACHED_BACKEND])

def article_history(request, header_id=None,order=0):
    user = None

    login(request)

    if request.user.is_authenticated() and request.user.is_staff:
      user = request.user
    else:
        return HttpResponseRedirect(reverse('index'))

    if not header_id:
        header_id = ArticleHeader.objects.get_first()[0]

    article_history = ArticleHeader.objects.get_history_chart(header_id)
    next_article = ArticleHeader.objects.get_next_art(order)
    prev_article = ArticleHeader.objects.get_prev_art(order)

    context = Context({'user': user, 'article_history': article_history,'next_article':next_article,'prev_article':prev_article})

    return render_to_response('charts/article_history.html', context ,RequestContext(request))

def comments_chart(request):
    user = None

    login(request)

    if request.user.is_authenticated() and request.user.is_staff:
      user = request.user
    else:
        return HttpResponseRedirect(reverse('index'))

    chart_data = mc.get('chart_data')
    if not chart_data:
         chart_data = Feedback.objects.feedback_charts()
         mc.set('chart_data', chart_data, settings.MEMCACHED_TIMEOUT)

    context = Context({'user': user, 'chart_data': chart_data})

    return render_to_response('charts/comments.html', context ,RequestContext(request))

def users_chart(request):
    user = None

    login(request)

    if request.user.is_authenticated() and request.user.is_staff:
      user = request.user
    else:
        return HttpResponseRedirect(reverse('index'))

    user_chart = mc.get('user_chart')
    if not user_chart:
        user_chart = user.users_chart()
        mc.set('user_chart', user_chart, settings.MEMCACHED_TIMEOUT)

    context = Context({'user': user, 'user_chart': user_chart})

    return render_to_response('charts/users.html', context ,RequestContext(request))

def articles_acceptance(request):
    user = None

    login(request)

    if request.user.is_authenticated() and request.user.is_staff:
        user = request.user
    else:
        return HttpResponseRedirect(reverse('index'))

    articles_acceptance = mc.get('articles_acceptance')
    if not articles_acceptance:
         articles_acceptance = ArticleHeader.objects.acceptance_chart()
         mc.set('articles_acceptance', articles_acceptance, settings.MEMCACHED_TIMEOUT)

    max_min = ArticleHeader.objects.get_max_min()
    max = max_min[0]
    min = max_min[1]
    
    context = Context({'user': user, 'max':max,'min':min,'articles_acceptance': articles_acceptance})

    return render_to_response('charts/acceptance.html', context ,RequestContext(request))

def comments_pdf(request, article_slug=None):
    user = None

    login(request)

    if request.user.is_authenticated() and request.user.is_staff:
      user = request.user
    else:
        return HttpResponseRedirect(reverse('index'))

    if article_slug:
        article = get_object_or_404( ArticleDetails, slug=article_slug )

    inactive_users = User.get_inactive

    comments = Feedback.objects.filter(articledetails_id = article.id, parent_id = None).order_by('-id').exclude(user__in=inactive_users)

    dt_obj = datetime.now()
    date_display = dt_obj.strftime("%Y-%m-%d")

    context = Context({'article':article, 'comments':comments, 'date_display': date_display})

    kwargs = {}

    if request.GET and request.GET.get('as', '') == 'html':
        return render_to_response('reports/comments_template.html', context ,RequestContext(request))

    else:
        return render_to_pdf('reports/comments_template.html', 'comments_template_', context, 'article-' + str(article.slug))

def topics_pdf(request):
    user = None

    login(request)

    if request.user.is_authenticated():
      user = request.user

    topics = Topic.objects.all().order_by('order')

    dt_obj = datetime.now()
    date_str = dt_obj.strftime("%Y%m%d_%H%M%S")
    date_display = dt_obj.strftime("%Y-%m-%d")

    context = Context({'topics':topics, 'date_display': date_display})

    kwargs = {}

    if request.GET and request.GET.get('as', '') == 'html':
        return render_to_response('reports/topics_template.html', context ,RequestContext(request))

    else:
        return render_to_pdf('reports/topics_template.html', 'topics_template_', context, 'dostor-masr')

def topic_pdf(request, topic_slug=None):
    user = None

    login(request)

    if request.user.is_authenticated():
      user = request.user

    if topic_slug:
        topic = get_object_or_404( Topic, slug=topic_slug )
        articles = topic.get_articles()

    dt_obj = datetime.now()
    date_str = dt_obj.strftime("%Y%m%d_%H%M%S")
    date_display = dt_obj.strftime("%Y-%m-%d")

    context = Context({'topic':topic, 'articles':articles, 'date_display': date_display})

    kwargs = {}

    if request.GET and request.GET.get('as', '') == 'html':
        return render_to_response('reports/topic_template.html', context ,RequestContext(request))

    else:
        return render_to_pdf('reports/topic_template.html', 'topic_template_', context, 'topic-' + str(topic_slug))

def export_feedback(request, article_slug):
    
    user = None
    login(request)

    
    if request.user.is_authenticated() and request.user.is_staff:
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

def render_to_pdf(template_html, template_prefix, context, pdf_filename):

    generated_pdf = mc.get(pdf_filename + '_pdf')

    output_file = core.__path__[0] + '/static/pdf/' + pdf_filename + '.pdf'

    if not generated_pdf or not os.path.isfile(output_file):

        dt_obj = datetime.now()
        date_str = dt_obj.strftime("%Y%m%d_%H%M%S")
        date_display = dt_obj.strftime("%Y-%m-%d")

        template = loader.get_template(template_html)
        rendered = template.render(context)
        full_temp_html_file_name = core.__path__[0] + '/static/temp/' + template_prefix + date_str + '.html'
        file= open(full_temp_html_file_name, 'w')
        file.write(rendered.encode('utf8'))
        file.close()

        command_args = 'wkhtmltopdf -L 10 -R 10 -T 20 -B 10 --footer-html ' + core.__path__[0] + '/static/footer.html ' + full_temp_html_file_name + ' ' + output_file
        popen = subprocess.Popen(command_args, bufsize=4096, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        pdf_contents = popen.stdout.read()
        popen.terminate()
        popen.wait()

        mc.set(pdf_filename + '_pdf', pdf_filename + '_generated', settings.MEMCACHED_TIMEOUT)

    download_name = pdf_filename + '.pdf'
    wrapper       = FileWrapper(open(output_file))
    content_type  = mimetypes.guess_type(output_file)[0]

    response = HttpResponse(wrapper,content_type=content_type)
    response['Content-Length'] = os.path.getsize(output_file)    
    response['Content-Disposition'] = "attachment; filename=%s"%download_name

    return response
