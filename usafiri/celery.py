import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'usafiri.settings')
app = Celery('usafiri')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
