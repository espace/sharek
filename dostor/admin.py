from dostor.models import Tag
from dostor.models import Article
from dostor.models import Topic
from dostor.models import Info, Feedback
from dostor.models import ReadOnlyAdminFields

from django.contrib import admin


class ArticleInlineAdmin(admin.TabularInline):
    model      = Article
    extra      = 0
    can_delete = True
    fields     = [ 'tags','topic' ,'name','slug','summary','original']

class ArticleAdmin(ReadOnlyAdminFields, admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    inlines = [ArticleInlineAdmin,]
    list_display = ('name','topic','original','order')
    list_filter = ('topic',)
    list_editable = ['order']
    readonly = ('likes', 'dislikes',)

    class Media:
        js = ( 'js/jquery.min.js', 'js/jquery-ui.min.js', 'js/admin-list-reorder.js', )
    

class FeedbackAdmin(admin.ModelAdmin):
    #prepopulated_fields = {"user": ["username"]}
    list_filter = ('article',)
    list_display = ('name', 'article','user', 'email', 'suggestion')
    

class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ('short_name','name','order')
    list_editable = ['order']

    class Media:
        js = ( 'js/jquery.min.js', 'js/jquery-ui.min.js', 'js/admin-list-reorder.js', )

class TopicAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ('name','short_name','order')
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
admin.site.register(Feedback, FeedbackAdmin)