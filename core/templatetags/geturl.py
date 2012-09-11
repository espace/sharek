import re 
from django import template
from BeautifulSoup import BeautifulSoup

register = template.Library()

@register.simple_tag
def geturl(url, timeout=None):
    """
    Usage: {% geturl url [timeout] %}

    Examples:
    {% geturl "http://example.com/path/to/content/" %}
    {% geturl object.urlfield 1 %} 
    """
    import socket
    import re
    from urllib2 import urlopen
    socket_default_timeout = socket.getdefaulttimeout()
    if timeout is not None:
        try:
            socket_timeout = float(timeout)
        except ValueError:
            raise template.TemplateSyntaxError, "timeout argument of geturl tag, if provided, must be convertible to a float"
        try:
            socket.setdefaulttimeout(socket_timeout)
        except ValueError:
            raise template.TemplateSyntaxError, "timeout argument of geturl tag, if provided, cannot be less than zero"
    try:
        try: 
            content = urlopen(url).read()
        finally: # reset socket timeout
            if timeout is not None:
                socket.setdefaulttimeout(socket_default_timeout) 
    except:
        content = ''
    
    soup = BeautifulSoup(content)
    form_str =str(soup.form)
    form_str = re.sub( 'method="POST"', 'method="POST" target="hidden_iframe" onsubmit="submitted=true;"', form_str)
    form_str = re.sub( 'value="Submit"', 'value="إرسال"', form_str)
    
    return form_str
