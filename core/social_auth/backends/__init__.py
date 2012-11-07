"""
Base backends structures.

This module defines base classes needed to define custom OpenID or OAuth
auth services from third parties. This customs must subclass an Auth and
and Backend class, check current implementation for examples.

Also the modules *must* define a BACKENDS dictionary with the backend name
(which is used for URLs matching) and Auth class, otherwise it won't be
enabled.
"""
from urllib2 import Request, HTTPError
from urllib import urlencode

from openid.consumer.consumer import Consumer, SUCCESS, CANCEL, FAILURE
from openid.consumer.discover import DiscoveryFailure
from openid.extensions import sreg, ax, pape

from oauth2 import Consumer as OAuthConsumer, Token, Request as OAuthRequest

from django.contrib.auth import authenticate
from django.utils import simplejson
from django.utils.importlib import import_module

from core.social_auth.models import UserSocialAuth
from core.social_auth.utils import setting, model_to_ctype, ctype_to_model, \
                              clean_partial_pipeline, url_add_parameters, \
                              get_random_string, constant_time_compare, \
                              dsa_urlopen
from core.social_auth.store import DjangoOpenIDStore
from core.social_auth.backends.exceptions import StopPipeline, AuthException, \
                                            AuthFailed, AuthCanceled, \
                                            AuthUnknownError, AuthTokenError, \
                                            AuthMissingParameter, \
                                            AuthStateMissing, \
                                            AuthStateForbidden, \
                                            NotAllowedToDisconnect
from core.social_auth.backends.utils import build_consumer_oauth_request


# OpenID configuration
OLD_AX_ATTRS = [
    ('http://schema.openid.net/contact/email', 'old_email'),
    ('http://schema.openid.net/namePerson', 'old_fullname'),
    ('http://schema.openid.net/namePerson/friendly', 'old_nickname')
]
AX_SCHEMA_ATTRS = [
    # Request both the full name and first/last components since some
    # providers offer one but not the other.
    ('http://axschema.org/contact/email', 'email'),
    ('http://axschema.org/namePerson', 'fullname'),
    ('http://axschema.org/namePerson/first', 'first_name'),
    ('http://axschema.org/namePerson/last', 'last_name'),
    ('http://axschema.org/namePerson/friendly', 'nickname'),
]
SREG_ATTR = [
    ('email', 'email'),
    ('fullname', 'fullname'),
    ('nickname', 'nickname')
]
OPENID_ID_FIELD = 'openid_identifier'
SESSION_NAME = 'openid'

# key for username in user details dict used around, see get_user_details
# method
USERNAME = 'username'

PIPELINE = setting('SOCIAL_AUTH_PIPELINE', (
                'core.social_auth.backends.pipeline.social.social_auth_user',
                # Removed by default since it can be a dangerouse behavior that
                # could lead to accounts take over.
                #'social_auth.backends.pipeline.associate.associate_by_email',
                'core.social_auth.backends.pipeline.user.get_username',
                'core.social_auth.backends.pipeline.user.create_user',
                'core.social_auth.backends.pipeline.social.associate_user',
                'core.social_auth.backends.pipeline.social.load_extra_data',
                'core.social_auth.backends.pipeline.user.update_user_details',
           ))


