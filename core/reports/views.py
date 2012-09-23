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

#from wkhtmltopdf import render_to_pdf

from operator import attrgetter


def pdf(request):
      t = loader.get_template('/reports/template.html')
      c = Context({'inspection':'test'})
      rendered = t.render(c)
      f = open('/reports/template.html', 'w')
      f.write(rendered)
      f.close()
      command_args = 'wkhtmltopdf --page-size Letter /reports/template.html -'
      popen = Popen(command_args, bufsize=4096, stdout=PIPE, stderr=PIPE, shell=True)
      popen.wait()
      pdf_contents = popen.stdout.read()
      r = HttpResponse(pdf_contents, mimetype='application/pdf')
      r['Content-Disposition'] = 'filename=InspectionReport.pdf'
      return r




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