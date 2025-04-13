from django import template
from django.utils.safestring import mark_safe
import jdatetime

register = template.Library()

@register.filter
def jformat(value, date_format="%Y/%m/%d"):
    """
    تبدیل یک تاریخ میلادی به تاریخ شمسی با فرمت دلخواه
    """
    if not value:
        return ""

    try:
        j_date = jdatetime.date.fromgregorian(date=value)
        return j_date.strftime(date_format)
    except Exception as e:
        return str(value)  # fallback در صورت بروز خطا
