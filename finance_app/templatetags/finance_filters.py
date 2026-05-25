from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """Split a string by the given separator"""
    return str(value).split(arg)

@register.filter  
def get_item(lst, index):
    """Get item from list by index"""
    try:
        return lst[index]
    except (IndexError, TypeError):
        return ''
    