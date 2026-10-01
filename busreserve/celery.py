import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'busreserve.settings')

app = Celery('busreserve')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()