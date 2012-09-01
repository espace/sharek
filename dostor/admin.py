from dostor.models import Tag
from dostor.models import Article
from dostor.models import Topic
from dostor.models import Info, Feedback
import ReadOnlyAdminFields

from django.contrib import admin


class ArticleInlineAdmin(admin.TabularInline):
    model      = Article
    extra      = 0
    can_delete = True
    fields     = [ 'tags','topic' ,'name','slug','summary']

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

from django import forms

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
    
admin.site.register(Article, ArticleAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Info, InfoAdmin)
admin.site.register(Feedback, FeedbackAdmin)