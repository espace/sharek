from django import template
from django.template.loader import get_template
from django.conf import settings

import tokenize
import StringIO

register = template.Library()

class CallNode(template.Node):
   def __init__(self, template_name, *args, **kwargs):
       self.template_name = template_name
       self.args = args
       self.kwargs = kwargs

   def render(self, context):
       try:
           template_name = self.template_name.resolve(context)
           t = get_template(template_name)
           d = {}
           args = d['args'] = []
           kwargs = d['kwargs'] = {}
           for i in self.args:
               args.append(i.resolve(context))
           for key, value in self.kwargs.items():
               kwargs[key] = d[key] = value.resolve(context)

           context.update(d)
           result = t.render(context)
           context.pop()
           return result
       except:
           if settings.TEMPLATE_DEBUG:
              raise
           return ''

def do_call(parser, token):
   """
   Loads a template and renders it with the current context.

   Example::

       {% call "foo/some_include" %}
       {% call "foo/some_include" with arg1 arg2 ... argn %}
   """
   bits = token.contents.split()
   if 'with' in bits: #has 'with' key
       pos = bits.index('with')
       argslist = bits[pos+1:]
       bits = bits[:pos]
   else:
       argslist = []
   if len(bits) != 2:
       raise template.TemplateSyntaxError, "%r tag takes one argument: the name of the template to be included" % bits[0]
   path = parser.compile_filter(bits[1])
   if argslist:
       args = []
       kwargs = {}
       for i in argslist:
           if '=' in i:
               a, b = i.split('=', 1)
               a = a.strip()
               b = b.strip()
               buf = StringIO.StringIO(a)
               keys = list(tokenize.generate_tokens(buf.readline))
               if keys[0][0] == tokenize.NAME:
                   kwargs[a] = parser.compile_filter(b)
               else:
                   raise template.TemplateSyntaxError, "Argument syntax wrong: should be key=value"
           else:
               args.append(parser.compile_filter(i))
   return CallNode(path, *args, **kwargs)

register.tag('call', do_call)