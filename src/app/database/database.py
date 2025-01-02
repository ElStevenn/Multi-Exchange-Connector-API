from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import inspect
import asyncio

from src.config import DB_HOST, DB_NAME, DB_PASS, DB_USER, BASE_DIR
from .models import Base

# Database engine 
if BASE_DIR.startswith('/home/mrpau'):
    async_engine = create_async_engine(f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}')
else:
    async_engine = create_async_engine(f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}')


async def get_all_tables():
    async with async_engine.begin() as conn:
        def sync_get_table_names(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()
        
        table_names = await conn.run_sync(sync_get_table_names)
        print(table_names)
    return table_names



if __name__ == "__main__":
    asyncio.run(get_all_tables())