class SocialAuthBackend(object):
    """A django.contrib.auth backend that authenticates the user based on
    a authentication provider response"""
    name = ''  # provider name, it's stored in database
    supports_inactive_user = False

    def authenticate(self, *args, **kwargs):
        """Authenticate user using social credentials

        Authentication is made if this is the correct backend, backend
        verification is made by kwargs inspection for current backend
        name presence.
        """
        # Validate backend and arguments. Require that the Social Auth
        # response be passed in as a keyword argument, to make sure we
        # don't match the username/password calling conventions of
        # authenticate.
        if not (self.name and kwargs.get(self.name) and 'response' in kwargs):
            return None

        response = kwargs.get('response')
        pipeline = PIPELINE
        kwargs = kwargs.copy()
        kwargs['backend'] = self

        if 'pipeline_index' in kwargs:
            pipeline = pipeline[kwargs['pipeline_index']:]
        else:
            kwargs['details'] = self.get_user_details(response)
            kwargs['uid'] = self.get_user_id(kwargs['details'], response)
            kwargs['is_new'] = False

        out = self.pipeline(pipeline, *args, **kwargs)
        if not isinstance(out, dict):
            return out

        social_user = out.get('social_user')
        if social_user:
            # define user.social_user attribute to track current social
            # account
            user = social_user.user
            user.social_user = social_user
            user.is_new = out.get('is_new')
            return user

    def pipeline(self, pipeline, *args, **kwargs):
        """Pipeline"""
        out = kwargs.copy()

        if 'pipeline_index' in kwargs:
            base_index = int(kwargs['pipeline_index'])
        else:
            base_index = 0

        for idx, name in enumerate(pipeline):
            out['pipeline_index'] = base_index + idx
            mod_name, func_name = name.rsplit('.', 1)
            mod = import_module(mod_name)
            func = getattr(mod, func_name, None)

            try:
                result = func(*args, **out) or {}
            except StopPipeline:
                # Clean partial pipeline on stop
                if 'request' in kwargs:
                    clean_partial_pipeline(kwargs['request'])
                break

            if isinstance(result, dict):
                out.update(result)
            else:
                return result
        return out

    def extra_data(self, user, uid, response, details):
        """Return default blank user extra data"""
        return {}

    def get_user_id(self, details, response):
        """Must return a unique ID from values returned on details"""
        raise NotImplementedError('Implement in subclass')

    def get_user_details(self, response):
        """Must return user details in a know internal struct:
            {USERNAME: <username if any>,
             'email': <user email if any>,
             'fullname': <user full name if any>,
             'first_name': <user first name if any>,
             'last_name': <user last name if any>}
        """
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def tokens(cls, instance):
        """Return the tokens needed to authenticate the access to any API the
        service might provide. The return value will be a dictionary with the
        token type name as key and the token value.

        instance must be a UserSocialAuth instance.
        """
        if instance.extra_data and 'access_token' in instance.extra_data:
            return {
                'access_token': instance.extra_data['access_token']
            }
        else:
            return {}

    def get_user(self, user_id):
        """
        Return user with given ID from the User model used by this backend.
        This is called by django.contrib.auth.middleware.
        """
        return UserSocialAuth.get_user(user_id)


class OAuthBackend(SocialAuthBackend):
    """OAuth authentication backend base class.

    EXTRA_DATA defines a set of name that will be stored in
               extra_data field. It must be a list of tuples with
               name and alias.

    Also settings will be inspected to get more values names that should be
    stored on extra_data field. Setting name is created from current backend
    name (all uppercase) plus _EXTRA_DATA.

    access_token is always stored.
    """
    EXTRA_DATA = None

    def get_user_id(self, details, response):
        """OAuth providers return an unique user id in response"""
        return response['id']

    def extra_data(self, user, uid, response, details):
        """Return access_token and extra defined names to store in
        extra_data field"""
        data = {'access_token': response.get('access_token', '')}
        name = self.name.replace('-', '_').upper()
        names = (self.EXTRA_DATA or []) + setting(name + '_EXTRA_DATA', [])
        for entry in names:
            if len(entry) == 2:
                (name, alias), discard = entry, False
            elif len(entry) == 3:
                name, alias, discard = entry
            elif len(entry) == 1:
                name = alias = entry
            else:  # ???
                continue

            value = response.get(name)
            if discard and not value:
                continue
            data[alias] = value
        return data


