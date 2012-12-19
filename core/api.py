from core.models import Topic

from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.resources import Resource, ModelResource


class ArticlesResource(ModelResource):
    class Meta:
        resource_name = 'articles'


class TopicsResource(Resource):
    id = fields.IntegerField(attribute = 'id')
    name = fields.CharField(attribute = 'name')
    count_articles = fields.IntegerField(attribute = 'count_articles')
    summary = fields.CharField(attribute = 'summary')
    
    class Meta:
        resource_name = 'topics'
        fields = ['id', 'count_articles', 'name', 'summary']

    # adapted this from ModelResource
    def get_resource_uri(self, bundle_or_obj):
        kwargs = {
            'resource_name': 'articles' #self._meta.resource_name,
        }

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.id # pk is referenced in ModelResource
        else:
            kwargs['pk'] = bundle_or_obj.id
        
        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name
        
        return self._build_reverse_url('api_dispatch_detail', kwargs = kwargs)

    def get_object_list(self, request):
        return Topic.objects.with_counts()

    def obj_get_list(self, request = None, **kwargs):
        return self.get_object_list(request)
