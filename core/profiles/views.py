import sys
import os
import core
import os.path
import subprocess

from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts  import render_to_response, get_object_or_404, redirect

from core.models import ArticleRating, ArticleDetails, Feedback

from sharek import settings

def user_profile(request):
    return render_to_response('user-profile.html', {} ,RequestContext(request))

def profile(request, browsing_data="def"):
    #browsing_data will represent the type of data the user want to see " likes, dislikes ,or comments"
    user = None
    if request.user.is_authenticated():
      user = request.user
    ids = []
    liked_articles = []
    disliked_articles = []
    commented_articles = []
    if browsing_data == "likes" or browsing_data == "def":
        liked_ids = ArticleRating.objects.filter(vote = True, user = user).values('articledetails').distinct()
        for id in liked_ids:
            ids.append(id['articledetails'])
        liked_articles = ArticleDetails.objects.filter(id__in=ids)
    elif browsing_data == "dislikes":
        disliked_ids = ArticleRating.objects.filter(vote = False, user = user).values('articledetails').distinct()
        for id in disliked_ids:
            ids.append(id['articledetails'])
        disliked_articles = ArticleDetails.objects.filter(id__in=ids)
        for article in disliked_articles:
            article['original_slug'] = 'test'
    elif browsing_data == "comments":
        commented_ids = Feedback.objects.filter(user = user,parent_id = None).values('articledetails').distinct()
        for id in commented_ids:
            if id['articledetails'] != None:
                temp = ArticleDetails.objects.get(id = id['articledetails'])
                feedbacks = Feedback.objects.filter(articledetails_id = id['articledetails'], parent_id = None, user = user)
                commented_articles.append({'topic':temp.header.topic,'name':temp.header.name,'url':"#",'feedbacks':feedbacks})
                

    return render_to_response('profile.html', {'profile':True,'browsing_data':browsing_data,'commented_articles':commented_articles,'disliked_articles':disliked_articles,'liked_articles':liked_articles,'settings': settings,'user':user} ,RequestContext(request))
