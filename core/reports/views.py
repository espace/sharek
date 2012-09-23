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
from sharek import settings


def pdf(request):
    template = loader.get_template('reports/template.html')
    context = Context({'user':request.user,'msg':'Testing sample PDF creation'})
    rendered = template .render(context )

    ROOT_FOLDER =  'http://dostor-masr.espace-technologies.com/sharek/static/'

    temp_html_file_name = 'temp_template.html'
    full_temp_html_file_name = ROOT_FOLDER + temp_html_file_name
    print(full_temp_html_file_name)
    file= open(full_temp_html_file_name, 'w')
    file.write(rendered)
    file.close( )

    command_args = 'wkhtmltopdf --page-size Letter ' + full_temp_html_file_name
    popen = subprocess.Popcd en(command_args, bufsize=4096, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    pdf_contents = popen.stdout.read( )
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