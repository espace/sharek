from django import forms
from django.utils import timezone
from datetime import datetime
from markitup.fields import MarkupField
from django.core import exceptions
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.signals import post_save
from django.db.models.aggregates import Max
from core.actions import exclusive_boolean_fields
from django.db import connection, models

from smart_selects.db_fields import ChainedForeignKey 

class Tag(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30, default='')
    slug = models.SlugField(max_length=50, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')
    order = models.IntegerField(blank = True, null = True)

    def __unicode__(self):
        #return u'%s - %s' % (self.topic.name, self.name)
        return self.name

    def get_absolute_url(self):
        return self.slug
    
    def get_articles(self):
      # the new tech of article " header and details "
      article_headers = self.articleheader_set.all()
      article_details = []
      for article_header in article_headers:
          ad = article_header.articledetails_set.filter(current = True)
          if len(ad) == 1:
              article_details.append(ad[0])
      return article_details

    
    def get_articles_limit(self, offset, limit):
        # the new tech of article " header and details "
        article_headers = self.articleheader_set.all()[offset:limit]
        article_details = []
        for article_header in article_headers:
            ad = article_header.articledetails_set.filter(current = True)
            if len(ad) == 1:
                article_details.append(ad[0])
        return article_details
        
        
    class Meta:
       ordering = ["order"]

class TopicManager(models.Manager):
    def with_counts(self):
       query = '''SELECT core_topic.id, core_topic.name, core_topic.slug, core_topic.order, core_topic.summary, core_topic._summary_rendered,
	   				( SELECT MAX(core_articledetails.mod_date) as articles_count FROM core_articleheader INNER JOIN core_articledetails on core_articleheader.id = core_articledetails.header_id WHERE core_topic.id = core_articleheader.topic_id AND core_articledetails.current is true ),
					( SELECT COUNT(core_articledetails.*) as articles_count FROM core_articleheader INNER JOIN core_articledetails on core_articleheader.id = core_articledetails.header_id WHERE core_topic.id = core_articleheader.topic_id AND core_articledetails.current is true ) as headers
				  FROM core_topic WHERE core_topic.parent_id IS NULL'''
       cursor = connection.cursor()
       cursor.execute(query)

       topic_list = []
       for row in cursor.fetchall():
           p = self.model(id=row[0], name=row[1], slug=row[2], order=row[3], summary=row[4], _summary_rendered=row[5])
           p.date_articles = row[6]
           p.count_articles = row[7]
           topic_list.append(p)
       return topic_list

class Topic(models.Model):
    parent = models.ForeignKey('self', null=True, blank=True)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30, default='')
    slug = models.SlugField(max_length=50, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')
    order = models.IntegerField(blank = True, null = True)
    objects = TopicManager()
    
    def __unicode__(self):
        if self.parent:
            if self.parent.parent:
                return "%s - %s - %s" % (self.parent.parent.name ,self.parent.name, self.name)
            return "%s - %s" % (self.parent.name, self.name)
        else:
            return "%s" % (self.name)

    def get_absolute_url(self):
        return self.slug

    @classmethod
    def total_contributions(self):
       query = '''SELECT SUM(count) FROM (
	   				SELECT COUNT(*) as count FROM core_feedback
					UNION
					SELECT COUNT(*) FROM core_rating
					UNION
					SELECT COUNT(*) FROM core_articlerating
				  ) total_count'''
       cursor = connection.cursor()
       cursor.execute(query)
       row = cursor.fetchone()
       return row[0]
    
    def get_articles(self, offset = None, limit = None):
       return self.get_articles_limit()
    
    def get_articles_limit(self, offset = None, limit = None):
       query = '''SELECT core_articleheader.topic_id, core_articleheader.name, core_topic.slug, core_articleheader.order,
						core_articledetails.id, core_articledetails.header_id, core_articledetails.slug, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.likes, core_articledetails.dislikes, core_articledetails.mod_date, core_articledetails.feedback_count
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					WHERE core_articledetails.current IS TRUE AND topic_id = %s
					ORDER BY core_articleheader.order'''

       if offset != None and limit != None:
           query = query + ' OFFSET ' + str(offset) + ' LIMIT ' + str(limit)

       cursor = connection.cursor()
       cursor.execute(query, [self.id])

       articles_list = []
       for row in cursor.fetchall():
           p = ArticleDetails(id=row[4], header_id=row[5], slug=row[6], summary=row[7], _summary_rendered=row[8], likes=row[9], dislikes=row[10], mod_date=row[11], feedback_count=row[12])
           p.topic_id = row[0]
           p.name = row[1]
           p.topic_slug = row[2]
           p.order = row[3]
           articles_list.append(p)
       return articles_list

    def get_mod_date(self):

       query = '''SELECT core_topic.id, MAX(core_articledetails.mod_date) as mod_date
	   			  FROM core_topic INNER JOIN core_articleheader on core_topic.id = core_articleheader.topic_id
				  INNER JOIN core_articledetails on core_articledetails.header_id = core_articleheader.id
				  WHERE core_articledetails.current is true
				  GROUP BY core_topic.id
				  HAVING core_topic.id = %s'''
       cursor = connection.cursor()
       cursor.execute(query, [self.id])
       row = cursor.fetchone()
       return row[1]

    def get_topic_children(self):
        return Topic.objects.filter(parent_id = self.id)

    def draw_me(self):
        if len(self.get_articles()) > 0:
            return True
        for child in self.get_topic_children():
          if child.draw_me():
            return True
        return False

class Chapter(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30, default='')
    slug = models.SlugField(max_length=50, unique=True, help_text="created from name")
    topic = models.ForeignKey(Topic,null = True)
    order = models.IntegerField(blank = True, null = True)

    def __unicode__(self):
        return self.name

class Branch(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30, default='')
    slug = models.SlugField(max_length=50, unique=True, help_text="created from name")
    chapter = models.ForeignKey(Chapter,null = True)
    order = models.IntegerField(blank = True, null = True)

    def __unicode__(self):
        return self.name

class ArticleHeaderManager(models.Manager):
    def get_next(self, topic, order):
       query = '''SELECT core_articleheader.id, core_articleheader.name, core_topic.slug, core_articledetails.slug
					FROM core_articleheader inner join core_articledetails
					ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_topic ON core_topic.id = core_articleheader.topic_id
					WHERE core_articleheader.order > %s AND core_articleheader.topic_id = %s AND core_articledetails.current is true
					ORDER BY core_articleheader.order LIMIT 1'''
       cursor = connection.cursor()
       cursor.execute(query, [order, topic])
       row = cursor.fetchone()
       if(row):
           p = self.model(id=row[0], name=row[1])
           p.slug = row[3]
           p.topic_slug = row[2]
           return p
       else:
           return None
    
    def get_prev(self, topic, order):
       query = '''SELECT core_articleheader.id, core_articleheader.name, core_topic.slug, core_articledetails.slug
					FROM core_articleheader inner join core_articledetails
					ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_topic ON core_topic.id = core_articleheader.topic_id
					WHERE core_articleheader.order < %s AND core_articleheader.topic_id = %s AND core_articledetails.current is true
					ORDER BY core_articleheader.order Desc LIMIT 1'''
       cursor = connection.cursor()
       cursor.execute(query, [order, topic])
       row = cursor.fetchone()
       if(row):
           p = self.model(id=row[0], name=row[1])
           p.slug = row[3]
           p.topic_slug = row[2]
           return p
       else:
           return None

class ArticleHeader(models.Model):
    tags = models.ManyToManyField(Tag)
    topic = models.ForeignKey(Topic,null = True)
    chapter = ChainedForeignKey(
        Chapter, 
        chained_field="topic",
        chained_model_field="topic", 
        show_all=False, 
        auto_choose=False,
        blank=True,
        null=True
    )
    branch = ChainedForeignKey(
        Branch, 
        chained_field="chapter",
        chained_model_field="chapter", 
        show_all=False, 
        auto_choose=False,
        blank=True,
        null=True
    )
    name = models.CharField(max_length=40)
    order = models.IntegerField(blank = True, null = True)
    objects = ArticleHeaderManager()

    def clean(self):
        if len(self.name) >= 40:
            raise exceptions.ValidationError('Too many characters ...')
        return self.name

    def get_original(self):
        versions = self.articledetails_set.all().order_by('id')
        return versions[0]

    class Meta:
       verbose_name = "Article"
       verbose_name_plural = "Articles"
       ordering = ["order"]

class ArticleManager(models.Manager):
    def get_top_liked(self, limit):
       query = '''SELECT core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug, core_articledetails.slug, max(core_articledetails.likes) likes
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					WHERE core_articledetails.current IS TRUE
					GROUP BY core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug, core_articledetails.slug
					ORDER BY likes DESC LIMIT %s'''
       cursor = connection.cursor()
       cursor.execute(query, [limit])

       article_list = []
       for row in cursor.fetchall():
           p = self.model(slug=row[5], likes=row[6])
           p.header = ArticleHeader.objects.get(id=row[0])
           p.topic = Topic.objects.get(id=row[2])
           article_list.append(p)
       return article_list

    def get_top_disliked(self, limit):
       query = '''SELECT core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug, core_articledetails.slug, max(core_articledetails.dislikes) dislikes
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					WHERE core_articledetails.current IS TRUE
					GROUP BY core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug, core_articledetails.slug
					ORDER BY dislikes DESC LIMIT %s'''
       cursor = connection.cursor()
       cursor.execute(query, [limit])

       article_list = []
       for row in cursor.fetchall():
           p = self.model(slug=row[5], dislikes=row[6])
           p.header = ArticleHeader.objects.get(id=row[0])
           p.topic = Topic.objects.get(id=row[2])
           article_list.append(p)
       return article_list

    def get_top_commented(self, limit):
       query = '''SELECT core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug, core_articledetails.slug, max(core_articledetails.feedback_count) feedback_count
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					WHERE core_articledetails.current IS TRUE
					GROUP BY core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug, core_articledetails.slug
					ORDER BY feedback_count DESC LIMIT %s'''
       cursor = connection.cursor()
       cursor.execute(query, [limit])

       article_list = []
       for row in cursor.fetchall():
           p = self.model(slug=row[5], feedback_count=row[6])
           p.header = ArticleHeader.objects.get(id=row[0])
           p.topic = Topic.objects.get(id=row[2])
           article_list.append(p)
       return article_list

class ArticleDetails(models.Model):
    header =  models.ForeignKey(ArticleHeader, null = True, blank = True)
    slug   = models.SlugField(max_length=40, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    feedback_count = models.IntegerField(default=0)
    current = models.BooleanField(default=False)
    mod_date = models.DateTimeField(default=timezone.make_aware(datetime.now(),timezone.get_default_timezone()).astimezone(timezone.utc), verbose_name='Modification Date')
    objects = ArticleManager()

    def get_votes(self):
        return Rating.objects.filter(articledetails_id= self.id)

    def get_top_feedback(self):
        inactive_users = User.get_inactive
        feedback = Feedback.objects.filter(articledetails_id= self.id).order_by('-order').exclude(user__in=inactive_users)[:1]
        if len(feedback) == 1:
            return feedback[0]
        else:
            return None
    
    def __unicode__(self):
        return self.slug
    
    def get_absolute_url(self):
        return "%s/" % (self.slug)

    def is_original(self):
        versions = self.header.articledetails_set.all().order_by('id')
        if self.id == versions[0].id:
            return True
        else:
            return False

    def get_current_version(self):
        return self.header.articledetails_set.get(current = True)

    class Meta:
       verbose_name = "Article Text"
       verbose_name_plural = "Article Texts"

exclusive_boolean_fields(ArticleDetails, ('current',), ('header',))

class Feedback(models.Model):
    parent = models.ForeignKey("self",blank=True,null=True)
    name = models.CharField(max_length=200)
    email = models.SlugField(default='')
    suggestion = MarkupField(default='')
    date = models.DateTimeField( auto_now_add=True, default=datetime.now() ,blank=True,null=True)
    order = models.IntegerField(default=0)
    user = models.CharField(max_length=200,default='')
    articledetails = models.ForeignKey(ArticleDetails, null = True, blank = True)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)

    def get_children(self):
        query = '''SELECT core_feedback.*
					FROM core_feedback INNER JOIN auth_user ON core_feedback.user = auth_user.username
					WHERE core_feedback.parent_id = %s AND auth_user.is_active IS TRUE ORDER BY core_feedback.id'''
        cursor = connection.cursor()
        cursor.execute(query, [self.id])
        return [Feedback(*i) for i in cursor.fetchall()]

class Rating(models.Model):
    articledetails = models.ForeignKey(ArticleDetails, null = True, blank = True)
    feedback = models.ForeignKey(Feedback)
    user = models.CharField(max_length=200,default='')
    vote = models.BooleanField()

class ArticleRating(models.Model):
    articledetails = models.ForeignKey(ArticleDetails, null = True, blank = True)
    user = models.CharField(max_length=200,default='')
    vote = models.BooleanField()

class Info(models.Model):
    name = models.CharField(max_length=40)
    slug     = models.SlugField(max_length=40, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')

    def clean(self):
        if len(self.name) >= 40:
            raise exceptions.ValidationError('Too many characters ...')
        return self.name
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return "/%s/" % (self.slug)

class ReadOnlyWidget(forms.Widget):
    def __init__(self, original_value, display_value):
        self.original_value = original_value
        self.display_value = display_value

        super(ReadOnlyWidget, self).__init__()

    def render(self, name, value, attrs=None):
        if self.display_value is not None:
            return unicode(self.display_value)
        return unicode(self.original_value)

    def value_from_datadict(self, data, files, name):
        return self.original_value

class ReadOnlyAdminFields(object):
    def get_form(self, request, obj=None):
        form = super(ReadOnlyAdminFields, self).get_form(request, obj)

        if hasattr(self, 'readonly'):
            for field_name in self.readonly:
                if field_name in form.base_fields:

                    if hasattr(obj, 'get_%s_display' % field_name):
                        display_value = getattr(obj, 'get_%s_display' % field_name)()
                    else:
                        display_value = None

                    form.base_fields[field_name].widget = ReadOnlyWidget(getattr(obj, field_name, ''), display_value)
                    form.base_fields[field_name].required = False

        return form


@classmethod
def get_top_users(self, limit):
    query = '''SELECT username, first_name, last_name, count(core_feedback.*) contribution
				FROM auth_user INNER JOIN core_feedback ON auth_user.username = core_feedback.user
				GROUP BY username, first_name, last_name, is_active
				HAVING is_active IS TRUE ORDER BY contribution DESC LIMIT %s'''
    cursor = connection.cursor()
    cursor.execute(query, [limit])

    users_list = []
    for row in cursor.fetchall():
        p = User(username=row[0], first_name=row[1], last_name=row[2])
        p.contribution = row[3]
        users_list.append(p)
    return users_list


@classmethod
def get_inactive(self):
    all_result = User.objects.filter(is_active=False).values('username')
    inactive = []
    for result in all_result:
        inactive.append(str(result['username']))
    
    return inactive


User.add_to_class('get_inactive', get_inactive)
User.add_to_class('get_top_users', get_top_users)