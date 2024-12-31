from celery import Celery

from src.config import REDIS_URL


"""
docs ->
 container: https://hub.docker.com/_/celery
 how it works: https://derlin.github.io/introduction-to-fastapi-and-celery/
 
"""


celery_app = Celery(
    'tasks',
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    timezone='UTC',
    beat_schedule={
     'fetch-user-assets-every-x-hours': {
            'task': 'tasks.fetch_user_assets',
            'schedule': 60 * 60 * 1,  
        },
    }
)