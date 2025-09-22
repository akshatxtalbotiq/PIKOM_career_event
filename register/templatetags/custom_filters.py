# templatetags/custom_filters.py
import json
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using a key.
    Usage: {{ mydict|get_item:key }}
    """
    if dictionary and key is not None:
        return dictionary.get(key)
    return None

@register.filter
def parse_json(json_string):
    """
    Template filter to parse JSON string into Python object.
    Usage: {{ json_string|parse_json }}
    """
    if not json_string:
        return None
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None