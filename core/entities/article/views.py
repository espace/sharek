# This Python file uses the following encoding: utf-8
from sharek import settings
from django.core.paginator import Paginator, PageNotAnInteger

from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.utils import simplejson

from core.views import login,mc
from core.helpers.diff_match import diff_match_patch
import core.analysis.tfidf as tfidf


from core.models import ArticleDetails, ArticleHeader, PollOptions, PollResult, Suggestion, SuggestionVotes, Topic, Feedback, Rating

def article_detail(request, classified_by, class_slug, article_slug, order_by="def", comment_no=None):
    user = None

    login(request)

    if request.user.is_authenticated():
      user = request.user

    article = mc.get('article_' + str(article_slug))
    if not article:
         article = ArticleHeader.objects.get_article(article_slug)
         mc.set('article_' + str(article_slug), article, settings.MEMCACHED_TIMEOUT)

    topic = get_object_or_404( Topic, slug = article.topic_slug )

    next = ArticleHeader.objects.get_next(article.topic_id, article.order)
    prev = ArticleHeader.objects.get_prev(article.topic_id, article.order)

    if classified_by == "tags":  
        tags = Tag.objects.all
        tag = get_object_or_404( Tag, slug=class_slug )
    elif classified_by == "topics":
        topics = Topic.objects.all
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')

    
    versions = []
    arts = article.header.articledetails_set.all()

    related_tags = mc.get('related_tags_' + str(article_slug))
    if not related_tags:
         related_tags = article.header.tags.all()
         mc.set('related_tags_' + str(article_slug), related_tags, settings.MEMCACHED_TIMEOUT)

    if comment_no != None:
        feedbacks = Feedback.objects.filter(id = comment_no)
        children = len(feedbacks[0].get_children())
        template_context = {'children':children,'just_comment':True,'topic_page':True,'prev':prev,'next':next,'arts':arts,'request':request, 'related_tags':related_tags,'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'topics':topics,'topic':topic}

    if comment_no == None:
        top_ranked_count = 3

        top_ranked = Feedback.objects.top_ranked(article.id, top_ranked_count)

        if order_by == "latest" or order_by == "def":
            feedbacks = Feedback.objects.feedback_list(article.id, 'latest', 0)
        elif order_by == "order":
            feedbacks = Feedback.objects.feedback_list(article.id, 'order', top_ranked_count)

        paginator = Paginator(feedbacks, settings.paginator) 
        page = request.GET.get('page')

        voted_fb = []
        voted_suggestion = []
        poll_selection = []

        suggestions = mc.get('suggestions' + str(article.id))
        if not suggestions:
            suggestions = article.get_suggestions()
            mc.set('suggestions' + str(article.id), suggestions, settings.MEMCACHED_TIMEOUT)

        if user:
            voted_fb = mc.get('voted_fb_' + str(article.id) + '-' + str(user.id))
            if not voted_fb:
                 voted_fb = Rating.objects.filter(articledetails_id = article.id, user = user)
                 mc.set('voted_fb_' + str(article.id) + '-' + str(user.id), voted_fb, settings.MEMCACHED_TIMEOUT)
      
            voted_suggestion = mc.get('voted_suggestion_'+ str(user.id))
            
            if not voted_suggestion:
                voted_suggestion = []
                for suggestion in suggestions:
                    votes = SuggestionVotes.objects.filter(suggestions_id = suggestion.id, user = user)
                    for vote in votes:
                        voted_suggestion.append(vote)
                mc.set('voted_suggestion_'+ str(user.id), voted_suggestion, settings.MEMCACHED_TIMEOUT)
            poll_selection = mc.get('poll_selection_'+ str(user.id))
            if not poll_selection:
                poll_selection = PollResult.objects.filter(user_id = user.id)
                mc.set('poll_selection_'+ str(user.id), poll_selection, settings.MEMCACHED_TIMEOUT)

        article_rate = None
        for art in voted_suggestion:
            if art.vote == True:
                article_rate = 1
            else:
                article_rate = -1

        try:
            feedbacks = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            feedbacks = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            feedbacks = paginator.page(paginator.num_pages)
        if request.user.is_staff:
            tfidfs = tfidf.get_article_tfidf(article.id)
        else:
            tfidfs = {}
        tfidfs = tfidfs.items()
        if classified_by == "tags":  
            template_context = {'tfidfs':tfidfs,'suggestions':suggestions,'poll_selection':poll_selection,'prev':prev,'next':next,'arts':arts,'voted_suggestions':voted_suggestion, 'article_rate':article_rate,'order_by':order_by,'voted_fb':voted_fb,'top_ranked':top_ranked,'request':request, 'related_tags':related_tags,'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'tags':tags,'tag':tag}
        elif classified_by == "topics":
            template_context = {'tfidfs':tfidfs,'suggestions':suggestions,'poll_selection':poll_selection,'prev':prev,'next':next,'arts':arts,'voted_suggestions':voted_suggestion, 'article_rate':article_rate,'order_by':order_by,'voted_fb':voted_fb,'top_ranked':top_ranked,'request':request, 'related_tags':related_tags,'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'topics':topics,'topic':topic}      

    return render_to_response('article.html',template_context ,RequestContext(request))

def article_summarization(request, classified_by, class_slug, article_slug, order_by="def", comment_no=None):
    user = None

    login(request)

    if request.user.is_authenticated():
      user = request.user

    article = mc.get('article_' + str(article_slug))
    if not article:
         article = ArticleHeader.objects.get_article(article_slug)
         mc.set('article_' + str(article_slug), article, settings.MEMCACHED_TIMEOUT)

    topic = get_object_or_404( Topic, slug = article.topic_slug )

    next = ArticleHeader.objects.get_next(article.topic_id, article.order)
    prev = ArticleHeader.objects.get_prev(article.topic_id, article.order)

    if classified_by == "tags":  
        tags = Tag.objects.all
        tag = get_object_or_404( Tag, slug=class_slug )
    elif classified_by == "topics":
        topics = Topic.objects.all
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')

    
    versions = []
    arts = article.header.articledetails_set.all()

    related_tags = mc.get('related_tags_' + str(article_slug))
    if not related_tags:
         related_tags = article.header.tags.all()
         mc.set('related_tags_' + str(article_slug), related_tags, settings.MEMCACHED_TIMEOUT)

    feedbacks = mc.get('article_summarized_feedbacks_' + str(article_slug))
    if not feedbacks:
        summarized_feedback = tfidf.get_summarized_feedback_ids(article.id)
        feedbacks = Feedback.objects.summerized_feedback_list(article.id, 'latest',summarized_feedback[0])
        similar_feedbacks = summarized_feedback[1]
        avg_likes_dislikes_count = []
        for record in similar_feedbacks:
            if len(record[1]) > 0:
                ids = str(record[1]).strip('[]')+','+str(record[0])
            else:
                ids = str(record[0])
            avg_likes_dislikes_count.append([record[0],Feedback.objects.get_avg_likes_dislikes_count(ids)])
        for ele in avg_likes_dislikes_count:
            for feedback in feedbacks:
                if ele[0] == feedback.id:
                    feedback.likes = ele[1][0]
                    feedback.dislikes = ele[1][1]
                    feedback.no_similaar_feedbacks = ele[1][2]
                    break

        mc.set('article_summarized_feedbacks_' + str(article_slug), feedbacks, settings.MEMCACHED_TIMEOUT)
    feedback_count = len(feedbacks)
    voted_fb = []
    voted_suggestion = []
    poll_selection = []

    suggestions = mc.get('suggestions' + str(article.id))
    if not suggestions:
        suggestions = article.get_suggestions()
        mc.set('suggestions' + str(article.id), suggestions, settings.MEMCACHED_TIMEOUT)


    voted_fb = mc.get('voted_fb_' + str(article.id) + '-' + str(user.id))
    if not voted_fb:
         voted_fb = Rating.objects.filter(articledetails_id = article.id, user = user)
         mc.set('voted_fb_' + str(article.id) + '-' + str(user.id), voted_fb, settings.MEMCACHED_TIMEOUT)


    tfidfs = tfidf.get_article_tfidf(article.id)
    tfidfs = tfidfs.items()


    template_context = {'feedback_count':feedback_count,'summarized':True,'tfidfs':tfidfs,'suggestions':suggestions,'poll_selection':poll_selection,'prev':prev,'next':next,'arts':arts,'voted_suggestions':voted_suggestion,'order_by':order_by,'voted_fb':voted_fb,'request':request, 'related_tags':related_tags,'feedbacks':feedbacks,'article': article,'user':user,'settings': settings,'topics':topics,'topic':topic}      

    return render_to_response('article.html',template_context ,RequestContext(request))

def article_diff(request, article_slug):
    
    user = None
    login(request)

    if request.user.is_authenticated():
      user = request.user

    lDiffClass = diff_match_patch()

    topics = Topic.objects.all

    article = get_object_or_404( ArticleDetails, slug=article_slug )
    tmp_versions = article.header.articledetails_set.all().order_by('id')

    previous = ''
    versions = []
    for temp in tmp_versions:
        article_info = {}

        article_info['current'] = temp.current
        article_info['name'] = temp.header.name
        article_info['slug'] = temp.slug
        article_info['date'] = temp.mod_date
        article_info['topic_absolute_url'] = temp.header.topic.get_absolute_url

        if previous == "":
           article_info['text'] = previous = temp.summary.raw
        else:
           lDiffs = lDiffClass.diff_main(previous, temp.summary.raw)
           lDiffClass.diff_cleanupSemantic(lDiffs)
           lDiffHtml = lDiffClass.diff_prettyHtml(lDiffs)
           article_info['text'] = lDiffHtml

        versions.append(article_info)

    template_context = {'article': article, 'topics':topics, 'topic':article.header.topic, 'versions': versions, 'request':request, 'user':user,'settings': settings}
    return render_to_response('article_diff.html',template_context ,RequestContext(request))

def rename_articles(request):
    if request.user.is_superuser:
        all_art = ArticleDetails.objects.filter(current = True)
        headers = []
        temp = {}
        for art in all_art:
            temp = {'header':art.header, 'topic_order':art.header.topic.order, 'order':art.header.order}
            headers.append(temp)

        headers = sorted(headers, key=lambda header: (header['topic_order'], header['order']))

        for idx,val in enumerate(headers):
            val['header'].name = "مادة ("+str(idx+1)+")"
            val['header'].order = idx
            val['header'].save()

        text = "done!"
    else:
        text = "you don't have permission"

    return render_to_response('operation.html',{'text':text} ,RequestContext(request))

def suggestion_vote(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            suggestion =  request.POST.get("suggestion")
            article =  request.POST.get("article")
            user =  request.user

            vote = False
            
            if request.POST.get("type") == "1" :
              vote = True

            art = Suggestion.objects.get(id = suggestion)

            p = art.likes
            n = art.dislikes

            record = SuggestionVotes.objects.filter(suggestions_id = suggestion, user = user )
            
            if record:
                if record[0].vote != vote:
                    if vote == True:
                      p += 1
                      n -= 1
                    else:
                      n += 1
                      p -= 1
                record[0].vote = vote
                record[0].save()
            else:
                SuggestionVotes(user = user, vote = vote,suggestions_id = suggestion).save()
                if vote == True:
                  p += 1
                else:
                  n += 1

            art.likes = p
            art.dislikes = n
            art.save()
            mc.delete('suggestions' + str(article))
            mc.delete('voted_suggestion_'+ str(user.id))

            return HttpResponse(simplejson.dumps({'suggestion':suggestion,'p':p,'n':n,'vote':request.POST.get("type")}))

def poll_select(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            option_id = request.POST.get("option_id")
            state = request.POST.get("state")
            user_id =  request.user.id

            option = PollOptions.objects.get(id = option_id)
            record = PollResult.objects.filter(option_id = option_id, user_id = user_id)
            suggestion = Suggestion.objects.get(id = option.suggestions_id)

            if not record:
                PollResult(option_id = option_id, user_id = user_id).save()
                option.count += 1
                suggestion.poll_total_count += 1
            else:
                record[0].delete()
                option.count -=1
                suggestion.poll_total_count -= 1
            
            suggestion.save()
            option.save()
            mc.delete('poll_selection_'+ str(user_id))

    return HttpResponse(simplejson.dumps({'option_id':option_id,'count':option.count}))