class OpenIDBackend(SocialAuthBackend):
    """Generic OpenID authentication backend"""
    name = 'openid'

    def get_user_id(self, details, response):
        """Return user unique id provided by service"""
        return response.identity_url

    def values_from_response(self, response, sreg_names=None, ax_names=None):
        """Return values from SimpleRegistration response or
        AttributeExchange response if present.

        @sreg_names and @ax_names must be a list of name and aliases
        for such name. The alias will be used as mapping key.
        """
        values = {}

        # Use Simple Registration attributes if provided
        if sreg_names:
            resp = sreg.SRegResponse.fromSuccessResponse(response)
            if resp:
                values.update((alias, resp.get(name) or '')
                                    for name, alias in sreg_names)

        # Use Attribute Exchange attributes if provided
        if ax_names:
            resp = ax.FetchResponse.fromSuccessResponse(response)
            if resp:
                for src, alias in ax_names:
                    name = alias.replace('old_', '')
                    values[name] = resp.getSingle(src, '') or values.get(name)
        return values

    def get_user_details(self, response):
        """Return user details from an OpenID request"""
        values = {USERNAME: '', 'email': '', 'fullname': '',
                  'first_name': '', 'last_name': ''}
        # update values using SimpleRegistration or AttributeExchange
        # values
        values.update(self.values_from_response(response,
                                                SREG_ATTR,
                                                OLD_AX_ATTRS +
                                                AX_SCHEMA_ATTRS))

        fullname = values.get('fullname') or ''
        first_name = values.get('first_name') or ''
        last_name = values.get('last_name') or ''

        if not fullname and first_name and last_name:
            fullname = first_name + ' ' + last_name
        elif fullname:
            try:  # Try to split name for django user storage
                first_name, last_name = fullname.rsplit(' ', 1)
            except ValueError:
                last_name = fullname

        values.update({'fullname': fullname, 'first_name': first_name,
                       'last_name': last_name,
                       USERNAME: values.get(USERNAME) or
                                   (first_name.title() + last_name.title())})
        return values

    def extra_data(self, user, uid, response, details):
        """Return defined extra data names to store in extra_data field.
        Settings will be inspected to get more values names that should be
        stored on extra_data field. Setting name is created from current
        backend name (all uppercase) plus _SREG_EXTRA_DATA and
        _AX_EXTRA_DATA because values can be returned by SimpleRegistration

        or AttributeExchange schemas.

        Both list must be a value name and an alias mapping similar to
        SREG_ATTR, OLD_AX_ATTRS or AX_SCHEMA_ATTRS
        """
        name = self.name.replace('-', '_').upper()
        sreg_names = setting(name + '_SREG_EXTRA_DATA')
        ax_names = setting(name + '_AX_EXTRA_DATA')
        data = self.values_from_response(response, sreg_names, ax_names)
        return data


class BaseAuth(object):
    """Base authentication class, new authenticators should subclass
    and implement needed methods.

        AUTH_BACKEND   Authorization backend related with this service
    """
    AUTH_BACKEND = None

    def __init__(self, request, redirect):
        self.request = request
        # Use request because some auth providers use POST urls with needed
        # GET parameters on it
        self.data = request.REQUEST
        self.redirect = redirect

    def auth_url(self):
        """Must return redirect URL to auth provider"""
        raise NotImplementedError('Implement in subclass')

    def auth_html(self):
        """Must return login HTML content returned by provider"""
        raise NotImplementedError('Implement in subclass')

    def auth_complete(self, *args, **kwargs):
        """Completes loging process, must return user instance"""
        raise NotImplementedError('Implement in subclass')

    def to_session_dict(self, next_idx, *args, **kwargs):
        """Returns dict to store on session for partial pipeline."""
        return {
            'next': next_idx,
            'backend': self.AUTH_BACKEND.name,
            'args': tuple(map(model_to_ctype, args)),
            'kwargs': dict((key, model_to_ctype(val))
                                for key, val in kwargs.iteritems())
        }

    def from_session_dict(self, session_data, *args, **kwargs):
        """Takes session saved data to continue pipeline and merges with any
        new extra argument needed. Returns tuple with next pipeline index
        entry, arguments and keyword arguments to continue the process."""
        args = args[:] + tuple(map(ctype_to_model, session_data['args']))

        kwargs = kwargs.copy()
        saved_kwargs = dict((key, ctype_to_model(val))
                            for key, val in session_data['kwargs'].iteritems())
        saved_kwargs.update((key, val)
                            for key, val in kwargs.iteritems())
        return (session_data['next'], args, saved_kwargs)

    def continue_pipeline(self, *args, **kwargs):
        """Continue previous halted pipeline"""
        kwargs.update({
            'auth': self,
            self.AUTH_BACKEND.name: True
        })
        return authenticate(*args, **kwargs)

    def request_token_extra_arguments(self):
        """Return extra arguments needed on request-token process,
        setting is per backend and defined by:
            <backend name in uppercase>_REQUEST_TOKEN_EXTRA_ARGUMENTS.
        """
        backend_name = self.AUTH_BACKEND.name.upper().replace('-', '_')
        return setting(backend_name + '_REQUEST_TOKEN_EXTRA_ARGUMENTS', {})

    def auth_extra_arguments(self):
        """Return extra arguments needed on auth process, setting is per
        backend and defined by:
            <backend name in uppercase>_AUTH_EXTRA_ARGUMENTS.
        The defaults can be overriden by GET parameters.
        """
        backend_name = self.AUTH_BACKEND.name.upper().replace('-', '_')
        extra_arguments = setting(backend_name + '_AUTH_EXTRA_ARGUMENTS', {})
        for key in extra_arguments:
            if key in self.data:
                extra_arguments[key] = self.data[key]
        return extra_arguments

    @property
    def uses_redirect(self):
        """Return True if this provider uses redirect url method,
        otherwise return false."""
        return True

    @classmethod
    def enabled(cls):
        """Return backend enabled status, all enabled by default"""
        return True

    def disconnect(self, user, association_id=None):
        """Deletes current backend from user if associated.
        Override if extra operations are needed.
        """
        name = self.AUTH_BACKEND.name
        if UserSocialAuth.allowed_to_disconnect(user, name, association_id):
        if association_id:
            UserSocialAuth.get_social_auth_for_user(user)\
                            .get(id=association_id).delete()
        else:
            UserSocialAuth.get_social_auth_for_user(user)\
                                .filter(provider=name)\
                                .delete()
        else:
            raise NotAllowedToDisconnect()

    def build_absolute_uri(self, path=None):
        """Build absolute URI for given path. Replace http:// schema with
        https:// if SOCIAL_AUTH_REDIRECT_IS_HTTPS is defined.
        """
        uri = self.request.build_absolute_uri(path)
        if setting('SOCIAL_AUTH_REDIRECT_IS_HTTPS'):
            uri = uri.replace('http://', 'https://')
        return uri


