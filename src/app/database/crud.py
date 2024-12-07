from fastapi import HTTPException
from typing import Optional
from functools import wraps
from uuid import UUID
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


# - - - PROXY - - - 
@db_connection
async def get_used_ips(session: AsyncSession):
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

# - - - ACCOUNTS - - - 
@db_connection
async def register_new_account(session: AsyncSession, user_id: str, account_id: str, email: str, account_name: str, account_type: str = None, proxy_ip: str = None) -> str:
    """Register a new trading account."""
    
    # Check if the account already exists
    result = await session.execute(
        select(Account).where(Account.account_id == account_id)
    )
    check_acc = result.scalar_one_or_none()
    if check_acc:
        raise HTTPException(
            status_code=400, 
            detail=f"Account with email {email} already exists. If you want to update the credentials, try updating."
        )

    # Set primary trading account type if none is provided
    if not account_type:
        result = await session.execute(
            select(Account).where(
                and_(Account.user_id == user_id, Account.type == 'trading')
            )
        )
        if result.scalar_one_or_none() is None:
            account_type = 'trading'
        else:
            account_type = 'sub-account'

    # Create the account
    account = Account(
        account_id=account_id,
        user_id=UUID(user_id),
        account_name=account_name,
        type=account_type,
        email=email,
        proxy_ip=proxy_ip
    )

    session.add(account)
    await session.flush()
    await session.refresh(account)  
    return account.account_id

@db_connection
async def get_main_account(session: AsyncSession, user_id: str) -> str:
    """Get main trading account"""
    result = await session.execute(
        select(Account)
        .where(
            and_(
                Account.user_id == user_id,
                Account.type == 'main-account'
            )
        )
    )

    main_account = result.scalar_one_or_none()

    if not main_account:
        return None
    
    return main_account.account_id, main_account.proxy_ip

# - - - USER - - -
@db_connection
async def get_user_data(session: AsyncSession, user_id: str):
    """Get user information (User table)"""
    result = await session.execute(
        select(Users)
        .where(Users.id == user_id)
    )

    user = result.scalar_one_or_none()

    if not user:
        return None
    
    return {"username": user.username, "name": user.name, "surname": user.surname, "email": user.email, "role": user.role}


# - - - CREDENTIALS - - - 
@db_connection
async def add_user_credentials(session: AsyncSession, account_id: str, exchange: str, encrypted_apikey: str = None, encrypted_secretkey = None, encrypted_passphrase = None, encrypted_oauth2_token = None):
    """Add user credentials associated with a user account."""
    credentials = UserCredentials(
        account_id=account_id,
        exchange_name=exchange
    )

    if encrypted_apikey:
        credentials.set_encrypted_apikey(encrypted_apikey)
    if encrypted_secretkey:
        credentials.set_encrypted_secret_key(encrypted_secretkey)
    if encrypted_passphrase:
        credentials.set_encrypted_passphrase(encrypted_passphrase)
    credentials.set_encrypted_passphrase(encrypted_passphrase)
    if encrypted_oauth2_token:
        credentials.set_encrypted_oauth2_token(encrypted_oauth2_token)
    
    session.add(credentials)
    await session.flush()
    await session.refresh(credentials)
    return credentials.id

@db_connection
async def get_account_credentials(session: AsyncSession, account_id: str):
    """Get exchange credentials """
    result = await session.execute(
        select(UserCredentials)
        .where(UserCredentials.account_id == account_id)
    )

    credentials: UserCredentials = result.scalar_one_or_none()

    if not credentials:
        raise HTTPException(status_code=404, detail="Credentials not found")

    return {
        "apikey": credentials.get_apikey(),
        "secret_key": credentials.get_secret_key(),
        "passphrase": credentials.get_passphrase(),
    }


async def database_crud_testing():
    user_id = "49898f05-bc00-4d4b-87fd-212885b8cf28"
    account_id = "1530240371"

    result = await get_main_account(user_id=user_id)
    print(result)

if __name__ == "__main__":
    asyncio.run(database_crud_testing())