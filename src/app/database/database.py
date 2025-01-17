from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import inspect
import asyncio, sys, os

if len(sys.argv) > 1 and sys.argv[1] == "test":
    from src.config import DB_HOST, DB_NAME, DB_PASS, DB_USER, BASE_DIR
    # from .models import Base
else:
    from config import DB_HOST, DB_NAME, DB_PASS, DB_USER, BASE_DIR

# Database engine 
if BASE_DIR.startswith('/home/mrpau'):
    async_engine = create_async_engine(f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}')
else:
    async_engine = create_async_engine(
        f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}',
        echo=False,
        future=True,
        pool_size=10,        
        max_overflow=20,
        pool_timeout=30
        )


async def get_all_tables():
    async with async_engine.begin() as conn:
        def sync_get_table_names(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()
        
        table_names = await conn.run_sync(sync_get_table_names)
        print("table names -> ",table_names)
    return table_names



if __name__ == "__main__":
    asyncio.run(get_all_tables())
