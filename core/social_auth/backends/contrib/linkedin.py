"""
Linkedin OAuth support

No extra configurations are needed to make this work.
"""
from xml.etree import ElementTree
from xml.parsers.expat import ExpatError

from core.social_auth.utils import setting
from core.social_auth.backends import ConsumerBasedOAuth, OAuthBackend, USERNAME
from core.social_auth.backends.exceptions import AuthCanceled, AuthUnknownError


LINKEDIN_SERVER = 'linkedin.com'
LINKEDIN_REQUEST_TOKEN_URL = 'https://api.%s/uas/oauth/requestToken' % \
                                    LINKEDIN_SERVER
LINKEDIN_ACCESS_TOKEN_URL = 'https://api.%s/uas/oauth/accessToken' % \
                                    LINKEDIN_SERVER
LINKEDIN_AUTHORIZATION_URL = 'https://www.%s/uas/oauth/authenticate' % \
                                    LINKEDIN_SERVER
LINKEDIN_CHECK_AUTH = 'https://api.%s/v1/people/~' % LINKEDIN_SERVER
# Check doc at http://developer.linkedin.com/docs/DOC-1014 about how to use
# fields selectors to retrieve extra user data
LINKEDIN_FIELD_SELECTORS = ['id', 'first-name', 'last-name']


class LinkedinBackend(OAuthBackend):
    """Linkedin OAuth authentication backend"""
    name = 'linkedin'
    EXTRA_DATA = [('id', 'id'),
                  ('first-name', 'first_name'),
                  ('last-name', 'last_name')]

    def get_user_details(self, response):
        """Return user details from Linkedin account"""
        first_name, last_name = response['first-name'], response['last-name']
        email = response.get('email-address', '')
        return {USERNAME: first_name + last_name,
                'fullname': first_name + ' ' + last_name,
                'first_name': first_name,
                'last_name': last_name,
                'email': email}


class LinkedinAuth(ConsumerBasedOAuth):
    """Linkedin OAuth authentication mechanism"""
    AUTHORIZATION_URL = LINKEDIN_AUTHORIZATION_URL
    REQUEST_TOKEN_URL = LINKEDIN_REQUEST_TOKEN_URL
    ACCESS_TOKEN_URL = LINKEDIN_ACCESS_TOKEN_URL
    SERVER_URL = 'api.%s' % LINKEDIN_SERVER
    AUTH_BACKEND = LinkedinBackend
    SETTINGS_KEY_NAME = 'LINKEDIN_CONSUMER_KEY'
    SETTINGS_SECRET_NAME = 'LINKEDIN_CONSUMER_SECRET'

    def user_data(self, access_token, *args, **kwargs):
        """Return user data provided"""
        fields_selectors = LINKEDIN_FIELD_SELECTORS + \
                           setting('LINKEDIN_EXTRA_FIELD_SELECTORS', [])
        url = LINKEDIN_CHECK_AUTH + ':(%s)' % ','.join(fields_selectors)
        request = self.oauth_request(access_token, url)
        raw_xml = self.fetch_response(request)
        try:
            return to_dict(ElementTree.fromstring(raw_xml))
        except (ExpatError, KeyError, IndexError):
            return None

    def auth_complete(self, *args, **kwargs):
        """Complete auth process. Check LinkedIn error response."""
        oauth_problem = self.request.GET.get('oauth_problem')
        if oauth_problem:
            if oauth_problem == 'user_refused':
                raise AuthCanceled(self, '')
            else:
                raise AuthUnknownError(self, 'LinkedIn error was %s' %
                                                    oauth_problem)
        return super(LinkedinAuth, self).auth_complete(*args, **kwargs)


def to_dict(xml):
    """Convert XML structure to dict recursively, repeated keys entries
    are returned as in list containers."""
    children = xml.getchildren()
    if not children:
        return xml.text
    else:
        out = {}
        for node in xml.getchildren():
            if node.tag in out:
                if not isinstance(out[node.tag], list):
                    out[node.tag] = [out[node.tag]]
                out[node.tag].append(to_dict(node))
            else:
                out[node.tag] = to_dict(node)
        return out


# Backend definition
BACKENDS = {
    'linkedin': LinkedinAuth,
}
