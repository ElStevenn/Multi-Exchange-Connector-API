from sqlalchemy.ext.asyncio import create_async_engine

from src.config import DB_HOST, DB_NAME, DB_PASS, DB_USER
from .models import Base


# Database engine 
async_engine = create_async_engine(f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}')