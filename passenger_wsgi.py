import sys
import os

# مسیر پروژه Django رو اضافه کن
sys.path.insert(0, os.path.dirname(__file__))

# ست کردن تنظیمات Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'workshop.settings'

# اجرای WSGI اپلیکیشن
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
