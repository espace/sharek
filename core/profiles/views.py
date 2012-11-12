import sys
import os
import core
import os.path
import subprocess

from core.profiles.models import *
from django.core.urlresolvers import reverse
from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts  import render_to_response, get_object_or_404, redirect

from core.models import ArticleRating, ArticleDetails, Feedback, User

from sharek import settings

def user_profile(request):
    return render_to_response('user-profile.html', {} ,RequestContext(request))

def profile(request, browsing_data="def"):
    #browsing_data will represent the type of data the user want to see " likes, dislikes ,or comments"

    user = None
    if request.user.is_authenticated():
      user = request.user
    else:
      return HttpResponseRedirect(reverse('index'))

    ids = []
    liked_articles = []
    disliked_articles = []
    commented_articles = []

    commented_ids = Feedback.objects.filter(user = user,parent_id = None).values('articledetails').distinct()

    contributions = commented_ids.count

    voted_articles = ArticleRating.objects.filter(user = user)

    if browsing_data == "likes" or browsing_data == "def":
        liked_articles = User.profile_likes(user.username)

    elif browsing_data == "dislikes":
        disliked_articles = User.profile_dislikes(user.username)

    elif browsing_data == "comments":
        for id in commented_ids:
            if id['articledetails'] != None:
                temp = ArticleDetails.objects.get(id = id['articledetails'])
                feedbacks = Feedback.objects.filter(articledetails_id = id['articledetails'], parent_id = None, user = user)
                commented_articles.append({'topic':temp.header.topic,'name':temp.header.name,'slug':temp.slug,'feedbacks':feedbacks})
                

    return render_to_response('profile.html', {'voted_articles': voted_articles, 'contributions': contributions, 'profile':True,'browsing_data':browsing_data,'commented_articles':commented_articles,'disliked_articles':disliked_articles,'liked_articles':liked_articles,'settings': settings,'user':user} ,RequestContext(request))
