from django import forms
from django.utils import timezone
from datetime import datetime
from markitup.fields import MarkupField
from django.core import exceptions
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.signals import post_save
from django.db.models.aggregates import Max
from django.db.models import signals
from core.actions import exclusive_boolean_fields
from django.db import connection, models
from django import db

#from tinymce import models as tinymce_models

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
    
    def get_articles(self, offset = None, limit = None):
       return self.get_articles_limit()
    
    def get_articles_limit(self, offset = None, limit = None):
       query = '''SELECT core_articleheader.topic_id, core_articleheader.name, core_topic.slug, core_articleheader.order,
						core_articledetails.id, core_articledetails.header_id, core_articledetails.slug, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.likes, core_articledetails.dislikes, core_articledetails.mod_date, core_articledetails.feedback_count,
						core_articleheader.chapter_id, core_chapter.name, core_articleheader.branch_id, core_branch.name, core_topic.name,
						core_articledetails.original, original_articledetails.slug
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_articledetails original_articledetails ON original_articledetails.id = core_articledetails.original
					INNER JOIN core_articleheader_tags ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_tag ON core_tag.id = core_articleheader_tags.tag_id
					INNER JOIN core_topic ON core_articleheader.id = core_articleheader_tags.articleheader_id
					LEFT JOIN core_chapter ON core_articleheader.chapter_id = core_chapter.id
					LEFT JOIN core_branch ON core_articleheader.branch_id = core_branch.id
					WHERE core_articledetails.current IS TRUE AND core_tag.id = %s
					ORDER BY coalesce(core_chapter.order, 0), coalesce(core_branch.order, 0), core_articleheader.order'''

       if offset != None and limit != None:
           query = query + ' OFFSET ' + str(offset) + ' LIMIT ' + str(limit)

       cursor = connection.cursor()
       cursor.execute(query, [self.id])

       articles_list = []
       for row in cursor.fetchall():
           p = ArticleDetails(id=row[4], header_id=row[5], slug=row[6], summary=row[7], _summary_rendered=row[8], likes=row[9], dislikes=row[10], mod_date=row[11], feedback_count=row[12], original = row[18])
           p.topic_id = row[0]
           p.name = row[1]
           p.topic_slug = row[2]
           p.order = row[3]
           p.chapter_id = row[13]
           p.chapter_name = row[14]
           p.branch_id = row[15]
           p.branch_name = row[16]
           p.topic_name = row[17]
           p.original_slug = row[19]
           articles_list.append(p)
       db.reset_queries()
       return articles_list
        
        
    class Meta:
       ordering = ["order"]

class TopicManager(models.Manager):
    def with_counts(self):
       query = '''SELECT core_topic.id, core_topic.name, core_topic.slug, core_topic.order, core_topic.summary, core_topic._summary_rendered,
	   				( SELECT MAX(core_articledetails.mod_date) as articles_count FROM core_articleheader INNER JOIN core_articledetails on core_articleheader.id = core_articledetails.header_id WHERE core_topic.id = core_articleheader.topic_id AND core_articledetails.current is true ),
					( SELECT COUNT(core_articledetails.*) as articles_count FROM core_articleheader INNER JOIN core_articledetails on core_articleheader.id = core_articledetails.header_id WHERE core_topic.id = core_articleheader.topic_id AND core_articledetails.current is true ) as headers
				  FROM core_topic '''
       cursor = connection.cursor()
       cursor.execute(query)

       topic_list = []
       for row in cursor.fetchall():
           p = self.model(id=row[0], name=row[1], slug=row[2], order=row[3], summary=row[4], _summary_rendered=row[5])
           p.date_articles = row[6]
           p.count_articles = row[7]
           topic_list.append(p)
       db.reset_queries()
       return topic_list

