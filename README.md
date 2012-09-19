# Sharek

_Contribution of the crowd_

Sharek is a platform that allows end users to contribute in building any structured text content. It basically started to allow Egyptian people write their own consistution after the uprising against corruption in 2011. A draft for the constitution articles is published allowing Egyptian users to to suggest and support enhancements to the text articles.
On August 2012, the contribution platform has been released to the public at http://dostour.eg/sharek/

## Installation

Based on django 1.4.1 and uses PostgreSQL as the database engine

### Setup on debian/ubuntu dependencies

  ```
    sudo apt-get install build-essential python-dev python-setuptools git-core gcc \
    curl libpcre3 libpcre3-dev build-essential bash-completion postgresql ipython \
    python python-dev python-setuptools -y 

    sudo easy_install pip  

    sudo pip install django

    sudo pip install django-markitup 

    sudo pip install Markdown

    sudo pip install django-ajax-selects

    sudo apt-get install python-beautifulsoup

    sudo pip install feedparser

    sudo easy_install template_utils

    easy_install django_evolution

    sudo pip install django-markitup

    sudo apt-get install python-psycopg2

    apt-get install python-simplejson ### easy_install simplejson

    sudo apt-get install python-tz

    sudo easy_install humanize
  ```

### Getting the app up

1. fork the and clone the repo
2. Create the proper database and database user to be used
3. rename the file *sharek/settings_local.py.example* to *sharek/settings_local.py* and change all the custom configuration for database, facebook and twitter to your own settings
4. Start the app using under development via:

```
 ./manage.py runserver 127.0.0.1:8000 --settings=settings
```

### Common problems and errors:

* _No module named settings_

 missing settings.py file in project directory


* _FATAL:  Peer authentication failed for user "dostory"_

 Then connecting to postgres has failed.. fix the authentication and verify connectivity using:

 ```
  psql -d db_name -U db_user -W 
 ```



