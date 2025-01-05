# src/app/celery_app/db_engine_holder.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncEngine

engine: Optional[AsyncEngine] = None
