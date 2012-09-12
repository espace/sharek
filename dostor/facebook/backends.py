from django.conf import settings
from django.contrib.auth import models as auth_models
    
import cgi
import urllib
import simplejson

class FacebookBackend:
    
    def authenticate(self, token=None):
        return ''