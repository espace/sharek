from django import template
register = template.Library()

def key(d, key_name):
    if d.__contains__(key_name):
      return d[key_name]
    else:
      return 0

def vote(voted, key_name):
  for comment_vote in voted:
    if comment_vote.feedback_id == key_name:
      if comment_vote.vote == True:
        return 1
      else:
        return -1

  return 0

def vote_sug(voted, key_name):
  for sug_vote in voted:
    if sug_vote.suggestions_id == key_name:
      if sug_vote.vote == True:
        return 1
      else:
        return -1
  return 0  

def linebreak(summary, replace_text):
    return summary.replace('\n', replace_text)

key = register.filter('key', key)
linebreak = register.filter('linebreak', linebreak)
vote = register.filter('vote', vote)
vote_sug = register.filter('vote_sug', vote_sug)
