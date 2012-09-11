import re
from django import template
from django.template import Library, Node, TemplateSyntaxError
from django.conf import settings

register = template.Library()

# E.g. to use the value of MY_HELP_URL from settings.py in a template
# {% get_setting MY_HELP_URL as help_url %} 
# {% if help_url %}<a href="{% help_url %}">Help</a>{% endif %}

class SettingNode(Node):
    def __init__(self, settingname, var_name):
        self.settingname = settingname
        self.var_name = var_name
    def render(self, context):
        context[self.var_name] = getattr(settings, self.settingname, '')
        return ''

@register.tag()
def get_setting(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise TemplateSyntaxError("%r tag requires arguments" % token.contents.split()[0])
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise TemplateSyntaxError("%r tag had invalid arguments" % tag_name)
    param, var_name = m.groups()
    # strip quotes if present
    if ( (param[0] in ('"', "'")) and param[0] == param[-1] ):
        param = param[1:-1]
    return SettingNode(param, var_name)