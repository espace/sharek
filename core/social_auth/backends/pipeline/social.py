from core.social_auth.models import UserSocialAuth, SOCIAL_AUTH_MODELS_MODULE
from core.social_auth.backends.exceptions import AuthAlreadyAssociated
from django.utils.translation import ugettext


def social_auth_user(backend, uid, user=None, *args, **kwargs):
    """Return UserSocialAuth account for backend/uid pair or None if it
    doesn't exists.

    Raise AuthAlreadyAssociated if UserSocialAuth entry belongs to another
    user.
    """
    social_user = UserSocialAuth.get_social_auth(backend.name, uid)
    if social_user:
        if user and social_user.user != user:
            msg = ugettext('This %(provider)s account is already in use.')
            raise AuthAlreadyAssociated(backend, msg % {
                'provider': backend.name
            })
        elif not user:
            user = social_user.user
    return {'social_user': social_user, 'user': user}


def associate_user(backend, user, uid, social_user=None, *args, **kwargs):
    """Associate user social account with user instance."""
    if social_user:
        return None

    try:
        social = UserSocialAuth.create_social_auth(user, uid, backend.name)
    except Exception as e:
        if not SOCIAL_AUTH_MODELS_MODULE.is_integrity_error(e):
            raise
        # Protect for possible race condition, those bastard with FTL
        # clicking capabilities, check issue #131:
        #   https://github.com/omab/django-social-auth/issues/131
        return social_auth_user(backend, uid, user, social_user=social_user,
                                *args, **kwargs)
    else:
        return {'social_user': social, 'user': social.user}


def load_extra_data(backend, details, response, uid, user, social_user=None,
                    *args, **kwargs):
    """Load extra data from provider and store it on current UserSocialAuth
    extra_data field.
    """
    social_user = social_user or \
                  UserSocialAuth.get_social_auth(backend.name, uid)
    if social_user:
        extra_data = backend.extra_data(user, uid, response, details)
        if extra_data and social_user.extra_data != extra_data:
            if social_user.extra_data:
                social_user.extra_data.update(extra_data)
            else:
                social_user.extra_data = extra_data
            social_user.save()
        return {'social_user': social_user}
