from dostor.models import Tag
from dostor.models import Article
from dostor.models import Topic
from dostor.models import Info

from django.contrib import admin

class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ('name','order')
    list_filter = ('tags',)
    list_editable = ['order']

    class Media:
        js = ( 'js/jquery.min.js', 'js/jquery-ui.min.js', 'js/admin-list-reorder.js', )
    

class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ('short_name','name','order')
    list_editable = ['order']

    class Media:
        js = ( 'js/jquery.min.js', 'js/jquery-ui.min.js', 'js/admin-list-reorder.js', )

class TopicAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ('short_name','name','order')
    list_editable = ['order']

    class Media:
        js = ( 'js/jquery.min.js', 'js/jquery-ui.min.js', 'js/admin-list-reorder.js', )

class InfoAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ('name',)

    class Media:
        js = ( 'js/jquery.min.js', 'js/jquery-ui.min.js', 'js/admin-list-reorder.js', )
    
admin.site.register(Article, ArticleAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Info, InfoAdmin)