class Topic(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30, default='')
    slug = models.SlugField(max_length=50, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')
    order = models.IntegerField(blank = True, null = True)
    objects = TopicManager()

    def __unicode__(self):
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
       db.reset_queries()
       return row[0]

    def get_articles(self, offset = None, limit = None):
       return self.get_articles_limit()
    
    def get_articles_limit(self, offset = None, limit = None):
       query = '''SELECT core_articleheader.topic_id, core_articleheader.name, core_topic.slug, core_articleheader.order,
						core_articledetails.id, core_articledetails.header_id, core_articledetails.slug, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.likes, core_articledetails.dislikes, core_articledetails.mod_date, core_articledetails.feedback_count,
						core_articleheader.chapter_id, core_chapter.name, core_articleheader.branch_id, core_branch.name, core_topic.name,
						core_branch.slug, core_chapter.slug, core_articledetails.original, original_articledetails.slug
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_articledetails original_articledetails ON original_articledetails.id = core_articledetails.original
					INNER JOIN core_articleheader_tags ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_tag ON core_tag.id = core_articleheader_tags.tag_id
					INNER JOIN core_topic ON core_articleheader.id = core_articleheader_tags.articleheader_id
					LEFT  JOIN core_chapter ON core_articleheader.chapter_id = core_chapter.id
					LEFT  JOIN core_branch ON core_articleheader.branch_id = core_branch.id
					WHERE core_articledetails.current IS TRUE AND core_tag.id = %s
					ORDER BY coalesce(core_chapter.order, 0), coalesce(core_branch.order, 0), core_articleheader.order'''

       if offset != None and limit != None:
           query = query + ' OFFSET ' + str(offset) + ' LIMIT ' + str(limit)

       cursor = connection.cursor()
       cursor.execute(query, [self.id])

       articles_list = []
       for row in cursor.fetchall():
           p = ArticleDetails(id=row[4], header_id=row[5], slug=row[6], summary=row[7], _summary_rendered=row[8], likes=row[9], dislikes=row[10], mod_date=row[11], feedback_count=row[12], original=row[20])
           p.topic_id = row[0]
           p.name = row[1]
           p.topic_slug = row[2]
           p.order = row[3]
           p.chapter_id = row[13]
           p.chapter_name = row[14]
           p.branch_id = row[15]
           p.branch_name = row[16]
           p.topic_name = row[17]
           p.branch_slug = row[18]
           p.chapter_slug = row[19]
           p.original_slug = row[21]
           articles_list.append(p)
       db.reset_queries()
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
       db.reset_queries()
       return row[1]

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
    
    def search_articles(self, str_query):
       query = '''SELECT core_articleheader.topic_id, core_articleheader.name, core_topic.slug, core_articleheader.order,
						core_articledetails.id, core_articledetails.header_id, core_articledetails.slug, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.likes, core_articledetails.dislikes, core_articledetails.mod_date, core_articledetails.feedback_count,
						core_articleheader.chapter_id, core_chapter.name, core_articleheader.branch_id, core_branch.name, core_topic.name
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					LEFT JOIN core_chapter ON core_articleheader.chapter_id = core_chapter.id
					LEFT JOIN core_branch ON core_articleheader.branch_id = core_branch.id
					WHERE core_articledetails.current IS TRUE AND core_articleheader.name like %s OR core_articledetails.summary like %s
					ORDER BY coalesce(core_chapter.order, 0), coalesce(core_branch.order, 0), core_articleheader.order'''
       print(query)
       cursor = connection.cursor()
       cursor.execute(query, [str_query, str_query])

       articles_list = []
       for row in cursor.fetchall():
           p = ArticleDetails(id=row[4], header_id=row[5], slug=row[6], summary=row[7], _summary_rendered=row[8], likes=row[9], dislikes=row[10], mod_date=row[11], feedback_count=row[12])
           p.topic_id = row[0]
           p.name = row[1]
           p.topic_slug = row[2]
           p.order = row[3]
           p.chapter_id = row[13]
           p.chapter_name = row[14]
           p.branch_id = row[15]
           p.branch_name = row[16]
           p.topic_name = row[17]
           articles_list.append(p)
       db.reset_queries()
       return articles_list

    def get_article(self, slug):
       query = '''SELECT core_articleheader.topic_id, core_articleheader.name, core_topic.slug, core_articleheader.order,
						core_articledetails.id, core_articledetails.header_id, core_articledetails.slug, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.likes, core_articledetails.dislikes, core_articledetails.mod_date, core_articledetails.feedback_count,
						core_articleheader.chapter_id, core_chapter.name, core_articleheader.branch_id, core_branch.name, core_topic.name,
						core_branch.slug, core_chapter.slug, core_articledetails.original, original_articledetails.slug
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_articledetails original_articledetails ON original_articledetails.id = core_articledetails.original
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					LEFT JOIN core_chapter ON core_articleheader.chapter_id = core_chapter.id
					LEFT JOIN core_branch ON core_articleheader.branch_id = core_branch.id
					WHERE core_articledetails.slug = %s'''
       cursor = connection.cursor()
       cursor.execute(query, [slug])
       row = cursor.fetchone()
       if(row):
           p = ArticleDetails(id=row[4], header_id=row[5], slug=row[6], summary=row[7], _summary_rendered=row[8], likes=row[9], dislikes=row[10], mod_date=row[11], feedback_count=row[12], original=row[20])
           p.topic_id = row[0]
           p.name = row[1]
           p.topic_slug = row[2]
           p.order = row[3]
           p.chapter_id = row[13]
           p.chapter_name = row[14]
           p.branch_id = row[15]
           p.branch_name = row[16]
           p.topic_name = row[17]
           p.branch_slug = row[18]
           p.chapter_slug = row[19]
           p.original_slug = row[21]
           db.reset_queries()
           return p
       else:
           return None

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
           db.reset_queries()
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
           db.reset_queries()
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

    def __unicode__(self):
        return self.name

    def clean(self):
        if len(self.name) >= 40:
            raise exceptions.ValidationError('Too many characters ...')
        return self.name

    class Meta:
       verbose_name = "Article"
       verbose_name_plural = "Articles"
       ordering = ["order"]

class ArticleManager(models.Manager):
    def get_top_liked(self, limit):
       query = '''SELECT core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
	   					core_articledetails.slug, max(core_articledetails.likes) likes, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					WHERE core_articledetails.current IS TRUE
					GROUP BY core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
						core_articledetails.slug, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date ORDER BY likes DESC LIMIT %s'''
       cursor = connection.cursor()
       cursor.execute(query, [limit])

       article_list = []
       for row in cursor.fetchall():
           p = self.model(slug=row[5], likes=row[6])
           p.header = ArticleHeader.objects.get(id=row[0])
           p.topic = Topic.objects.get(id=row[2])
           p.topic_slug = row[7]
           p.name = row[8]
           p.summary = row[9]
           p._summary_rendered = row[10]
           p.mod_date = row[11]
           article_list.append(p)
       db.reset_queries()    
       return article_list

    def get_top_disliked(self, limit):
       query = '''SELECT core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
	   					core_articledetails.slug, max(core_articledetails.dislikes) dislikes, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					WHERE core_articledetails.current IS TRUE
					GROUP BY core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
						core_articledetails.slug, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date					ORDER BY dislikes DESC LIMIT %s'''
       cursor = connection.cursor()
       cursor.execute(query, [limit])

       article_list = []
       for row in cursor.fetchall():
           p = self.model(slug=row[5], dislikes=row[6])
           p.header = ArticleHeader.objects.get(id=row[0])
           p.topic = Topic.objects.get(id=row[2])
           p.topic_slug = row[7]
           p.name = row[8]
           p.summary = row[9]
           p._summary_rendered = row[10]
           p.mod_date = row[11]
           article_list.append(p)
       db.reset_queries()
       return article_list

    def get_top_commented(self, limit):
       query = '''SELECT core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
	   					core_articledetails.slug, max(core_articledetails.feedback_count) feedback_count, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					WHERE core_articledetails.current IS TRUE
					GROUP BY core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
						core_articledetails.slug, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date
					ORDER BY feedback_count DESC LIMIT %s'''
       cursor = connection.cursor()
       cursor.execute(query, [limit])

       article_list = []
       for row in cursor.fetchall():
           p = self.model(slug=row[5], feedback_count=row[6])
           p.header = ArticleHeader.objects.get(id=row[0])
           p.topic = Topic.objects.get(id=row[2])
           p.topic_slug = row[7]
           p.name = row[8]
           p.summary = row[9]
           p._summary_rendered = row[10]
           p.mod_date = row[11]
           article_list.append(p)
       db.reset_queries()
       return article_list

class ArticleDetails(models.Model):
    header =  models.ForeignKey(ArticleHeader, null = True, blank = True)
    slug   = models.SlugField(max_length=40, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    original = models.IntegerField(default=0)
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

def update_original(sender, instance, created, **kwargs):
    if created:
       query = '''UPDATE core_articledetails tt
                    SET original = ( SELECT min(dd.id)
                             FROM core_articledetails dd
                             WHERE dd.header_id = tt.header_id
                             GROUP BY dd.header_id
                            )
                  WHERE tt.id = %s'''
       cursor = connection.cursor()
       cursor.execute(query, [instance.id])

signals.post_save.connect(update_original, sender = ArticleDetails)

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
        db.reset_queries()
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
    db.reset_queries()
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