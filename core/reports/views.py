import sys
import os
import core
import os.path
import subprocess

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

import time
from datetime import datetime
from operator import attrgetter
from sharek import settings

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
		template = loader.get_template('reports/topic_template.html')
		rendered = template.render(context)
		full_temp_html_file_name = core.__path__[0] + '/static/temp/topic_template_' + date_str + '.html'
		file= open(full_temp_html_file_name, 'w')
		file.write(rendered.encode('utf8'))
		file.close( )
	
		command_args = 'wkhtmltopdf ' + full_temp_html_file_name + ' -'
		popen = subprocess.Popen(command_args, bufsize=4096, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		pdf_contents = popen.stdout.read()
		popen.terminate()
		popen.wait()
		
		#If you want to send email (Better use Thread)
		#email = EmailMultiAlternatives("Sample PDF", "Please find the attached sample pdf.", "example@shivul.com", ["email@example.com",])
		#email.attach('sample.pdf', pdf_contents, 'application/pdf')
		#email.send()
			
		response = HttpResponse(pdf_contents, mimetype='application/pdf')
		response['Content-Disposition'] = 'filename=Sample.pdf'
		return response


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