from sharek import settings
import core
import os.path
import subprocess
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
from decimal import Decimal
from django.core.cache import cache
from django.template import Context, loader, RequestContext
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
					FROM core_articleheader_tags
					INNER JOIN core_articleheader ON core_articleheader.id = core_articleheader_tags.articleheader_id
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id AND core_articledetails.current IS TRUE
					INNER JOIN core_articledetails original_articledetails ON original_articledetails.id = core_articledetails.original
					INNER JOIN core_topic ON core_topic.id = core_articleheader.topic_id
					LEFT JOIN core_chapter ON core_articleheader.chapter_id = core_chapter.id
					LEFT JOIN core_branch ON core_articleheader.branch_id = core_branch.id
					WHERE tag_id = %s ORDER BY core_topic.order, coalesce(core_chapter.order, 0), coalesce(core_branch.order, 0), core_articleheader.order'''

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
       cursor.close()
       return articles_list
        
    def get_topics(self, limit = None):
      return self.get_topics_limit()

    def get_topics_limit(self, limit = None):
      if limit != None:
        return self.topic_set.all()[:limit]
      else:
        return self.topic_set.all()

    class Meta:
       ordering = ["order"]

class TopicManager(models.Manager):
    def topics_tree(self):
       query = '''WITH RECURSIVE q AS
					(
						SELECT  t.id, t.name, t.slug, t.order, 1 AS level, t.slug AS topic_slug, COALESCE(t.order, 0)::VARCHAR AS breadcrumb, 
						COUNT(core_articledetails.*) AS articles_count 
						FROM core_topic t inner join core_articleheader on t.id = core_articleheader.topic_id
						INNER JOIN core_articledetails on core_articleheader.id = core_articledetails.header_id
						WHERE t.id = core_articleheader.topic_id AND core_articledetails.current is true
						GROUP BY t.id, t.name, t.slug, t.order
						UNION
						SELECT  c.id, c.name, c.slug, c.order, 2 AS level, t1.slug, COALESCE(t1.order, 0)::VARCHAR || '-' || COALESCE(c.order, 0)::VARCHAR ,0 FROM core_chapter c INNER JOIN core_topic t1 ON c.topic_id = t1.id
						inner join core_articleheader on c.id = core_articleheader.chapter_id
						INNER JOIN core_articledetails on core_articleheader.id = core_articledetails.header_id
						WHERE c.id = core_articleheader.chapter_id AND core_articledetails.current is true
						UNION
						SELECT  b.id, b.name, b.slug, b.order, 3 AS level, t1.slug ,COALESCE(t1.order, 0)::VARCHAR || '-' || COALESCE(c1.order, 0)::VARCHAR || '-' || COALESCE(b.order, 0)::VARCHAR, 0 FROM core_branch b INNER JOIN core_chapter c1 ON b.chapter_id = c1.id INNER JOIN core_topic t1 ON c1.topic_id = t1.id
						inner join core_articleheader on b.id = core_articleheader.branch_id
						INNER JOIN core_articledetails on core_articleheader.id = core_articledetails.header_id
						WHERE b.id = core_articleheader.branch_id AND core_articledetails.current is true
					)
					SELECT * FROM q ORDER BY breadcrumb, q.order'''
       cursor = connection.cursor()
       cursor.execute(query)

       topic_list = []
       for row in cursor.fetchall():
            p = {'name':row[1], 'slug':row[2], 'level':row[4], 'topic_slug':row[5], 'articles_count':row[7]}
            topic_list.append(p)

       cursor.close()
       return topic_list

    def with_counts(self):
       query = '''SELECT core_topic.id, core_topic.short_name, core_topic.name, core_topic.slug, core_topic.order, core_topic.summary, core_topic._summary_rendered,
	   				( SELECT MAX(core_articledetails.mod_date) as articles_count FROM core_articleheader INNER JOIN core_articledetails on core_articleheader.id = core_articledetails.header_id WHERE core_topic.id = core_articleheader.topic_id AND core_articledetails.current is true ),
					( SELECT COUNT(core_articledetails.*) as articles_count FROM core_articleheader INNER JOIN core_articledetails on core_articleheader.id = core_articledetails.header_id WHERE core_topic.id = core_articleheader.topic_id AND core_articledetails.current is true ) as headers
				  FROM core_topic ORDER BY core_topic.order '''
       cursor = connection.cursor()
       cursor.execute(query)

       topic_list = []
       for row in cursor.fetchall():
           p = self.model(id=row[0], short_name=row[1], name=row[2], slug=row[3], order=row[4], summary=row[5], _summary_rendered=row[6])
           p.date_articles = row[7]
           p.count_articles = row[8]
           topic_list.append(p)

       cursor.close()
       return topic_list
   
   # by Amr
    def get_latest_topics(self, limit):
      query = '''SELECT DISTINCT ON (core_topic.id, core_topic.name) core_topic.name, core_topic.id, core_topic.slug, core_suggestion.description, core_articledetails.mod_date
                 FROM core_topic
                 INNER JOIN core_articleheader ON core_articleheader.topic_id = core_topic.id
                 INNER JOIN core_articledetails ON core_articledetails.header_id = core_articleheader.id
                 INNER JOIN core_suggestion ON core_suggestion.articledetails_id = core_articledetails.id
                 WHERE core_articledetails.current IS TRUE
                 ORDER BY core_topic.id DESC limit %s'''
          
      cursor = connection.cursor()
      cursor.execute(query, [limit])

      topics_list = []
      for row in cursor.fetchall():
         single_topic = {}
         single_topic['name'] = row[0]
         single_topic['slug'] = row[2]
         single_topic['description'] = row[3]
         single_topic['mod_date'] = row[4]
         topics_list.append(single_topic)
      cursor.close()
      return topics_list

class Topic(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30, default='')
    slug = models.SlugField(max_length=50, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')
    order = models.IntegerField(blank = True, null = True)
    tags = models.ManyToManyField(Tag,blank = True, null = True)
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
					SELECT COUNT(*) FROM core_suggestionvotes
				  ) total_count'''
       cursor = connection.cursor()
       cursor.execute(query)
       row = cursor.fetchone()
       cursor.close()
       value = row[0]
       return Decimal(value.to_eng_string())
    
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
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					LEFT JOIN core_chapter ON core_articleheader.chapter_id = core_chapter.id
					LEFT JOIN core_branch ON core_articleheader.branch_id = core_branch.id
					WHERE core_articledetails.current IS TRUE AND core_articleheader.topic_id = %s
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
       cursor.close()
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
       cursor.close()
       return row[1]

    class Meta:
       ordering = ["order"]

