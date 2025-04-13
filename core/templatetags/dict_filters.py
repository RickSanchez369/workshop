# core/templatetags/dict_filters.py
from django import template
register = template.Library()

@register.filter
def dict_get(d, key):
    return d.get(key)


@register.filter
def comma(value):
    try:
        value = int(str(value).replace(',', ''))
        return "{:,}".format(value)
    except:
        return value
