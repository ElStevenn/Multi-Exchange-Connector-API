# src/app/celery/tasks.py

import logging
from src.app.celery.celery_config import celery_app
from src.app.celery.async_tasks import _fetch_user_assets_task
import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_async(coroutine):
    """
    Runs an asynchronous coroutine in a separate thread with its own event loop.
    """
    def run(loop, coro):
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
        loop.close()
    
    loop = asyncio.new_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(run, loop, coroutine)
    try:
        return future.result()
    except Exception as e:
        logger.error(f"Error running async task in thread: {e}", exc_info=True)

@celery_app.task
def fetch_user_assets_concurrently():
    """
    Celery task to fetch assets for all users concurrently in batches of 100.
    Handles async database calls and async HTTP requests.
    """
    logger.info("Starting fetch_user_assets_concurrently task...")
    run_async(_fetch_user_assets_task())
    logger.info("Finished fetch_user_assets_concurrently task...")
