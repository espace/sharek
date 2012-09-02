import cStringIO as StringIO
#import ho.pisa as pisa
import xhtml2pdf.pisa as pisa

from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from cgi import escape

from dostor.models import Tag, Article, Feedback, Rating, Topic, Info, ArticleRating


def export_feedback(request):
    #Retrieve data or whatever you need
    result = Feedback.objects.all

    return render_to_pdf(
            'reports/export_feedback.html',
            {
                'pagesize':'A4',
                'mylist': result,
            }
        )

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    context = Context(context_dict)
    html  = template.render(context)
    result = StringIO.StringIO()

    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), mimetype='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))