import os
from django import template
from django.db.models.fields.files import ImageFieldFile
import Image as PImage
from urlparse import urljoin
from os import path

register = template.Library()

class NotImageFieldError(ValueError):
    pass

def get_thumb(imagefield, width, height):
    size = width, height
    pathname, filename = path.split(imagefield.path)
    shortname, extname = path.splitext(filename)
    thumbname = '%s-%dx%d%s' % (shortname, width, height, extname)
    p = path.join(pathname, 'thumbs', thumbname)
    if path.isfile(p):
        pass
    else:
        if not path.isdir(path.dirname(p)):
            os.mkdir(path.dirname(p), 0755)
        img = PImage.open(imagefield.path)
        img.thumbnail(size, PImage.ANTIALIAS)
        img.save(p)

    return urljoin(imagefield.url, 'thumbs/' + thumbname)


def get_rescale(imagefield, width, height):
    pathname, filename = path.split(imagefield.path)
    shortname, extname = path.splitext(filename)
    thumbname = '%s-%dx%d%s' % (shortname, width, height, extname)
    p = path.join(pathname, 'rescaled', thumbname)
    if path.isfile(p):
        pass
    else:
        if not path.isdir(path.dirname(p)):
            os.mkdir(path.dirname(p), 0755)
        img = PImage.open(imagefield.path)
        src_width, src_height = img.size
        src_ratio = float(src_width) / float(src_height)
        dst_ratio = float(width) / float(height)

        if dst_ratio < src_ratio:
            crop_height = src_height
            crop_width = crop_height * dst_ratio
            x_offset = float(src_width - crop_width) / 2
            y_offset = 0
        else:
            crop_width = src_width
            crop_height = crop_width / dst_ratio
            x_offset = 0
            y_offset = float(src_height - crop_height) / 3
        img = img.crop((int(x_offset), int(y_offset), int(x_offset+crop_width), int(y_offset+crop_height)))
        img = img.resize((width, height), PImage.ANTIALIAS)
        img.save(p)

    return urljoin(imagefield.url, 'rescaled/' + thumbname)

class ThumbNail(template.Node):
    def __init__(self, imagestr, width, height, rescale=False):
        self.imagestr = template.Variable(imagestr)
        self.width = width
        self.height = height
        self.rescale = rescale

    def render(self, context):
        image = self.imagestr.resolve(context)
        if not isinstance(image, ImageFieldFile):
            raise NotImageFieldError, '%s is not an instance of ImageFieldFile.' % self.imagestr
        if self.rescale:
            self.url = get_rescale(image, self.width, self.height)
        else:
            self.url = get_thumb(image, self.width, self.height)
        return self.url

@register.tag(name='thumb')
def do_thumb(parser, token):
    try:
        tagname, imagestr, widthstr, heightstr, rescalestr = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly 4 arguments" % token.contents.split()[0]
    try:
        width = int(widthstr)
        height = int(heightstr)
        if rescalestr in ('1', 'yes', 'true', 'True'):
            rescale = True
        else:
            rescale = False
    except ValueError:
        raise template.TemplateSyntaxError, 'Arguments error in tag %r' % token.contents.split()[0]
    return ThumbNail(imagestr, width, height, rescale)