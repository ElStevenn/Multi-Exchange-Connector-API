# src/app/celery/tasks.py

import logging
import asyncio
import sys

# We no longer need ThreadPoolExecutor because we're not spawning a separate thread
# from concurrent.futures import ThreadPoolExecutor

if len(sys.argv) > 1 and sys.argv[1] == "test":
    from src.app.celery_app.celery_config import celery_app
    from src.app.celery_app.async_tasks import _fetch_user_assets_task
else:
    from app.celery_app.celery_config import celery_app
    from app.celery_app.async_tasks import _fetch_user_assets_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(name='app.celery_app.tasks.fetch_user_assets_concurrently')
def fetch_user_assets_concurrently():
    """
    Celery task to fetch assets for all users concurrently in batches of 100.
    Handles async database calls and async HTTP requests.
    """
    logger.info("Starting fetch_user_assets_concurrently task...")

    # Directly run your async function in this synchronous Celery task
    # using asyncio.run(...) on the *same* event loop that Celery uses.
    asyncio.run(_fetch_user_assets_task())

    logger.info("Finished fetch_user_assets_concurrently task...")
