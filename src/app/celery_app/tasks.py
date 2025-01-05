# src/app/celery_app/tasks.py

import logging
import sys
import asyncio
import threading

from celery.signals import worker_init, worker_shutdown
from sqlalchemy.ext.asyncio import create_async_engine

from .db_engine_holder import engine as global_engine

if len(sys.argv) > 1 and sys.argv[1] == "test":
    from src.app.celery_app.celery_config import celery_app
    from src.app.celery_app.async_tasks import _fetch_user_assets_task
else:
    from app.celery_app.celery_config import celery_app
    from app.celery_app.async_tasks import _fetch_user_assets_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

persistent_loop = None

@worker_init.connect
def init_persistent_loop(**kwargs):
    """
    Runs once when the Celery worker process boots up.
    We create a single event loop and the DB engine here,
    both living as long as the worker.
    """
    global persistent_loop, global_engine

    logger.info("Initializing persistent loop + DB engine in worker_init...")

    # Create the persistent loop
    persistent_loop = asyncio.new_event_loop()
    logger.info("Persistent event loop created.")

    # Start that loop in a background thread
    def loop_runner(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    t = threading.Thread(target=loop_runner, args=(persistent_loop,), daemon=True)
    t.start()
    logger.info("Persistent loop thread started.")

    # Create the async engine on the new loop
    def create_engine_sync():
        # e.g. read DB credentials from config
        from config import DB_HOST, DB_NAME, DB_PASS, DB_USER

        db_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"
        logger.info("Creating async engine on persistent loop.")
        new_engine = create_async_engine(
            db_url,
            echo=False,
            future=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30
        )
        return new_engine

    async def async_wrapper():
        return create_engine_sync()

    future = asyncio.run_coroutine_threadsafe(async_wrapper(), persistent_loop)
    new_engine = future.result()  # block until engine is created

    global_engine = new_engine
    logger.info("Async engine created and stored globally.")

@worker_shutdown.connect
def shutdown_persistent_loop(**kwargs):
    """
    Optionally close the loop & engine when the worker shuts down.
    """
    global persistent_loop, global_engine

    if persistent_loop is not None:
        logger.info("Shutting down persistent loop.")
        persistent_loop.call_soon_threadsafe(persistent_loop.stop)
        persistent_loop = None

    if global_engine is not None:
        logger.info("Nulling out the global engine reference.")
        global_engine = None

@celery_app.task(name='app.celery_app.tasks.fetch_user_assets_concurrently')
def fetch_user_assets_concurrently():
    """
    Celery task that schedules the real async work on the persistent loop
    (and uses the engine from global_engine).
    """
    logger.info("Starting fetch_user_assets_concurrently task...")

    global persistent_loop
    if not persistent_loop:
        logger.error("No persistent event loop is running!")
        return

    future = asyncio.run_coroutine_threadsafe(_fetch_user_assets_task(), persistent_loop)

    result = None
    try:
        result = future.result()
    except Exception as e:
        logger.error(f"Error while running _fetch_user_assets_task: {e}", exc_info=True)

    logger.info("Finished fetch_user_assets_concurrently task...")
    return result
