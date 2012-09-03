from dostor.models import Tag
from dostor.models import Article
from dostor.models import Topic
from dostor.models import Info, Feedback
from dostor.models import ReadOnlyAdminFields
from django.contrib.auth.models import User

from dostor.actions import export_as_csv_action

from django.contrib import admin


class ArticleInlineAdmin(admin.TabularInline):
    model      = Article
    extra      = 0
    can_delete = True
    fields     = [ 'tags','topic' ,'name','slug','summary','default', 'mod_date']

class ArticleAdmin(ReadOnlyAdminFields, admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    inlines = [ArticleInlineAdmin,]
    list_display = ('name','original','topic', 'default','order')
    list_filter = ('topic',)
    list_editable = ['order', 'default']
    #readonly = ('likes', 'dislikes',)

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

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username' ,'first_name', 'last_name', 'is_staff', 'is_active')
    list_editable = ['is_staff', 'is_active']
    list_filter = ('is_staff', 'is_active')
    
admin.site.register(Article, ArticleAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Info, InfoAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