class OpenIdAuth(BaseAuth):
    """OpenId process handling"""
    AUTH_BACKEND = OpenIDBackend

    def auth_url(self):
        """Return auth URL returned by service"""
        openid_request = self.setup_request(self.auth_extra_arguments())
        # Construct completion URL, including page we should redirect to
        return_to = self.build_absolute_uri(self.redirect)
        return openid_request.redirectURL(self.trust_root(), return_to)

    def auth_html(self):
        """Return auth HTML returned by service"""
        openid_request = self.setup_request(self.auth_extra_arguments())
        return_to = self.build_absolute_uri(self.redirect)
        form_tag = {'id': 'openid_message'}
        return openid_request.htmlMarkup(self.trust_root(), return_to,
                                         form_tag_attrs=form_tag)

    def trust_root(self):
        """Return trust-root option"""
        return setting('OPENID_TRUST_ROOT') or self.build_absolute_uri('/')

    def continue_pipeline(self, *args, **kwargs):
        """Continue previous halted pipeline"""
        response = self.consumer().complete(dict(self.data.items()),
                                            self.build_absolute_uri())
        kwargs.update({
            'auth': self,
            'response': response,
            self.AUTH_BACKEND.name: True
        })
        return authenticate(*args, **kwargs)

    def auth_complete(self, *args, **kwargs):
        """Complete auth process"""
        response = self.consumer().complete(dict(self.data.items()),
                                            self.build_absolute_uri())
        if not response:
            raise AuthException(self, 'OpenID relying party endpoint')
        elif response.status == SUCCESS:
            kwargs.update({
                'auth': self,
                'response': response,
                self.AUTH_BACKEND.name: True
            })
            return authenticate(*args, **kwargs)
        elif response.status == FAILURE:
            raise AuthFailed(self, response.message)
        elif response.status == CANCEL:
            raise AuthCanceled(self)
        else:
            raise AuthUnknownError(self, response.status)

    def setup_request(self, extra_params=None):
        """Setup request"""
        openid_request = self.openid_request(extra_params)
        # Request some user details. Use attribute exchange if provider
        # advertises support.
        if openid_request.endpoint.supportsType(ax.AXMessage.ns_uri):
            fetch_request = ax.FetchRequest()
            # Mark all attributes as required, Google ignores optional ones
            for attr, alias in (AX_SCHEMA_ATTRS + OLD_AX_ATTRS):
                fetch_request.add(ax.AttrInfo(attr, alias=alias,
                                              required=True))
        else:
            fetch_request = sreg.SRegRequest(optional=dict(SREG_ATTR).keys())
        openid_request.addExtension(fetch_request)

        # Add PAPE Extension for if configured
        preferred_policies = setting(
            'SOCIAL_AUTH_OPENID_PAPE_PREFERRED_AUTH_POLICIES')
        preferred_level_types = setting(
            'SOCIAL_AUTH_OPENID_PAPE_PREFERRED_AUTH_LEVEL_TYPES')
        max_age = setting('SOCIAL_AUTH_OPENID_PAPE_MAX_AUTH_AGE')
        if max_age is not None:
            try:
                max_age = int(max_age)
            except (ValueError, TypeError):
                max_age = None

        if (max_age is not None or preferred_policies is not None
            or preferred_level_types is not None):
            pape_request = pape.Request(
                preferred_auth_policies=preferred_policies,
                max_auth_age=max_age,
                preferred_auth_level_types=preferred_level_types
                )
            openid_request.addExtension(pape_request)

        return openid_request

    def consumer(self):
        """Create an OpenID Consumer object for the given Django request."""
        return Consumer(self.request.session.setdefault(SESSION_NAME, {}),
                        DjangoOpenIDStore())

    @property
    def uses_redirect(self):
        """Return true if openid request will be handled with redirect or
        HTML content will be returned.
        """
        return self.openid_request().shouldSendRedirect()

    def openid_request(self, extra_params=None):
        """Return openid request"""
        if not hasattr(self, '_openid_request'):
        try:
                self._openid_request = self.consumer().begin(
                    url_add_parameters(self.openid_url(), extra_params)
                )
        except DiscoveryFailure, err:
            raise AuthException(self, 'OpenID discovery error: %s' % err)
        return self._openid_request

    def openid_url(self):
        """Return service provider URL.
        This base class is generic accepting a POST parameter that specifies
        provider URL."""
        if OPENID_ID_FIELD not in self.data:
            raise AuthMissingParameter(self, OPENID_ID_FIELD)
        return self.data[OPENID_ID_FIELD]


