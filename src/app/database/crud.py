from fastapi import HTTPException
from functools import wraps
import asyncio

from sqlalchemy import select, update, insert, delete, join, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, DBAPIError, NoResultFound

from .database import async_engine
from .models import *



def db_connection(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with AsyncSession(async_engine) as session:
            async with session.begin():
                try:
                    result = await func(session, *args, **kwargs)
                    return result
                except OSError:
                    raise HTTPException(
                        status_code=503,
                        detail="DB connection in the server does not work, maybe the container is not running or IP is wrong since you've restarted the node",
                    )
                except IntegrityError as e:
                    await session.rollback()
                    raise HTTPException(status_code=400, detail=str(e))
                # except DBAPIError as e:
                #     await session.rollback()
                #     raise HTTPException(status_code=400, detail="There is probably a wrong data type")
    return wrapper


@db_connection
async def select_used_ips(session: AsyncSession):
    """Select used proxies IPs"""
    result = await session.execute(
        select(
            case(
                (Account.proxy_ip.is_(None), None),
                else_=Account.proxy_ip
            ).label("ip"),
            func.count(Account.proxy_ip).label("used")
        ).group_by(Account.proxy_ip) 
    )

    used_ips = [{"ip": row.ip, "used": row.used} for row in result.fetchall()]
  
    return used_ips

   



async def main_testing():
    res = await select_used_ips()
    

if __name__ == "__main__":
    asyncio.run(main_testing())