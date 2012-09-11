import csv
from django.http import HttpResponse
from django.db.models.signals import post_save

"""
an Exclusive Boolean Field means that only one row in the model table
can have that field True at a time...

if you supply names in 'with_fields' then only one row in the model table
where those additional fields match the instance being saved can have
their exclusive boolean fields True at the same time.
"""
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


def export_as_csv_action(description="Export selected objects as CSV file",
                         fields=None, exclude=None, header=True):
    """
    This function returns an export csv action
    'fields' and 'exclude' work like in django ModelForm
    'header' is whether or not to output the column names as the first row
    """
    def export_as_csv(modeladmin, request, queryset):
        """
        Generic csv export admin action.
        based on http://djangosnippets.org/snippets/1697/
        """
        opts = modeladmin.model._meta
        field_names = set([field.name for field in opts.fields])
        if fields:
            fieldset = set(fields)
            field_names = field_names & fieldset
        elif exclude:
            excludeset = set(exclude)
            field_names = field_names - excludeset

        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % unicode(opts).replace('.', '_')

        writer = csv.writer(response)
        if header:
            writer.writerow(list(field_names))
        for obj in queryset:
            writer.writerow([unicode(getattr(obj, field)).encode("utf-8","replace") for field in field_names])
        return response
    export_as_csv.short_description = description
    return export_as_csv