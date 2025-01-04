# src/app/celery/celery_config.py
import sys
from celery import Celery
from celery.schedules import crontab

if len(sys.argv) > 1 and sys.argv[1] == "test":
    from src.config import REDIS_URL
else:
    from config import REDIS_URL

celery_app = Celery(
    'tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['src.app.celery.tasks'] 
)

# General Configuration
celery_app.conf.update(
    timezone='UTC', 
    task_default_queue='celery',
    worker_max_tasks_per_child=100
)

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    'fetch-user-assets-every-hour-on-the-hour': {
        'task': 'src.app.celery.tasks.fetch_user_assets_concurrently',
        'schedule': crontab(minute=0, hour='*'),  # Every hour, at minute 0 (e.g., 5:00, 6:00, etc.)
    },
}