class BaseOAuth(BaseAuth):
    """OAuth base class"""
    SETTINGS_KEY_NAME = ''
    SETTINGS_SECRET_NAME = ''
    SCOPE_VAR_NAME = None
    SCOPE_PARAMETER_NAME = 'scope'
    DEFAULT_SCOPE = None
    SCOPE_SEPARATOR = ' '

    def __init__(self, request, redirect):
        """Init method"""
        super(BaseOAuth, self).__init__(request, redirect)
        self.redirect_uri = self.build_absolute_uri(self.redirect)

    @classmethod
    def get_key_and_secret(cls):
        """Return tuple with Consumer Key and Consumer Secret for current
        service provider. Must return (key, secret), order *must* be respected.
        """
        return setting(cls.SETTINGS_KEY_NAME), \
               setting(cls.SETTINGS_SECRET_NAME)

    @classmethod
    def enabled(cls):
        """Return backend enabled status by checking basic settings"""
        return setting(cls.SETTINGS_KEY_NAME) and \
               setting(cls.SETTINGS_SECRET_NAME)

    def get_scope(self):
        """Return list with needed access scope"""
        scope = self.DEFAULT_SCOPE or []
        if self.SCOPE_VAR_NAME:
            scope = scope + setting(self.SCOPE_VAR_NAME, [])
        return scope

    def get_scope_argument(self):
        param = {}
        scope = self.get_scope()
        if scope:
            param[self.SCOPE_PARAMETER_NAME] = self.SCOPE_SEPARATOR.join(scope)
        return param


