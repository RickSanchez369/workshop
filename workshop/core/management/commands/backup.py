# core/management/commands/backup.py
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings
import os
import datetime
import subprocess

class Command(BaseCommand):
    help = 'بکاپ‌گیری از دیتابیس و ارسال به ایمیل'

    def handle(self, *args, **kwargs):
        today = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = f'backup_{today}.sql'
        path = os.path.join('backups', filename)
        os.makedirs('backups', exist_ok=True)

        # گرفتن بکاپ از PostgreSQL
        result = subprocess.run([
            'pg_dump',
            '-U', 'postgres',              # 👈 نام یوزر دیتابیس
            '-d', 'miladworkshop',         # 👈 نام دیتابیس
            '-f', path,
        ], env={'PGPASSWORD': 'your_db_password'})  # 👈 رمز دیتابیس

        if result.returncode != 0:
            self.stdout.write(self.style.ERROR('❌ خطا در گرفتن بکاپ!'))
            return

        # ارسال فایل بکاپ به ایمیل
        email = EmailMessage(
            subject='📦 بکاپ دیتابیس',
            body='فایل بکاپ دیتابیس به پیوست ارسال شد.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['youradmin@example.com'],
        )
        email.attach_file(path)
        email.send()
        self.stdout.write(self.style.SUCCESS('✅ بکاپ گرفته شد و ایمیل شد!'))
