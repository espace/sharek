# This Python file uses the following encoding: utf-8
from sharek import settings
from core.models import Feedback, article_idf, article_analysis
import core.analysis.preprocessing as pre
from django.db import connection
import math
import collections
from collections import defaultdict
import numpy as np
from copy import copy, deepcopy

from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from core.views import mc


                        ########################### Utilities ###########################
# get the last comment id now
def get_last_comment_id(article_id):
  query = ''' SELECT MAX(id) from core_feedback where parent_id is NULL and articledetails_id = %s '''
  cursor = connection.cursor()
  cursor.execute(query, [article_id])
  last_comment_id = cursor.fetchone()

  return last_comment_id[0]


# get the last comment id from last run of idf computing
def get_last_run_comment_id(article_id):
  query = ''' SELECT last_comment_id from core_article_analysis where articledetail_id = %s '''
  cursor = connection.cursor()
  cursor.execute(query, [article_id])
  data = cursor.fetchone()
  if data:
    last_run_comment_id = data[0]
  else:
    last_run_comment_id = 0 #first time to do the idf on this article

  return last_run_comment_id

def unique_words(strings):
  words = defaultdict(int)
  for string in strings:
    items = string
    for item in items:
      words[item]+=1
  words = words.items()
  return dict(words)

def get_cleaned_suggestions_for_idf(id):
  query = '''SELECT distinct id,suggestion from core_feedback where parent_id is NULL and articledetails_id = %s and id > %s'''
  cursor = connection.cursor()
  last_run_comment_id = get_last_run_comment_id(id)
  cursor.execute(query, [id, last_run_comment_id])
  suggestions = cursor.fetchall()
  cleaned = pre.stammer(suggestions)

  cleaned_comments = article_analysis.objects.filter(articledetail_id = id)
  if cleaned_comments:
    cleaned_comments[0].no_of_cleaned_comment = len(cleaned) + cleaned_comments[0].no_of_cleaned_comment
    cleaned_comments[0].save()
  else:
    article_analysis(articledetail_id = id, no_of_cleaned_comment = len(cleaned)).save()
  return cleaned


def get_cleaned_suggestions(id):
  query = '''SELECT id,suggestion from core_feedback where parent_id is NULL and articledetails_id = %s order by id'''
  cursor = connection.cursor()
  cursor.execute(query, [id])
  suggestions = cursor.fetchall()
  cleaned = pre.stammer(suggestions)

  cleaned_comments = article_analysis.objects.filter(articledetail_id = id)
  if cleaned_comments:
    cleaned_comments[0].no_of_cleaned_comment = len(cleaned) + cleaned_comments[0].no_of_cleaned_comment
    cleaned_comments[0].save()
  else:
    article_analysis(articledetail_id = id, no_of_cleaned_comment = len(cleaned)).save()
  return cleaned

                        ########################### Core Code ###########################

def idf(request):
  query ='''SELECT distinct articledetails_id from core_feedback order by 1'''
  cursor = connection.cursor()
  cursor.execute(query)
  ids = cursor.fetchall()

  for id in ids:
    cleaned = get_cleaned_suggestions_for_idf(id[0])
    words = unique_words(cleaned)
    last_comment_id = get_last_comment_id(id[0])

    compute_idf(id[0], words, cleaned, last_comment_id)
  return render_to_response('operation.html',{'text':"done isA"} ,RequestContext(request))

def compute_idf(id , words, cleaned, last_comment_id):
  for word in words.keys():
    counter = 0
    for string in cleaned:
      if word in string[1]:
        counter +=1

    last_comment = article_analysis.objects.get(articledetail_id = id)    
    last_comment.last_comment_id = last_comment_id
    last_comment.save()

    term_idf = article_idf.objects.filter(articledetail_id = id , term = word)
    if term_idf:
      term_idf[0].idf = math.log10(last_comment.no_of_cleaned_comment/((counter+term_idf[0].no_of_comments)*1.0))
      term_idf[0].no_of_comments = counter + term_idf[0].no_of_comments
      term_idf[0].save()
    else:
      article_idf(articledetail_id = id , term = word, idf = math.log10(last_comment.no_of_cleaned_comment/((counter)*1.0)), no_of_comments = counter).save()