class ConsumerBasedOAuth(BaseOAuth):
    """Consumer based mechanism OAuth authentication, fill the needed
    parameters to communicate properly with authentication service.

        AUTHORIZATION_URL       Authorization service url
        REQUEST_TOKEN_URL       Request token URL
        ACCESS_TOKEN_URL        Access token URL
    """
    AUTHORIZATION_URL = ''
    REQUEST_TOKEN_URL = ''
    ACCESS_TOKEN_URL = ''

    def auth_url(self):
        """Return redirect url"""
        token = self.unauthorized_token()
        name = self.AUTH_BACKEND.name + 'unauthorized_token_name'
        self.request.session[name] = token.to_string()
        return self.oauth_authorization_request(token).to_url()

    def auth_complete(self, *args, **kwargs):
        """Return user, might be logged in"""
        name = self.AUTH_BACKEND.name + 'unauthorized_token_name'
        unauthed_token = self.request.session.get(name)
        if not unauthed_token:
            raise AuthTokenError('Missing unauthorized token')

        token = Token.from_string(unauthed_token)
        if token.key != self.data.get('oauth_token', 'no-token'):
            raise AuthTokenError('Incorrect tokens')

        try:
            access_token = self.access_token(token)
        except HTTPError, e:
            if e.code == 400:
                raise AuthCanceled(self)
            else:
                raise

        data = self.user_data(access_token)
        if data is not None:
            data['access_token'] = access_token.to_string()

        kwargs.update({
            'auth': self,
            'response': data,
            self.AUTH_BACKEND.name: True
        })
        return authenticate(*args, **kwargs)

    def unauthorized_token(self):
        """Return request for unauthorized token (first stage)"""
        request = self.oauth_request(token=None, url=self.REQUEST_TOKEN_URL,
                             extra_params=self.request_token_extra_arguments())
        response = self.fetch_response(request)
        return Token.from_string(response)

    def oauth_authorization_request(self, token):
        """Generate OAuth request to authorize token."""
        params = self.auth_extra_arguments() or {}
        params.update(self.get_scope_argument())
        return OAuthRequest.from_token_and_callback(
            token=token,
                                        callback=self.redirect_uri,
                                        http_url=self.AUTHORIZATION_URL,
            parameters=params
        )

    def oauth_request(self, token, url, extra_params=None):
        """Generate OAuth request, setups callback url"""
        return build_consumer_oauth_request(self, token, url,
                                            self.redirect_uri,
                                            self.data.get('oauth_verifier'),
                                            extra_params)

    def fetch_response(self, request):
        """Executes request and fetchs service response"""
        response = dsa_urlopen(request.to_url())
        return '\n'.join(response.readlines())

    def access_token(self, token):
        """Return request for access token value"""
        request = self.oauth_request(token, self.ACCESS_TOKEN_URL)
        return Token.from_string(self.fetch_response(request))

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        raise NotImplementedError('Implement in subclass')

    @property
    def consumer(self):
        """Setups consumer"""
        return OAuthConsumer(*self.get_key_and_secret())


