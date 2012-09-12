from core.models import Tag
#from core.models import Article
from core.models import Topic
from core.models import Info, Feedback, ArticleDetails, ArticleHeader#, Article
from core.models import ReadOnlyAdminFields
from django.contrib.auth.models import User

from core.actions import export_as_csv_action

from django.contrib import admin

class ArticleDetailsInlineAdmin(admin.TabularInline):
    model      = ArticleDetails
    extra      = 1
    can_delete = True
    fields     = ['slug','summary','current', 'mod_date']


class ArticleHeaderAdmin(admin.ModelAdmin):
    inlines = [ArticleDetailsInlineAdmin,]
    list_display = ('name','topic','order')
    list_filter = ('topic',)
    list_editable = ['order']

    class Media:
        js = ( 'js/jquery.min.js', 'js/jquery-ui.min.js', 'js/admin-list-reorder.js', )

'''
class ArticleInlineAdmin(admin.TabularInline):
    model      = Article
    extra      = 0
    can_delete = True
    fields     = [ 'tags','topic' ,'name','slug','summary','current', 'mod_date','likes', 'dislikes']

class ArticleAdmin(ReadOnlyAdminFields, admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    inlines = [ArticleInlineAdmin,]
    list_display = ('name','original','topic', 'current','order')
    list_filter = ('topic',)
    list_editable = ['order', 'current']
    #readonly = ('likes', 'dislikes',)

    class Media:
        js = ( 'js/jquery.min.js', 'js/jquery-ui.min.js', 'js/admin-list-reorder.js', )
 
'''
class FeedbackAdmin(admin.ModelAdmin):
    #prepopulated_fields = {"user": ["username"]}
    list_filter = ('articledetails',)
    list_display = ('name', 'articledetails','user', 'email', 'suggestion')
    

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

    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def get_actions(self, request):
       actions = super(UserAdmin, self).get_actions(request)
       try:
           del actions['delete_selected']
       except KeyError:
           pass
       return actions
    
#admin.site.register(Article, ArticleAdmin)
admin.site.register(ArticleHeader, ArticleHeaderAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Info, InfoAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
