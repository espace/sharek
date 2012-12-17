# This Python file uses the following encoding: utf-8
from sharek import settings

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect

from core.models import ArticleDetails, ArticleRating, Feedback, Rating

def latest_comments(request):

    user = None
    if request.user.is_authenticated():
      user = request.user

    if request.method == 'POST':
        page =  request.POST.get("page")
        article =  request.POST.get("article")
        order_by =  request.POST.get("order_by")

        offset = settings.paginator * int(page)
        limit = settings.paginator

        obj_article = get_object_or_404( ArticleDetails, id=article )
        topic = obj_article.header.topic
        top_ranked_count = 3

        if order_by == "latest" or order_by == "def":
             feedbacks = Feedback.objects.feedback_list(obj_article.id, 'latest', top_ranked_count)
        elif order_by == "order":
             feedbacks = Feedback.objects.feedback_list(obj_article.id, 'order', top_ranked_count)

        voted_fb = Rating.objects.filter(articledetails_id = obj_article.id, user = user)
        voted_article = ArticleRating.objects.filter(articledetails_id = obj_article.id, user = user)

        paginator = Paginator(feedbacks, settings.paginator)
        try:
            feedbacks = paginator.page(page)
            return render_to_response('include/latest_comments.html',{'topic':topic,'settings': settings,'voted_fb':voted_fb,'voted_articles':voted_article,'feedbacks':feedbacks,'article':obj_article,'page':page} ,RequestContext(request))
        except PageNotAnInteger:
            return HttpResponse('')
        except EmptyPage:
            return HttpResponse('')

def remove_feedback(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            feedback_id = request.POST.get("feedback")
            feedback = Feedback.objects.get(id=feedback_id)
            replys = Feedback.objects.filter(parent_id = request.POST.get("feedback"))
            reply_ids = []
            for reply in replys:
                reply_ids.append(reply.id)
            #the user has to be the feedback owner to be able to remove it
            if feedback.user == request.user.username or request.user.is_staff:
                feedback.articledetails.feedback_count = feedback.articledetails.feedback_count - 1
                feedback.articledetails.save()
                feedback.delete()
                return HttpResponse(simplejson.dumps({'feedback_id':request.POST.get("feedback"),'reply_ids':reply_ids}))

def modify(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            sug = str(request.POST.get("suggestion").encode('utf-8'))
            article = get_object_or_404( ArticleDetails, id=request.POST.get("article"))
            feedbacks = Feedback.objects.filter(articledetails_id = request.POST.get("article"), email= request.POST.get("email"), name = request.POST.get("name"))
            for feedback in feedbacks:
                if feedback.suggestion.raw.encode('utf-8') == sug:
                    return HttpResponse(simplejson.dumps({'duplicate':True,'name':request.POST.get("name")}))

            Feedback(user = request.POST.get("user_id"),articledetails_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email = request.POST.get("email"), name = request.POST.get("name")).save()
            feedback = Feedback.objects.filter(articledetails_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.POST.get("email"), name = request.POST.get("name"))
            article.feedback_count = article.feedback_count + 1
            article.save()
                    
            if request.user.username != "admin":
                # post on twitter or facebook
                if UserSocialAuth.auth_provider(request.user.username) == 'facebook':
                    extra_data = UserSocialAuth.get_extra_data(request.user.username)
                    access_token = extra_data['access_token']
                 # GraphAPI is the main class from facebook_sdp.py
                    art = get_object_or_404(ArticleDetails, id=request.POST.get("article"))
                    art_name = art.header.name.encode('utf-8')
                    art_body = art.summary.raw.encode('utf-8')
                    graph = facebook_sdk.GraphAPI(access_token)
                    attachment = {}
                    attachment['name'] = art_name
                    attachment['link'] = shorten_url(settings.domain+"sharek/"+request.POST.get("class_slug")+"/"+request.POST.get("article_slug")+"/comment/"+str(feedback[0].id)+"/")
                    attachment['picture'] = settings.domain + settings.STATIC_URL + "images/facebook-thumb.jpg"
                    attachment['description'] = art_body
                    message = 'لقد شاركت في كتابة #دستور_مصر وقمت بالتعليق على '+art_name+" من الدستور"
                    graph.put_wall_post(message, attachment)
            
                if UserSocialAuth.auth_provider(request.user.username) == 'twitter':
                    extra_data = UserSocialAuth.get_extra_data(request.user.username)
                    access_token = extra_data['access_token']
                    access_token_secret = access_token[access_token.find('=')+1 : access_token.find('&')]
                    access_token_key = access_token[access_token.rfind('=')+1:]
                    api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                                      consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                                      access_token_key=access_token_key,
                                      access_token_secret=access_token_secret)
                    link = shorten_url(settings.domain+"sharek/"+request.POST.get("class_slug")+"/"+request.POST.get("article_slug")+"/comment/"+str(feedback[0].id)+"/")
                    message = 'لقد شاركت في كتابة #دستور_مصر بالتعليق على '+get_object_or_404(ArticleDetails, id=request.POST.get("article")).header.name.encode('utf-8')+"  "+link
                    api.PostUpdate(message)

                    
            return HttpResponse(simplejson.dumps({'date':str(feedback[0].date),'id':feedback[0].id ,'suggestion':request.POST.get("suggestion")}))

def reply_feedback(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            sug = str(request.POST.get("suggestion").encode('utf-8'))
            feedbacks = Feedback.objects.filter(articledetails_id = request.POST.get("article"), email= request.POST.get("email"), name = request.POST.get("name"))
            for feedback in feedbacks:
                if feedback.suggestion.raw.encode('utf-8') == sug:
                    return HttpResponse(simplejson.dumps({'duplicate':True,'name':request.POST.get("name")}))
            Feedback(user = request.POST.get("user_id"),articledetails_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email = request.POST.get("email"), name = request.POST.get("name"), parent_id = request.POST.get("parent")).save()
            reply = Feedback.objects.filter(user = request.POST.get("user_id"),articledetails_id = request.POST.get("article"),suggestion = request.POST.get("suggestion") , email= request.POST.get("email"), name = request.POST.get("name"), parent_id= request.POST.get("parent"))
            return HttpResponse(simplejson.dumps({'date':str(reply[0].date),'id':reply[0].id ,'suggestion':request.POST.get("suggestion"),'parent':request.POST.get("parent")}))

def vote(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            feedback =  request.POST.get("modification")
            article =  request.POST.get("article")
            user =  request.user

            record = Rating.objects.filter(feedback_id = feedback, user = user )

            vote = False
            if request.POST.get("type") == "1" :
              vote = True
            
            mod = Feedback.objects.get(id=feedback)

            p = mod.likes
            n = mod.dislikes
            
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
                Rating(user = user, vote = vote, feedback_id = feedback,articledetails_id = request.POST.get("article")).save()
                if vote == True:
                  p += 1
                else:
                  n += 1

            mod.likes = p
            mod.dislikes = n
            mod.order = mod.likes - mod.dislikes
            mod.save()

            mc.delete('voted_fb_' + str(article) + '-' + str(user.id))
            return HttpResponse(simplejson.dumps({'modification':request.POST.get("modification"),'p':p,'n':n,'vote':request.POST.get("type")}))