class BaseOAuth2(BaseOAuth):
    """Base class for OAuth2 providers.

    OAuth2 draft details at:
        http://tools.ietf.org/html/draft-ietf-oauth-v2-10

    Attributes:
        AUTHORIZATION_URL       Authorization service url
        ACCESS_TOKEN_URL        Token URL
    """
    AUTHORIZATION_URL = None
    ACCESS_TOKEN_URL = None
    RESPONSE_TYPE = 'code'
    REDIRECT_STATE = True

    def state_token(self):
        """Generate csrf token to include as state parameter."""
        return get_random_string(32)

    def get_redirect_uri(self, state):
        """Build redirect_uri with redirect_state parameter."""
        uri = self.redirect_uri
        if self.REDIRECT_STATE:
            uri = url_add_parameters(uri, {'redirect_state': state})
        return uri

    def auth_url(self):
        """Return redirect url"""
        client_id, client_secret = self.get_key_and_secret()
        state = self.state_token()
        # Store state in session for further request validation. The state
        # value is passed as state parameter (as specified in OAuth2 spec), but
        # also added to redirect_uri, that way we can still verify the request
        # if the provider doesn't implement the state parameter.
        self.request.session[self.AUTH_BACKEND.name + '_state'] = state
        args = {
            'client_id': client_id,
            'state': state,
            'redirect_uri': self.get_redirect_uri(state)
        }

        args.update(self.get_scope_argument())
        if self.RESPONSE_TYPE:
            args['response_type'] = self.RESPONSE_TYPE

        args.update(self.auth_extra_arguments())
        if self.request.META.get('QUERY_STRING'):
            query_string = '&' + self.request.META['QUERY_STRING']
        else:
            query_string = ''
        return self.AUTHORIZATION_URL + '?' + urlencode(args) + query_string

    def validate_state(self):
        """Validate state value. Raises exception on error, returns state
        value if valid."""
        state = self.request.session.get(self.AUTH_BACKEND.name + '_state')
        request_state = self.data.get('state') or \
                        self.data.get('redirect_state')
        if not request_state:
            raise AuthMissingParameter(self, 'state')
        elif not state:
            raise AuthStateMissing(self, 'state')
        elif not constant_time_compare(request_state, state):
            raise AuthStateForbidden(self)
        return state

    def auth_complete(self, *args, **kwargs):
        """Completes loging process, must return user instance"""
        if self.data.get('error'):
            error = self.data.get('error_description') or self.data['error']
            raise AuthFailed(self, error)

        state = self.validate_state()
        client_id, client_secret = self.get_key_and_secret()
        params = {
            'grant_type': 'authorization_code',  # request auth code
            'code': self.data.get('code', ''),  # server response code
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': self.get_redirect_uri(state)
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'}
        request = Request(self.ACCESS_TOKEN_URL, data=urlencode(params),
                          headers=headers)

        try:
            response = simplejson.loads(dsa_urlopen(request).read())
        except HTTPError, e:
            if e.code == 400:
                raise AuthCanceled(self)
            else:
                raise
        except (ValueError, KeyError):
            raise AuthUnknownError(self)

        if response.get('error'):
            error = response.get('error_description') or response.get('error')
            raise AuthFailed(self, error)
        else:
            data = self.user_data(response['access_token'], response)
            response.update(data or {})
            kwargs.update({
                'auth': self,
                'response': response,
                self.AUTH_BACKEND.name: True
            })
            return authenticate(*args, **kwargs)


# Backend loading was previously performed via the
# SOCIAL_AUTH_IMPORT_BACKENDS setting - as it's no longer used,
# provide a deprecation warning.
if setting('SOCIAL_AUTH_IMPORT_BACKENDS'):
    from warnings import warn
    warn("SOCIAL_AUTH_IMPORT_SOURCES is deprecated")


# Cache for discovered backends.
BACKENDSCACHE = {}


def get_backends(force_load=False):
    """
    Entry point to the BACKENDS cache. If BACKENDSCACHE hasn't been
    populated, each of the modules referenced in
    AUTHENTICATION_BACKENDS is imported and checked for a BACKENDS
    definition and if enabled, added to the cache.

    Previously all backends were attempted to be loaded at
    import time of this module, which meant that backends that subclass
    bases found in this module would not have the chance to be loaded
    by the time they were added to this module's BACKENDS dict. See:
    https://github.com/omab/django-social-auth/issues/204

    This new approach ensures that backends are allowed to subclass from
    bases in this module and still be picked up.

    A force_load boolean arg is also provided so that get_backend
    below can retry a requested backend that may not yet be discovered.
    """
    if not BACKENDSCACHE or force_load:
        for auth_backend in setting('AUTHENTICATION_BACKENDS'):
            mod, cls_name = auth_backend.rsplit('.', 1)
            module = import_module(mod)
            backend = getattr(module, cls_name)

            if issubclass(backend, SocialAuthBackend):
                name = backend.name
                backends = getattr(module, 'BACKENDS', {})
                if name in backends and backends[name].enabled():
                    BACKENDSCACHE[name] = backends[name]
    return BACKENDSCACHE


def get_backend(name, *args, **kwargs):
    """Returns a backend by name. Backends are stored in the BACKENDSCACHE
    cache dict. If not found, each of the modules referenced in
    AUTHENTICATION_BACKENDS is imported and checked for a BACKENDS
    definition. If the named backend is found in the module's BACKENDS
    definition, it's then stored in the cache for future access.
    """
    try:
        # Cached backend which has previously been discovered.
        return BACKENDSCACHE[name](*args, **kwargs)
    except KeyError:
        # Force a reload of BACKENDS to ensure a missing
        # backend hasn't been missed.
        get_backends(force_load=True)
        try:
            return BACKENDSCACHE[name](*args, **kwargs)
        except KeyError:
            return None


BACKENDS = {
    'openid': OpenIdAuth
}