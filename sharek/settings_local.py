
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'dostor_masr_staging',                      # Or path to database file if using sqlite3.
        'USER': 'dostory',                      			# Not used with sqlite3.
        'PASSWORD': 'dostory',                  			# Not used with sqlite3.
        'HOST': '',                     					# Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      					# Set to empty string for default. Not used with sqlite3.
    }
}

paginator = 10
domain = "http://dostour2012.org/sharek/"

FACEBOOK_APP_ID = '462028557155670'
FACEBOOK_API_KEY = ''
FACEBOOK_API_SECRET = 'be12f929d5bb8c51129b798f88548cfa'
FACEBOOK_REDIRECT_URI = 'http://dostour2012.org/sharek/facebook/login'


TWITTER_CONSUMER_KEY         = 'QpP7HcPkTwajLwn0E3k4w'
TWITTER_CONSUMER_SECRET      = 'jIo8jHkzGqHOFXDMotDcZsM3GbbyLYo6ee5CXUmRtA'

#FACEBOOK_APP_ID              = '337841982964299' #localhost
#FACEBOOK_API_SECRET          = 'a21b5514d63bb2969b078e31273314de' #localhost
FACEBOOK_EXTENDED_PERMISSIONS = ['email']

GOOGLE_CONSUMER_KEY          = ''
GOOGLE_CONSUMER_SECRET       = ''
GOOGLE_OAUTH2_CLIENT_ID      = ''
GOOGLE_OAUTH2_CLIENT_SECRET  = ''