def get_summarized_feedback_ids(article_id):

  tfidfs = []

  #retrive the idf of words article
  idf = retrive_idf(article_id)

  cleaned = get_cleaned_suggestions(article_id)
  for suggestion_vector in cleaned:
    #compute tf of suggestion
    #words = collections.Counter()
    #words.update(suggestion_vector[1].split())
    words = defaultdict(int)
    items = suggestion_vector[1].split()
    for item in items:
      words[item]+=1
    words = words.items()

    maximum = max(max(values) if hasattr(values,'__iter__') else values for values in dict(words).values())
    d1 = dict(words)
    tf = dict((k, float(d1[k]) / maximum) for k in d1)
    #compute tfidf
    tfidf = {}
    for term in tf.keys():
      tf_val = float(tf[term])
      idf_val = idf[term]
      tfidf[term] = tf_val * idf_val 
    #tfidf = dict((k, float(tf[k]) * idf[k]) for k in tf)
    tfidfs.append([suggestion_vector[0],tfidf])
  #summerize the suggestions
  summerized = summerize(tfidfs)
  summerized_ids ="" 
  for vector in summerized:
    summerized_ids+= str(vector[0])+","
  summerized_ids+= str(summerized[0][0])

  return summerized_ids

def retrive_idf(article_id):
  query ='''SELECT term, idf from core_article_idf where articledetail_id = %s'''
  cursor = connection.cursor()
  cursor.execute(query, [article_id])
  temp = cursor.fetchall()
  terms = {}
  for term in temp:
    terms[term[0]] = term[1]
  return terms


def get_article_tfidf(article):
  #if request.method == 'GET':
  article_id =  article 
  tfidf = mc.get('article_cloud_'+str(article_id))
  if not tfidf:
    idf = retrive_idf(article_id)
    cleaned = get_cleaned_suggestions(article_id)
    tfidf = {}
    for suggestion_vector in cleaned:
      #compute tf of suggestion
      #words = collections.Counter()
      #words.update(suggestion_vector[1].split())
      words = defaultdict(int)
      items = suggestion_vector[1].split()
      for item in items:
        words[item]+=1
      words = words.items()
      maximum = max(max(values) if hasattr(values,'__iter__') else values for values in dict(words).values())
      d1 = dict(words)
      tf = dict((k, float(d1[k]) / maximum) for k in d1)
      #compute tfidf
      for term in tf.keys():
        tf_val = float(tf[term])
        idf_val = idf[term]
        try:
          tfidf[term] = tfidf[term] + (tf_val * idf_val)
        except: 
          tfidf[term] = tf_val * idf_val
    # get the max tfidf value to normalize
    maximum = max(max(values) if hasattr(values,'__iter__') else values for values in tfidf.values())
    # normalize the tfidf
    tfidf = dict((k, float(tfidf[k]) / maximum) for k in tfidf)
    # clear the tfidf range
    tfidf = dict((k, float(tfidf[k]) * 100) for k in tfidf)
    # get the top 100
    tfidf = dict(sorted(tfidf.items(), key=lambda x: x[1],reverse=True)[:100])
    mc.set('article_cloud_' + str(article_id), tfidf, settings.MEMCACHED_TIMEOUT)
  return tfidf

#summerize the suggestions accrding to cosien similarity
def summerize(tfidfs):
  similar_feedbacks = []
  for ele in tfidfs:
    print ele[0]
  for index, v1 in enumerate(tfidfs):
    if not v1 == "-":        
      similar_feedbacks.append([v1[0],[]])
      for active, v2 in enumerate(tfidfs[index+1:]):
        if not v2 == "-":
          org_v1 = deepcopy(v1)
          only_v1 = set(org_v1[1].keys()) - set(v2[1].keys())
          only_v2 = set(v2[1].keys()) - set(org_v1[1].keys())
          for term in only_v1:
            v2[1][term] = 0
          for term in only_v2:
            org_v1[1][term] = 0
          t1 = []
          t2 = []

          for key in sorted(org_v1[1].iterkeys()):
            t1.append(org_v1[1][key])
          for key in sorted(v2[1].iterkeys()):
            t2.append(v2[1][key])

          ''' Compute the Cosine similarity of two victors
            law:  t1 * t2 / |t1|*|t2| '''
          similarity = np.dot(t1,t2)/(np.linalg.norm(t1)*np.linalg.norm(t2))
          #TODO : save index and return them to return the full suggesion 
          if similarity > 0.5:
            similar_feedbacks[-1][1].append(v2[0])
            tfidfs[active+index+1] = "-"
  print "%%%%%%%%%%%%%%%%%%%%%%%%%%%"
  for ele in similar_feedbacks:
    print ele
  print "%%%%%%%%%%%%%%%%%%%%%%%%%%%"
  summerized = []
  for vector in tfidfs:
    if not vector == "-":
      summerized.append(vector)
  return summerized


def recalculate_last_comment(request):
  query ='''SELECT distinct articledetails_id from core_feedback order by 1'''
  cursor = connection.cursor()
  cursor.execute(query)
  ids = cursor.fetchall()

  for id in ids:
    last_comment_id = get_last_comment_id(id[0])
    last_comment = article_analysis.objects.get(articledetail_id = id[0])    
    last_comment.last_comment_id = last_comment_id
    last_comment.save()

  return render_to_response('operation.html',{'text':"recalculate_last_comment done isA"} ,RequestContext(request))