class Chapter(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30, default='')
    slug = models.SlugField(max_length=50, unique=True, help_text="created from name")
    topic = models.ForeignKey(Topic,null = True)
    order = models.IntegerField(blank = True, null = True)

    def __unicode__(self):
        return self.name

    class Meta:
       ordering = ["order"]

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
						core_articleheader.chapter_id, core_chapter.name, core_articleheader.branch_id, core_branch.name, core_topic.name,
						core_branch.slug, core_chapter.slug, core_articledetails.original, original_articledetails.slug
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_articledetails original_articledetails ON original_articledetails.id = core_articledetails.original
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
       cursor.close()
       return articles_list

    def get_article(self, slug):
      query = '''SELECT core_articleheader.topic_id, core_articleheader.name AS article_name, core_topic.slug, core_articleheader.order,
          core_articledetails.id, core_articledetails.header_id, core_articledetails.slug, 
          core_articledetails.mod_date, core_articledetails.feedback_count,core_articleheader.chapter_id, core_chapter.name,
          core_articleheader.branch_id, core_branch.name, core_topic.name AS topic_name,
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
      cursor.close()
      if(row):
         p = ArticleDetails(id=row[4], header_id=row[5], slug=row[6], mod_date=row[7], feedback_count=row[8], original=row[16])
         p.topic_id = row[0]
         p.name = row[1]
         p.topic_slug = row[2]
         p.order = row[3]
         p.chapter_id = row[9]
         p.chapter_name = row[10]
         p.branch_id = row[11]
         p.branch_name = row[12]
         p.topic_name = row[13]
         p.branch_slug = row[14]
         p.chapter_slug = row[15]
         p.original_slug = row[17]
         return p
      else: 
        return None

    def get_next_art(self,order):
      query ='''SELECT core_articleheader.name,core_articleheader.id,core_articleheader.order
        FROM core_articledetails,core_articleheader 
        WHERE core_articledetails.header_id = core_articleheader.id
        and core_articledetails.current = TRUE
        and core_articleheader.order > %s
        GROUP BY core_articleheader.name,core_articleheader.order,core_articleheader.id
        ORDER BY 3 LIMIT 1'''
      cursor = connection.cursor()
      cursor.execute(query, [order])
      return cursor.fetchone()

    def get_prev_art(self,order):
      query ='''SELECT core_articleheader.name,core_articleheader.id,core_articleheader.order
        FROM core_articledetails,core_articleheader 
        WHERE core_articledetails.header_id = core_articleheader.id
        and core_articledetails.current = TRUE
        and core_articleheader.order < %s
        GROUP BY core_articleheader.name,core_articleheader.order,core_articleheader.id
        ORDER BY 3 DESC LIMIT 1'''
      cursor = connection.cursor()
      cursor.execute(query, [order])
      return cursor.fetchone()

    def get_history_chart(self,header_id):
      query ='''WITH RECURSIVE w AS (
        SELECT core_articleheader.name,core_articledetails.mod_date,core_articledetails.id , SUM(core_suggestion.likes) as likes,SUM(core_suggestion.dislikes) as dislikes
        FROM core_articledetails, core_suggestion,core_articleheader 
        WHERE core_suggestion.articledetails_id = core_articledetails.id
        and core_articledetails.header_id = core_articleheader.id
        and core_articledetails.header_id = %s
        GROUP BY core_articleheader.name,core_articledetails.id,core_articledetails.mod_date
        ORDER BY core_articledetails.mod_date
        ) select name, id, round((1.0*likes)/nullif(likes+dislikes,0) * 100,1) as likes, round((1.0*dislikes)/nullif(likes+dislikes,0) * 100,1) as dislikes from w'''
      cursor = connection.cursor()
      cursor.execute(query, [header_id])
      return cursor.fetchall()

    def get_first(self):
      query ='''SELECT core_articleheader.id
        FROM core_articledetails,core_articleheader 
        WHERE core_articledetails.header_id = core_articleheader.id
        and core_articledetails.current = TRUE
        ORDER BY core_articleheader.order LIMIT 1'''
      cursor = connection.cursor()
      cursor.execute(query)
      return cursor.fetchone()

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
       cursor.close()
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
       cursor.close()
       if(row):
           p = self.model(id=row[0], name=row[1])
           p.slug = row[3]
           p.topic_slug = row[2]
           return p
       else:
           return None

    def acceptance_chart(self):
      query = '''SELECT core_articleheader.order,core_articleheader.name, core_articledetails.slug AS article_slug , core_topic.slug AS topic_slug
        ,SUM(core_suggestion.likes)AS likes 
        ,SUM(core_suggestion.dislikes) AS dislikes
        ,SUM(core_suggestion.likes)-SUM(core_suggestion.dislikes) AS acceptance
        ,SUM(core_suggestion.likes)+SUM(core_suggestion.dislikes) AS total
        from core_articleheader,core_suggestion,core_articledetails ,core_topic
        where core_articledetails.current=TRUE and core_suggestion.articledetails_id = core_articledetails.id 
        and core_articledetails.header_id=core_articleheader.id
        and core_articleheader.topic_id = core_topic.id
        group by core_articleheader.name,core_articleheader.order,core_articledetails.slug,core_topic.slug ORDER BY 1'''
      cursor = connection.cursor()
      cursor.execute(query)
      return cursor.fetchall()

    def get_approved_count(self):
      q = ''' SELECT COUNT(acceptance) from (SELECT core_articleheader.order,core_articleheader.name
        ,SUM(core_suggestion.likes)-SUM(core_suggestion.dislikes) AS acceptance
        from core_articleheader,core_suggestion,core_articledetails ,core_topic
        where core_articledetails.current=TRUE and core_suggestion.articledetails_id = core_articledetails.id 
        and core_articledetails.header_id=core_articleheader.id
        and core_articleheader.topic_id = core_topic.id
        group by core_articleheader.name,core_articleheader.order,core_articledetails.slug,core_topic.slug ORDER BY 1) gg WHERE acceptance >= 0'''

      cursor = connection.cursor()
      cursor.execute(q)
      row = cursor.fetchone()
      cursor.close()
      p = row[0]
      return p

    def get_refused_count(self):
      q = ''' SELECT COUNT(acceptance) from (SELECT core_articleheader.order,core_articleheader.name
        ,SUM(core_suggestion.likes)-SUM(core_suggestion.dislikes) AS acceptance
        from core_articleheader,core_suggestion,core_articledetails ,core_topic
        where core_articledetails.current=TRUE and core_suggestion.articledetails_id = core_articledetails.id 
        and core_articledetails.header_id=core_articleheader.id
        and core_articleheader.topic_id = core_topic.id
        group by core_articleheader.name,core_articleheader.order,core_articledetails.slug,core_topic.slug ORDER BY 1) gg WHERE acceptance < 0'''

      cursor = connection.cursor()
      cursor.execute(q)
      row = cursor.fetchone()
      cursor.close()
      p = row[0]
      return p
    
class ArticleHeader(models.Model):
    tags = models.ManyToManyField(Tag,blank = True, null = True)
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
    
    # by Amr
    def get_latest(self, limit):
      query = '''SELECT core_articleheader.topic_id, core_articleheader.name, core_topic.slug, core_articleheader.order,
                core_articledetails.id, core_articledetails.header_id, core_articledetails.slug, core_articledetails.summary, core_articledetails._summary_rendered,
                core_articledetails.likes, core_articledetails.dislikes, core_articledetails.mod_date, core_articledetails.feedback_count,
                core_articleheader.chapter_id, core_chapter.name, core_articleheader.branch_id, core_branch.name, core_topic.name,
                core_branch.slug, core_chapter.slug, core_articledetails.original
              FROM core_articleheader
              INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
              INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
              LEFT JOIN core_chapter ON core_articleheader.chapter_id = core_chapter.id
              LEFT JOIN core_branch ON core_articleheader.branch_id = core_branch.id
              WHERE core_articledetails.current IS TRUE
              ORDER BY core_articledetails.id desc limit %s'''
          
      cursor = connection.cursor()
      cursor.execute(query, [limit])

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
         articles_list.append(p)
      cursor.close()
      return articles_list
    
    def get_top_liked(self, limit):
       query = '''SELECT core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
	   					core_articledetails.slug, max(core_articledetails.likes) likes, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date, original_articledetails.slug
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_articledetails original_articledetails ON original_articledetails.id = core_articledetails.original
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					WHERE core_articledetails.current IS TRUE
					GROUP BY core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
						core_articledetails.slug, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date, original_articledetails.slug ORDER BY likes DESC LIMIT %s'''
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
           p.original_slug = row[12]
           article_list.append(p)
       cursor.close()    
       return article_list

    def get_top_disliked(self, limit):
       query = '''SELECT core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
	   					core_articledetails.slug, max(core_articledetails.dislikes) dislikes, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date, original_articledetails.slug
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_articledetails original_articledetails ON original_articledetails.id = core_articledetails.original
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					WHERE core_articledetails.current IS TRUE
					GROUP BY core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
						core_articledetails.slug, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date, original_articledetails.slug ORDER BY dislikes DESC LIMIT %s'''
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
           p.original_slug = row[12]
           article_list.append(p)
       cursor.close()
       return article_list

    def get_top_commented(self, limit):
       query = '''SELECT core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
	   					core_articledetails.slug, max(core_articledetails.feedback_count) feedback_count, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date, original_articledetails.slug
					FROM core_articleheader
					INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
					INNER JOIN core_articledetails original_articledetails ON original_articledetails.id = core_articledetails.original
					INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
					WHERE core_articledetails.current IS TRUE
					GROUP BY core_articleheader.id, core_articleheader.name, core_topic.id, core_topic.name, core_topic.slug,
						core_articledetails.slug, core_topic.slug,
						core_articleheader.name, core_articledetails.summary, core_articledetails._summary_rendered,
						core_articledetails.mod_date, original_articledetails.slug
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
           p.original_slug = row[12]
           article_list.append(p)
       cursor.close()
       return article_list

    def get_most_updated(self, limit):
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
              WHERE core_articledetails.current IS TRUE
              ORDER BY core_articledetails.mod_date desc limit %s'''
          
      cursor = connection.cursor()
      cursor.execute(query, [limit])

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
      cursor.close()
      return articles_list

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

    def get_suggestions(self):
        return Suggestion.objects.filter(articledetails_id=self.id)

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
       verbose_name = "Article Detail"
       verbose_name_plural = "Article Details"

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

class FeedbackManager(models.Manager):
    def feedback_charts(self):
       query = '''SELECT name,likes-dislikes AS net_acceptance FROM core_articleheader,core_articledetails WHERE core_articledetails.current=TRUE AND core_articledetails.header_id=core_articleheader.id ORDER BY core_articleheader.order'''
       cursor = connection.cursor()
       cursor.execute(query)

       return cursor.fetchall()

    def top_ranked(self, article_id, limit):
       query = '''SELECT core_feedback.id, core_feedback.name, core_feedback.email, core_feedback.date, core_feedback.order, core_feedback.user,
						core_feedback.suggestion, core_feedback._suggestion_rendered, core_feedback.articledetails_id,
						core_feedback.likes, core_feedback.dislikes, COALESCE(social_auth_usersocialauth.provider, 'facebook') provider,
						count(reply.id)
					FROM core_feedback
					INNER JOIN auth_user on core_feedback.user = auth_user.username
					LEFT JOIN social_auth_usersocialauth on social_auth_usersocialauth.user_id = auth_user.id
					LEFT JOIN core_feedback reply on reply.parent_id = core_feedback.id
					WHERE auth_user.is_active IS TRUE AND core_feedback.parent_id IS NULL AND core_feedback.articledetails_id = %s
					GROUP BY core_feedback.id, core_feedback.name, core_feedback.email, core_feedback.date, core_feedback.order, core_feedback.user,
						core_feedback.suggestion, core_feedback._suggestion_rendered, core_feedback.articledetails_id,
						core_feedback.likes, core_feedback.dislikes, COALESCE(social_auth_usersocialauth.provider, 'facebook')
					ORDER BY core_feedback.likes - core_feedback.dislikes DESC, id LIMIT %s'''
       cursor = connection.cursor()
       cursor.execute(query, [article_id, limit])

       feedback_list = []

       for row in cursor.fetchall():
           p = self.model(id=row[0], name=row[1], email=row[2], date=row[3], order=row[4], user=row[5], suggestion=row[6], _suggestion_rendered=row[7], articledetails_id=row[8], likes=row[9], dislikes=row[10])
           p.provider = row[11]
           p.children = row[12]

           feedback_list.append(p)

       cursor.close()
       return feedback_list

    def feedback_list(self, article_id, order, offset):
       query = '''SELECT core_feedback.id, core_feedback.name, core_feedback.email, core_feedback.date, core_feedback.order, core_feedback.user,
						core_feedback.suggestion, core_feedback._suggestion_rendered, core_feedback.articledetails_id,
						core_feedback.likes, core_feedback.dislikes, COALESCE(social_auth_usersocialauth.provider, 'facebook') provider,
						count(reply.id)
					FROM core_feedback
					INNER JOIN auth_user on core_feedback.user = auth_user.username
					LEFT JOIN social_auth_usersocialauth on social_auth_usersocialauth.user_id = auth_user.id
					LEFT JOIN core_feedback reply on reply.parent_id = core_feedback.id
					WHERE auth_user.is_active IS TRUE AND core_feedback.parent_id IS NULL AND core_feedback.articledetails_id = %s
					GROUP BY core_feedback.id, core_feedback.name, core_feedback.email, core_feedback.date, core_feedback.order, core_feedback.user,
						core_feedback.suggestion, core_feedback._suggestion_rendered, core_feedback.articledetails_id,
						core_feedback.likes, core_feedback.dislikes, COALESCE(social_auth_usersocialauth.provider, 'facebook')
					ORDER BY '''

       if order == 'order':
             query += "core_feedback.likes - core_feedback.dislikes DESC"
       else:
             query += "id DESC"

       query += " , id OFFSET %s"

       cursor = connection.cursor()
       cursor.execute(query, [article_id, offset])

       feedback_list = []

       for row in cursor.fetchall():
           p = self.model(id=row[0], name=row[1], email=row[2], date=row[3], order=row[4], user=row[5], suggestion=row[6], _suggestion_rendered=row[7], articledetails_id=row[8], likes=row[9], dislikes=row[10])
           p.provider = row[11]
           p.children = row[12]

           feedback_list.append(p)

       cursor.close()
       return feedback_list
   
    # by Amr
    def get_latest_comments(self, limit):
       query = '''SELECT auth_user.username, auth_user.first_name, auth_user.last_name, core_feedback.id, core_feedback.suggestion, core_articleheader.name, core_articledetails.mod_date,COALESCE(social_auth_usersocialauth.provider, 'facebook') as provider
                  FROM core_feedback
                  INNER JOIN auth_user ON core_feedback.user = auth_user.username
                  INNER JOIN core_articledetails ON core_articledetails.id = core_feedback.articledetails_id
                  INNER JOIN core_articleheader ON core_articledetails.header_id = core_articleheader.id
                  LEFT JOIN social_auth_usersocialauth on social_auth_usersocialauth.user_id = auth_user.id
                  GROUP BY auth_user.username, auth_user.first_name, auth_user.last_name, core_feedback.id,
                  social_auth_usersocialauth.provider, auth_user.is_active, core_articleheader.name, core_articledetails.mod_date
                  HAVING auth_user.is_active IS TRUE AND core_feedback.parent_id IS NULL ORDER BY core_feedback.id DESC LIMIT %s '''
       cursor = connection.cursor()
       cursor.execute(query, [limit])

       feedback_list = []

       for row in cursor.fetchall():
           p = self.model(id=row[3])
           p.username = row[0]
           p.first_name = row[1]
           p.last_name = row[2]
           p.my_suggestion = row[4]
           p.article_name = row[5]
           p.mod_date = row[6]
           p.provider = row[7]
           
           feedback_list.append(p)

       cursor.close()
       return feedback_list

class Feedback(models.Model):
    parent = models.ForeignKey("self",blank=True,null=True)
    name = models.CharField(max_length=200)
    email = models.SlugField(default='')
    suggestion = MarkupField(default='')
    date = models.DateTimeField( auto_now_add=True, default=datetime.now() ,blank=True,null=True)
    order = models.IntegerField(default=0)
    user = models.CharField(max_length=200,default='')
    commenter = models.ForeignKey(User, null = True)
    articledetails = models.ForeignKey(ArticleDetails, null = True, blank = True)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    objects = FeedbackManager()

    def get_children(self):
        query = '''SELECT core_feedback.id, core_feedback.name, core_feedback.email, core_feedback.date, core_feedback.order, core_feedback.user,
						core_feedback.suggestion, core_feedback._suggestion_rendered, core_feedback.articledetails_id,
						core_feedback.likes, core_feedback.dislikes, COALESCE(social_auth_usersocialauth.provider, 'facebook') provider
					FROM core_feedback
					INNER JOIN auth_user on core_feedback.user = auth_user.username
					LEFT JOIN social_auth_usersocialauth on social_auth_usersocialauth.user_id = auth_user.id
					WHERE auth_user.is_active IS TRUE AND parent_id = %s
					ORDER BY id DESC'''

        cursor = connection.cursor()
        cursor.execute(query, [self.id])

        replies_list = []

        for row in cursor.fetchall():
            p = Feedback(id=row[0], name=row[1], email=row[2], date=row[3], order=row[4], user=row[5], suggestion=row[6], _suggestion_rendered=row[7], articledetails_id=row[8], likes=row[9], dislikes=row[10])
            p.provider = row[11]

            replies_list.append(p)

        cursor.close()
        return replies_list

class Rating(models.Model):
    articledetails = models.ForeignKey(ArticleDetails, null = True, blank = True)
    feedback = models.ForeignKey(Feedback)
    user = models.CharField(max_length=200,default='')
    voter = models.ForeignKey(User, null = True)
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
    query = '''SELECT username, first_name, last_name, count(core_feedback.*) contribution, COALESCE(social_auth_usersocialauth.provider, 'facebook') as provider
				FROM auth_user INNER JOIN core_feedback ON auth_user.username = core_feedback.user
				LEFT JOIN social_auth_usersocialauth on social_auth_usersocialauth.user_id = auth_user.id
				GROUP BY username, first_name, last_name, is_active, social_auth_usersocialauth.provider
				HAVING is_active IS TRUE ORDER BY contribution DESC LIMIT %s'''
    cursor = connection.cursor()
    cursor.execute(query, [limit])

    users_list = []
    for row in cursor.fetchall():
        p = User(username=row[0], first_name=row[1], last_name=row[2])
        p.contribution = row[3]
        users_list.append(p)
    cursor.close()
    return users_list

@classmethod
def get_inactive(self):
    all_result = User.objects.filter(is_active=False).values('username')
    inactive = []
    for result in all_result:
        inactive.append(str(result['username']))
    
    return inactive

@classmethod
def users_chart(self):
   query = '''SELECT to_char("date_joined",'mm/yyyy') AS month, count(*) AS users FROM auth_user GROUP BY to_char("date_joined",'mm/yyyy')  ORDER BY to_char("date_joined",'mm/yyyy')'''
   cursor = connection.cursor()
   cursor.execute(query)

   return cursor.fetchall()

User.add_to_class('get_inactive', get_inactive)
User.add_to_class('get_top_users', get_top_users)
User.add_to_class('users_chart', users_chart)

class Suggestion(models.Model):
    articledetails = models.ForeignKey(ArticleDetails)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    description = MarkupField(default='', null = True, blank = True)
    image = models.ImageField(upload_to="suggestions/", blank=True)
    video = models.CharField(max_length=12,default='',help_text="The Youtube video code, ex: oq6Yij-hnGo ", null = True, blank = True)
    poll_total_count = models.IntegerField(default=0)
    date = models.DateTimeField( auto_now_add=True, default=datetime.now() ,blank=True,null=True)

    def get_poll_options(self):
      options = PollOptions.objects.filter(suggestions_id = self.id)
      return options

    class Meta:
      get_latest_by = 'id'

class SuggestionVotes(models.Model):
    suggestions = models.ForeignKey(Suggestion)    
    user = models.CharField(max_length=200,default='')
    vote = models.BooleanField()

class PollOptions(models.Model):
    suggestions = models.ForeignKey(Suggestion)
    option = models.CharField(max_length=1024,default='')
    count = models.IntegerField(default=0)

class PollResult(models.Model):
    option = models.ForeignKey(PollOptions)    
    user = models.ForeignKey(User)

# store the term idf per article
class article_idf(models.Model):
  articledetail = models.ForeignKey(ArticleDetails)
  term = models.CharField(max_length=200,default='')
  idf = models.FloatField()

# store the term idf across the whole articles
class idf(models.Model):
  term = models.CharField(max_length=200,default='')
  idf = models.FloatField()
