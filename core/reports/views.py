
import textmining

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

import pprint
from difflib import SequenceMatcher

# http://python-cluster.sourceforge.net/
from cluster import HierarchicalClustering

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


    articles_acceptance = ArticleHeader.objects.acceptance_chart()
    approved_count = ArticleHeader.objects.get_approved_count()
    refused_count = ArticleHeader.objects.get_refused_count()
    
    context = Context({'user': user,'articles_acceptance': articles_acceptance,'approved_count':approved_count, 'refused_count':refused_count})

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

def cosine_distance(a, b):
    cos = 0.0
    a_tfidf = a["tfidf"]
    for token, tfidf in b["tfidf"].iteritems():
        if token in a_tfidf:
            cos += tfidf * a_tfidf[token]
    return cos

def normalize(features):
    norm = 1.0 / sqrt(sum(i**2 for i in features.itervalues()))
    for k, v in features.iteritems():
        features[k] = v * norm
    return features

def add_tfidf_to(documents):
    tokens = {}
    for id, doc in enumerate(documents):
        tf = {}
        doc["tfidf"] = {}
        doc_tokens = doc.get("tokens", [])
        for token in doc_tokens:
            tf[token] = tf.get(token, 0) + 1
        num_tokens = len(doc_tokens)
        if num_tokens > 0:
            for token, freq in tf.iteritems():
                tokens.setdefault(token, []).append((id, float(freq) / num_tokens))

    doc_count = float(len(documents))
    for token, docs in tokens.iteritems():
        idf = log(doc_count / len(docs))
        for id, tf in docs:
            tfidf = tf * idf
            if tfidf > 0:
                documents[id]["tfidf"][token] = tfidf

    for doc in documents:
        doc["tfidf"] = normalize(doc["tfidf"])

def choose_cluster(node, cluster_lookup, edges):
    new = cluster_lookup[node]
    if node in edges:
        seen, num_seen = {}, {}
        for target, weight in edges.get(node, []):
            seen[cluster_lookup[target]] = seen.get(
                cluster_lookup[target], 0.0) + weight
        for k, v in seen.iteritems():
            num_seen.setdefault(v, []).append(k)
        new = num_seen[max(num_seen)][0]
    return new

def majorclust(graph):
    cluster_lookup = dict((node, i) for i, node in enumerate(graph.nodes))

    count = 0
    movements = set()
    finished = False
    while not finished:
        finished = True
        for node in graph.nodes:
            new = choose_cluster(node, cluster_lookup, graph.edges)
            move = (node, cluster_lookup[node], new)
            if new != cluster_lookup[node] and move not in movements:
                movements.add(move)
                cluster_lookup[node] = new
                finished = False

    clusters = {}
    for k, v in cluster_lookup.iteritems():
        clusters.setdefault(v, []).append(k)

    return clusters.values()

def get_distance_graph(documents):
    class Graph(object):
        def __init__(self):
            self.edges = {}

        def add_edge(self, n1, n2, w):
            self.edges.setdefault(n1, []).append((n2, w))
            self.edges.setdefault(n2, []).append((n1, w))

    graph = Graph()
    doc_ids = range(len(documents))
    graph.nodes = set(doc_ids)
    for a, b in combinations(doc_ids, 2):
        graph.add_edge(a, b, cosine_distance(documents[a], documents[b]))
    return graph

def get_documents():
    texts = [
        "الاسلام دين الدوله واللغه العربيه لغتها الرسميه والشريعه الاسلاميه المصدر الاساسى للتشريع ...ولأتباع المسيحية واليهودية الحق في الاحتكام إلى شرائعهم الخاصة في أحوالهم الشخصية، وممارسة شئونهم (شعائرهم) الدينية واختيار قياداتهم الروحية.",
        "الاسلام دين الدوله واللغه العربيه لغتها الرسميه والشريعه الاسلاميه المصدر الاساسى للتشريع ...ولأتباع المسيحية واليهودية الحق في الاحتكام إلى شرائعهم الخاصة في أحوالهم الشخصية، وممارسة شئونهم (شعائرهم) الدينية واختيار قياداتهم الروحية.",
        "الشريعة الإسلامية المصدر الرئيسي للتشريع بديلاً عن مبادئ)",
        " الإسلام دين الدولة واللغة العربية لغتها الرسمية والشريعة الإسلامية المصدر الرئيسي الوحيد للتشريع..",
        "االاسلام دين الدولة و اللغة العربية لغتها الرسمية و الشريعة الاسلامية هي المصدر للتشريع",
        "الاسلام دين الدولة و اللغة العربية لغتها الرسمية و الشريعة الاسلامية هي المصدر الرئيسي للتشريع",
    ]
    return [{"text": text, "tokens": text.split()}
             for i, text in enumerate(texts)]

def feedback_clustering_tmp(request, article_slug):

    documents = get_documents()
    add_tfidf_to(documents)
    dist_graph = get_distance_graph(documents)

    html = "=========<br>"
    for cluster in majorclust(dist_graph):
        for doc_id in cluster:
            html += documents[doc_id]["text"] + "<br>"
        html += "=========<br>"

    return HttpResponse(html)

def feedback_clustering(request, article_slug):
    # Find the 10 most statistically significant two word phrases in the
    # full text of 'The Adventures of Sherlock Holmes'
    example_dir = os.path.dirname(__file__)
    sample_text_file = os.path.join(example_dir, 'holmes.txt')
    text = open(sample_text_file).read()
    words = textmining.simple_tokenize(text)
    bigrams = textmining.bigram_collocations(words)
    print '\nbigram_collocations_example 1\n'
    for bigram in bigrams[:10]:
        print ' '.join(bigram)

    return HttpResponse("")
