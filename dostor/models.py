from django.db import models
from markitup.fields import MarkupField

class Tag(models.Model):
    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=30, unique=True, help_text="created from name")
    photo = models.ImageField(upload_to="dostor/static/photos/", blank=True)
    summary = MarkupField(blank=True, default='')

    def __unicode__(self):
        #return u'%s - %s' % (self.topic.name, self.name)
        return self.name

    def get_absolute_url(self):
        return "/%s" % (self.slug)
    
    def get_articles(self):
        return Article.objects.filter(tag_id= self.id)
        
    class Meta:
       ordering = ["name"]
       
class Article(models.Model):
    tags = models.ManyToManyField(Tag)
    name = models.CharField(max_length=40)
    slug 	 = models.SlugField(max_length=40, unique=True, help_text="created from name")
    summary = MarkupField(blank=True, default='')
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return "/%s/%s/" % (self.tag.slug ,self.slug)

    class Meta:
       ordering = ["name"]       
