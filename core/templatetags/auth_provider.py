from core.social_auth.models import UserSocialAuth
from django import template
register = template.Library()

@register.filter
def get_auth_provider(username):
    return UserSocialAuth.auth_provider(username)

get_auth_provider = register.filter('get_auth_provider', get_auth_provider)
