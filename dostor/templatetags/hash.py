from django import template
register = template.Library()

def key(d, key_name):
    if d.__contains__(key_name):
      return d[key_name]
    else:
      return 0
    
key = register.filter('key', key)
