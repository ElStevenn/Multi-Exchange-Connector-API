from .celery_config import celery_app
from src.app.database.crud import get_all_users, get_user_accounts, get_account_credentials, add_spot_historical_metadata, add_futures_historical_metadata, add_balance_historical_metadata
from src.app.exchanges.exchange_utils import get_account_assets_, get_asset_price_in_usd
import asyncio


@celery_app.task
def fetch_user_assets_concurrently():
    """
    Celery task to fetch assets for all users concurrently in batches of 100.
    Handles async database calls and async HTTP requests.
    """
    asyncio.run(_fetch_user_assets_task())


async def _fetch_user_assets_task():
    """
    Fetch all necessary data before processing assets concurrently.
    """
    users = await get_all_users()
    asset_price_usd = await get_asset_price_in_usd("usd")

    accounts = []
    for user in users:
        user_accounts = await get_user_accounts(user_id=user['id'])
        for account in user_accounts:
            accounts.append({"user_id": user['id'], **account})
    
    detailed_accounts = []
    for account in accounts:
        credentials = await get_account_credentials(account_id=account['id'])
        detailed_accounts.append({
            "user_id": account['user_id'],
            "account_id": account['id'],
            "exchange": account.get('exchange'),
            "proxy": credentials.get('proxy'),
            "apikey": credentials.get('apikey'),
            "secret_key": credentials.get('secret_key'),
            "passphrase": credentials.get('passphrase'),
            "proxy_ip": credentials.get('proxy_ip')
        })
    
    batches = [detailed_accounts[i:i + 100] for i in range(0, len(detailed_accounts), 100)]
    
    for batch in batches:
        tasks = [
            _fetch_assets_for_user(
                account['account_id'],
                account['exchange'],
                account['proxy'],
                account['apikey'],
                account['secret_key'],
                account['passphrase'],
                account['proxy_ip'],
                asset_price_usd=asset_price_usd
            )
            for account in batch
        ]
        await asyncio.gather(*tasks)


async def _fetch_assets_for_user(account_id, exchange, proxy, apikey=None, secret_key=None, passphrase=None, proxy_ip=None, asset_price_usd=None):
    """
    Fetch assets for a single user account using the API.
    """
    try:
        # Get user assets
        assets = await get_account_assets_(
            account_id=account_id,
            exchange=exchange,
            proxy=proxy,
            apikey=apikey,
            secret_key=secret_key,
            passphrase=passphrase,
            proxy_ip=proxy_ip
        )
        
        spot_balance = float(assets['spot_account'].get('available', 0.0))
        spot_usd_value = spot_balance * asset_price_usd

        future_balance = float(assets['future_account'].get('available', 0.0))
        future_usd_value = future_balance * asset_price_usd

        total_balance = spot_balance + future_balance
        total_usd_value = total_balance * asset_price_usd

        # Save assets to database
        await add_spot_historical_metadata(account_id=account_id, asset="usd", balance=spot_balance, usd_value=spot_usd_value)

        await add_futures_historical_metadata(account_id=account_id, asset="usd", balance=future_balance, usd_value=future_usd_value)

        await add_balance_historical_metadata(account_id=account_id, asset="usd", balance=total_balance, usd_value=total_usd_value)

    except Exception as e:
        print(f"Failed to fetch assets for account {account_id}: {e}")