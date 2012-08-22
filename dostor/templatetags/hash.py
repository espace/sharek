from django import template
register = template.Library()

def key(d, key_name):
    if d.__contains__(key_name):
      return d[key_name]
    else:
      return 0

def vote(voted, key_name):
  for comment_vote in voted:
    print "ana hnaaaaaaaaaaaaaaaa"
    print comment_vote.feedback_id
    print key_name
    print "5alasssssssssssssssssss"
    if comment_vote.feedback_id == key_name:
      return comment_vote.vote

  return 0

key = register.filter('key', key)
vote = register.filter('vote', vote)