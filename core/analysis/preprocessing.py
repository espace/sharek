# This Python file uses the following encoding: utf-8

import re
import collections
import numpy as np

#from core.views import mc
import memcache
from sharek import settings
mc = memcache.Client([settings.MEMCACHED_BACKEND])

def remove_stop_words(string,stop_words):
  temp = ""
  for word in string.split():
    if not word in stop_words.keys():
      temp += word.strip() + " "
  return temp


def load_stop_words():
  stop_words = mc.get('stop_words')
  if not stop_words:
    ins = open('stopwords.txt').read().splitlines()
    stop_words = {}
    for line in ins:
        stop_words[line.decode('utf-8')] = True
    mc.set('stop_words', stop_words, settings.MEMCACHED_TIMEOUT)
  return stop_words

def stammer(strings):
  stop_words = load_stop_words()
  #myFile = open(name+'.py', 'w')
  cleaned = []
  for string in strings:
    clean = remove_stop_words(string[1],stop_words)
    clean  = remove_punctuations(clean)
    splitted = clean.split()
    word = ""
    temp = ""
    for word in splitted:
    #postfixes
      if re.match(".*كما$",word) and len(word) >10: word = re.sub("كما$","",word)
      if re.match(".*هما$",word) and len(word) >10: word = re.sub("هما$","",word)
      if re.match(".*كن$",word) and len(word) >10: word = re.sub("كن$","",word)
      if re.match(".*هن$",word) and len(word) >10: word = re.sub("هن$","",word)
      if re.match(".*تي$",word) and len(word) >10: word = re.sub("تي$","",word)
      if re.match(".*ها$",word) and len(word) >8: word = re.sub("ها$","",word)
      if re.match(".*نا$",word) and len(word) >8: word = re.sub("نا$","",word)
      if re.match(".*كم$",word) and len(word) >8: word = re.sub("هم$","",word)
      if re.match(".*كم$",word) and len(word) >8: word = re.sub("كم$","",word)
      if re.match(".*تما$",word) and len(word) >10: word = re.sub("تما$","",word)
      if re.match(".*ون$",word) and len(word) >10: word = re.sub("ون$","",word)
      if re.match(".*تين$",word) and len(word) >10: word = re.sub("تين$","",word)
      if re.match(".*تان$",word) and len(word) >10: word = re.sub("تان$","",word)
      if re.match(".*ات$",word) and len(word) >10: word = re.sub("ات$","",word)
      if re.match(".*ان$",word) and len(word) >10: word = re.sub("ان$","",word)
      if re.match(".*ين$",word) and len(word) >10: word = re.sub("ين$","",word)
      if re.match(".*وا$",word) and len(word) >10: word = re.sub("وا$","",word)
      if re.match(".*تا$",word) and len(word) >10: word = re.sub("تا$","",word)
      if re.match(".*تم$",word) and len(word) >10: word = re.sub("تم$","",word)
      if re.match(".*تن$",word) and len(word) >10: word = re.sub("تن$","",word)
      if re.match(".*نا$",word) and len(word) >10: word = re.sub("ان$","",word)
    #prefixes
      if re.match("^وبال",word): word = re.sub("^وبال","",word)
      if re.match("^وال",word): word = re.sub("^وال","",word)
      if re.match("^بال",word): word = re.sub("^بال","",word)
      if re.match("^فال",word): word = re.sub("^فال","",word)
      if re.match("^ولل",word): word = re.sub("^ولل","",word)
      if re.match("^ال",word) and len(word) > 8: word = re.sub("^ال","",word)
      if re.match("^وب",word): word = re.sub("^وب","",word)
      if re.match("^ول",word): word = re.sub("^ول","",word)
      if re.match("^لل",word): word = re.sub("^لل","",word)
      if re.match("^فس",word): word = re.sub("^فس","",word)
      if re.match("^فب",word): word = re.sub("^فب","",word)
      if re.match("^فل",word): word = re.sub("^فل","",word)
      if re.match("^وس",word): word = re.sub("^وس","",word)
      if re.match("^كال",word): word = re.sub("^كال","",word)
      temp += word + " "
    # cleaned array of [ suggestion_id, suggestion_cleaned_text ]
    if len(temp)>0:cleaned.append([string[0],temp])
  return cleaned

def remove_punctuations(string):
  string = string.replace(',',' ')
  string = string.replace('.',' ')
  string = string.replace('\"',' ')
  string = string.replace("'",' ')
  string = string.replace(';',' ')
  string = string.replace(':',' ')
  string = string.replace('\\',' ')
  string = string.replace('/',' ')
  string = string.replace('_',' ')
  string = string.replace('*',' ')
  string = string.replace('!',' ')
  string = string.replace('@',' ')
  string = string.replace('#',' ')
  string = string.replace('$',' ')
  string = string.replace('&',' ')
  string = string.replace('(',' ')
  string = string.replace(')',' ')
  string = string.replace('[',' ')
  string = string.replace(']',' ')
  string = string.replace('{',' ')
  string = string.replace('}',' ')
  string = string.replace('+',' ')
  string = string.replace('-',' ')
  string = string.replace('?',' ')
  string = string.replace('~',' ')
  string = string.replace('؟'.decode('utf-8'),' ')
  string = string.replace('،'.decode('utf-8'),' ')
  return string

def unique_words(string):
  words = collections.Counter()
  words.update(string.split())
  return list(words)