from dostor.models import Tag
from dostor.models import Article

from django.contrib import admin


class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ('name',)
    list_filter = ('tags',)
    

class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ('name',)
    
admin.site.register(Article, ArticleAdmin)
admin.site.register(Tag, TagAdmin)
