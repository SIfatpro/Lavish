# products/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Returns the value for the given key from a dictionary.
    Usage: {{ dictionary|get_item:key }}
    """
    try:
        return dictionary.get(key)
    except (TypeError, AttributeError):
        return None
 