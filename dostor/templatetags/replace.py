import re 

from django import template
register = template.Library()

@register.filter
def replace ( string, args ): 
    arg_list = [arg.strip() for arg in args.split(',')]
    search  = arg_list[0]
    replace = arg_list[1]
    path = str(string)
    return re.sub( search, replace, path )
    
key = register.filter('replace', replace)
