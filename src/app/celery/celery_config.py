# src/app/celery/celery_config.py

from celery import Celery
from celery.schedules import crontab
from src.config import REDIS_URL

celery_app = Celery(
    'tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['src.app.celery.tasks']  # Include the tasks module
)

# General Configuration
celery_app.conf.update(
    timezone='UTC',  # Adjust to your preferred timezone
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
