# src/app/celery/tasks.py

import logging
import sys
import asyncio
import threading
from celery.signals import worker_init, worker_shutdown

if len(sys.argv) > 1 and sys.argv[1] == "test":
    from src.app.celery_app.celery_config import celery_app
    from src.app.celery_app.async_tasks import _fetch_user_assets_task
else:
    from app.celery_app.celery_config import celery_app
    from app.celery_app.async_tasks import _fetch_user_assets_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# We'll store a global reference to the event loop
persistent_loop = None

@worker_init.connect
def init_persistent_loop(**kwargs):
    """
    This signal runs once when the Celery worker process boots up.
    We create a single event loop here and start it in a dedicated thread.
    """
    global persistent_loop

    # Create the loop
    persistent_loop = asyncio.new_event_loop()
    logger.info("Persistent event loop created.")

    # Start the loop in a background thread
    def loop_runner(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    t = threading.Thread(target=loop_runner, args=(persistent_loop,), daemon=True)
    t.start()
    logger.info("Persistent loop thread started.")

@worker_shutdown.connect
def shutdown_persistent_loop(**kwargs):
    """
    Optionally close the loop when the worker shuts down.
    """
    global persistent_loop
    if persistent_loop is not None:
        logger.info("Shutting down persistent loop.")
        persistent_loop.call_soon_threadsafe(persistent_loop.stop)
        persistent_loop = None

@celery_app.task(name='app.celery_app.tasks.fetch_user_assets_concurrently')
def fetch_user_assets_concurrently():
    """
    Celery task that schedules the real async work on the persistent loop
    instead of calling `asyncio.run()`.
    """
    logger.info("Starting fetch_user_assets_concurrently task...")

    global persistent_loop
    if not persistent_loop:
        # If for some reason the loop isn't set up, fallback or raise
        logger.error("No persistent event loop is running!")
        return

    # Schedule the coroutine on the persistent loop
    future = asyncio.run_coroutine_threadsafe(_fetch_user_assets_task(), persistent_loop)

    # This blocks the Celery worker until the async task finishes
    # which is typically desired (Celery won't see the task as "done" otherwise).
    result = None
    try:
        result = future.result()  # gather any return from `_fetch_user_assets_task`
    except Exception as e:
        logger.error(f"Error while running _fetch_user_assets_task: {e}", exc_info=True)

    logger.info("Finished fetch_user_assets_concurrently task...")
    return result
