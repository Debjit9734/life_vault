import os
from celery import Celery
import redis  # Required for Redis operations

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'life_vault.settings')

app = Celery('life_vault')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')