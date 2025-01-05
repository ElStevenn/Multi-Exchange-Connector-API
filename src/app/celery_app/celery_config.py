# src/app/celery_app/celery_config.py

import sys
import celery as celery_lib
from celery.schedules import crontab

if len(sys.argv) > 1 and sys.argv[1] == "test":
    from src.config import REDIS_URL
else:
    from config import REDIS_URL

celery_app = celery_lib.Celery(
    'tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.celery_app.tasks'] 
)

# General Configuration
celery_app.conf.update(
    timezone='UTC', 
    task_default_queue='celery',
    worker_max_tasks_per_child=100
)

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    'fetch-user-assets-every-5-minutes': {
        'task': 'app.celery_app.tasks.fetch_user_assets_concurrently',
        'schedule': crontab(minute='5-55/5'),  # Runs at 5,10,15,...55 minutes past the hour
        'options': {'queue': 'once_off_queue'},  # Ensure it uses the correct queue
    },
}
