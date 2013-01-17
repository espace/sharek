from core.models import Feedback, article_idf
import core.analysis.preprocessing as pre
from django.db import connection
import math
import collections

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts  import render_to_response, get_object_or_404, redirect

def get_cleaned_suggestions(id):
  query = '''SELECT distinct id,suggestion from core_feedback where parent_id is NULL and articledetails_id = %s'''
  cursor = connection.cursor()
  cursor.execute(query, [id])
  suggestions = cursor.fetchall()
  cleaned = pre.stammer(suggestions)
  return cleaned

def unique_words(strings):
  words = collections.Counter()
  for string in strings:
    words.update(string[1].split())
  return dict(words)

def idf(request):
  query ='''SELECT distinct articledetails_id from core_feedback order by 1'''
  cursor = connection.cursor()
  cursor.execute(query)
  ids = cursor.fetchall()

  for id in ids:
    cleaned = get_cleaned_suggestions(id[0])
    words = unique_words(cleaned)
    compute_idf(id[0], words, cleaned)
  return render_to_response('operation.html',{'text':"done isA"} ,RequestContext(request))

def compute_idf(id , words, cleaned):
  for word in words.keys():
    counter = 0
    for string in cleaned:
      if word in string.split():
        counter +=1
    article_idf(articledetail_id = id , term = word, idf = math.log10(len(cleaned)/(counter*1.0))).save()

def compute_tfidf(request):
  #query ='''SELECT distinct articledetails_id from core_feedback order by 1'''
  '''cursor = connection.cursor()
  cursor.execute(query)
  ids = cursor.fetchall()'''
  ids = [[208]]
  tfidfs = []
  for id in ids:
    #retrive the idf of words article
    idf = retrive_idf(id[0])
    cleaned = get_cleaned_suggestions(id[0])
    for suggestion_vector in cleaned:
      #compute tf of suggestion
      words = collections.Counter()
      words.update(suggestion_vector[1].split())
      maximum = max(max(values) if hasattr(values,'__iter__') else values for values in dict(words).values())
      d1 = dict(words)
      tf = dict((k, float(d1[k]) / maximum) for k in d1)
      #compute tfidf
      tfidf = dict((k, float(tf[k]) * idf[k]) for k in tf)
      tfidfs.append([suggestion_vector[0],tfidf])
    #summerize the suggestions
    summerized = summerize(tfidfs)
    summerized_ids = []
    for vector in summerized:
      summerized_ids.append(vector[0])

    query ='''SELECT suggestion from core_feedback where id in %s'''
    cursor = connection.cursor()
    cursor.execute(query, [summerized_ids])
    suggestions = cursor.fetchall()

    text_file = open("write_it.txt", "w")
    for index, suggestion in enumerate(suggestions):
      text_file.write(index + "- \t"+ suggestion[0]+"\n\n")
    text_file.close()

  return render_to_response('operation.html',{'text':"done isA"} ,RequestContext(request))

def retrive_idf(article_id):
  query ='''SELECT term, idf from core_article_idf where articledetail_id = %s'''
  cursor = connection.cursor()
  cursor.execute(query, [article_id])
  temp = cursor.fetchall()
  terms = {}
  for term in temp:
    terms[temp[0]] = temp[1]
  return terms

#summerize the suggestions accrding to cosien similarity
def summerize(tfidfs):
  print "summerization ...."
  for index, v1 in enumerate(tfidfs):
    print index
    for active, v2 in enumerate(tfidfs[index+1:]):
      only_v1 = set(v1[1].keys()) - set(v2[1].keys())
      only_v2 = set(v2[1].keys()) - set(v1[1].keys())
      for term in only_v1:
        v2[1][term] = 0
      for term in only_v2:
        v1[1][term] = 0
      t1 = {}
      t2 = {}

      for key in sorted(v1[1].iterkeys()):
        t1[key] = v1[1][key]
      for key in sorted(v2[1].iterkeys()):
        t2[key] = v2[1][key]

      ''' Compute the Cosine similarity of two victors
        law:  t1 * t2 / |t1|*|t2| '''
      similarity = np.dot(t1,t2)/(np.linalg.norm(t1)*np.linalg.norm(t2))
      #TODO : save index and return them to return the full suggesion 
      if similarity > 0.7:
        del tfidfs[active]
  return tfidfs


      



