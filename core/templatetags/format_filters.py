# core/templatetags/format_filters.py

from django import template

register = template.Library()

@register.filter
def smart_round(value):
    try:
        value = float(value)
        if value == int(value):
            return int(value)
        else:
            return round(value, 1)
    except:
        return value
