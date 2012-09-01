from django import forms
from django.db import models
from django.utils import timezone
from datetime import datetime
from markitup.fields import MarkupField
from django.core import exceptions
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.signals import post_save
from django.db.models.aggregates import Max



class Tag(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30, default='')
    slug = models.SlugField(max_length=50, unique=True, help_text="created from name")
    #photo = models.ImageField(upload_to="dostor/static/photos/", blank=True)
    summary = MarkupField(blank=True, default='')
    order = models.IntegerField(blank = True, null = True)

    def __unicode__(self):
        #return u'%s - %s' % (self.topic.name, self.name)
        return self.name

    def get_absolute_url(self):
        return self.slug
    
    def get_articles(self):
        return Article.objects.filter(tag_id= self.id)
        
    class Meta:
       ordering = ["order"]

class Topic(models.Model):
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
        return Article.objects.filter(topic_id= self.id)

    def articles_count(self):
       arts = Article.objects.filter(topic_id= self.id).values('original').annotate(max_id=Max('id')).order_by()
       return len(arts)
    
    class Meta:
       ordering = ["order"]
       
class Article(models.Model):
    tags = models.ManyToManyField(Tag)
    topic = models.ForeignKey(Topic,null = True)
    name = models.CharField(max_length=40)
    slug 	 = models.SlugField(max_length=40, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')
    order = models.IntegerField(blank = True, null = True)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    original = models.ForeignKey("self",null = True, blank = True)
    default = models.BooleanField(default=False)

    def feedback_count(self):
        return len(Feedback.objects.filter(article_id = self.id))

    def get_votes(self):
        return Rating.objects.filter(article_id= self.id)

    def get_top_feedback(self):
        feedback = Feedback.objects.filter(article_id= self.id).order_by('-order')[:1]
        if len(feedback) == 1:
            return feedback[0]
        else:
            return None

    def clean(self):
        if len(self.name) >= 40:
            raise exceptions.ValidationError('Too many characters ...')
        return self.name
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return "%s/" % (self.slug)

    def save(self):
        super(Article, self).save()
        if self.original == None:
            self.original = self
            self.save()
    
    @classmethod
    def get_top_liked(self, limit):
      return Article.objects.order_by('-likes')[:limit]
    
    @classmethod
    def get_top_disliked(self, limit):
      return Article.objects.order_by('-dislikes')[:limit]
    
    @classmethod
    def get_top_commented(self, limit):
      return Article.objects.annotate(num_feedbacks=Count('feedback')).order_by('-num_feedbacks')[:limit]

    class Meta:
       ordering = ["order"]

class Feedback(models.Model):
    article = models.ForeignKey(Article)
    parent = models.ForeignKey("self",blank=True,null=True)
    name = models.CharField(max_length=200)
    email = models.SlugField(default='')
    suggestion = MarkupField(default='')
    date = models.DateTimeField( auto_now_add=True, default=datetime.now() ,blank=True,null=True)
    order = models.IntegerField(default=0)
    user = models.CharField(max_length=200,default='')

    def get_children(self):
        return Feedback.objects.filter(parent_id = self.id).order_by('id')

class Rating(models.Model):
    article = models.ForeignKey(Article)
    feedback = models.ForeignKey(Feedback)
    user = models.CharField(max_length=200,default='')
    vote = models.BooleanField()


class ArticleRating(models.Model):
    article = models.ForeignKey(Article)
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

def exclusive_boolean_handler(sender, instance, created, **kwargs):
    eb_fields = getattr(sender, '_exclusive_boolean_fields', [])
    with_fields = getattr(sender, '_exclusive_boolean_with_fields', [])
    uargs = {}
    for field in eb_fields:
        ifield = getattr(instance, field)
        if ifield == True:
            uargs.update({field:False})
    fargs = {}
    for field in with_fields:
        ifield = getattr(instance, field)
        fargs.update({field:ifield})
    sender.objects.filter(**fargs).exclude(pk=instance.pk).update(**uargs)

def exclusive_boolean_fields(model, eb_fields=[], with_fields=[]):
    setattr(model, '_exclusive_boolean_fields', eb_fields)
    setattr(model, '_exclusive_boolean_with_fields', with_fields)
    post_save.connect(exclusive_boolean_handler, sender=model)

exclusive_boolean_fields(Article, ('default',), ('original',))