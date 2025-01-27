# src/app/celery/async_tasks.py

import logging
import sys

if len(sys.argv) > 1 and sys.argv[1] == "test":
    from src.app.database.crud import (
        get_all_users,
        get_user_accounts,
        get_account_credentials,
        add_spot_historical_metadata,
        add_futures_historical_metadata,
        add_balance_historical_metadata,
        trim_balance_history_per_user
    )

    from src.app.exchanges.exchange_utils import get_account_balance_, get_asset_price_in_usd 
    from src.app.proxy import BrightProxy
else:
    from app.database.crud import (
        get_all_users,
        get_user_accounts,
        get_account_credentials,
        add_spot_historical_metadata,
        add_futures_historical_metadata,
        add_balance_historical_metadata,
        trim_balance_history_per_user
    )

    from app.exchanges.exchange_utils import get_account_balance_, get_asset_price_in_usd 
    from app.proxy import BrightProxy
    
import asyncio
import aiohttp
from asyncio import Semaphore

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Adjust as needed

# Configuration
MAX_ROWS_PER_USER = 13140
BATCH_SIZE = 100
MAX_CONCURRENT_API_CALLS = 50  # Adjust based on proxy and API limits
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 2  # seconds

# Initialize a semaphore for controlling concurrency
semaphore = Semaphore(MAX_CONCURRENT_API_CALLS)

async def _fetch_user_assets_task():
    """
    Fetch all necessary data before processing assets concurrently.
    """
    logger.info("Starting to fetch user assets...")
    try:
        users = await get_all_users()
        logger.info(f"Fetched {len(users)} users.")

        # Initialize the proxy once
        proxy = await BrightProxy().create()
        logger.info("Proxy initialized.")

        # Fetch asset price in USD once
        asset_price_usd = await get_asset_price_in_usd("usd")
        logger.info(f"Asset price fetched: USD {asset_price_usd}")

        # Gather all accounts across all users
        accounts = []
        for user in users:
            user_accounts = await get_user_accounts(user_id=user['id'])
            for account in user_accounts:
                accounts.append({
                    "user_id": user['id'],
                    **account
                })
        logger.info(f"Total accounts fetched: {len(accounts)}")

        # Prepare detailed account information with credentials
        detailed_accounts = []
        for account in accounts:
            credentials = await get_account_credentials(account_id=account['id'])
            if not credentials:
                logger.warning(f"No credentials found for account {account['id']}. Skipping.")
                continue  # Skip accounts without credentials
            detailed_accounts.append({
                "user_id": account['user_id'],
                "account_id": account['id'],
                "exchange": credentials.get('exchange'),
                "proxy": credentials.get('proxy'),
                "apikey": credentials.get('apikey'),
                "secret_key": credentials.get('secret_key'),
                "passphrase": credentials.get('passphrase'),
                "proxy_ip": account.get('proxy_ip')
            })
        logger.info(f"Detailed accounts prepared: {len(detailed_accounts)}")

        # Split into batches for processing
        batches = [detailed_accounts[i:i + BATCH_SIZE] for i in range(0, len(detailed_accounts), BATCH_SIZE)]
        logger.info(f"Total batches to process: {len(batches)}")

        for index, batch in enumerate(batches, start=1):
            logger.info(f"Processing batch {index}/{len(batches)} with {len(batch)} accounts.")
            tasks = [
                _fetch_assets_for_user(
                    user_id=account['user_id'],
                    account_id=account['account_id'],
                    exchange=account['exchange'], 
                    proxy=proxy,
                    apikey=account['apikey'],
                    secret_key=account['secret_key'],
                    passphrase=account['passphrase'],
                    proxy_ip=account['proxy_ip'],
                    asset_price_usd=asset_price_usd
                )
                for account in batch
            ]
            # Gather tasks with concurrency control
            await asyncio.gather(*tasks, return_exceptions=True)  # Handle exceptions within tasks

    except Exception as e:
        logger.error(f"Error in _fetch_user_assets_task: {e}", exc_info=True)

async def _fetch_assets_for_user(
    user_id: str,
    account_id: str,
    exchange: str,
    proxy: str,
    apikey: str = None,
    secret_key: str = None,
    passphrase: str = None,
    proxy_ip: str = None,
    asset_price_usd: float = None
):
    """
    Fetch assets for a single user account using the API.
    """
    async with semaphore:
        for attempt in range(1, API_RETRY_ATTEMPTS + 1):
            try:
                logger.debug(f"Attempt {attempt}: Fetching assets for account {account_id}.")

                # Fetch account balance
                assets = await get_account_balance_(
                    account_id=account_id,
                    exchange=exchange,
                    proxy=proxy,
                    apikey=apikey,
                    secret_key=secret_key,
                    passphrase=passphrase,
                    proxy_ip=proxy_ip
                )

                if not assets:
                    raise ValueError("Received empty assets data.")

                # Process assets
                spot_balance = float(assets['accounts'].get('spot', 0.0))
                spot_usd_value = spot_balance * asset_price_usd

                future_balance = float(assets['accounts'].get('futures', 0.0))
                future_usd_value = future_balance * asset_price_usd

                total_balance = float(assets.get('total', 0.0))
                total_usd_value = total_balance * asset_price_usd

                # Save assets to historical metadata
                await asyncio.gather(
                    add_spot_historical_metadata(account_id=account_id, asset="usd", balance=spot_balance, usd_value=spot_usd_value),
                    add_futures_historical_metadata(account_id=account_id, asset="usd", balance=future_balance, usd_value=future_usd_value),
                    add_balance_historical_metadata(account_id=account_id, asset="usd", balance=total_balance, usd_value=total_usd_value)
                )

                # Trim balance history to maintain record limits per user
                await trim_balance_history_per_user(user_id=user_id, max_records=MAX_ROWS_PER_USER)

                logger.info(f"Successfully processed account {account_id} for user {user_id}.")
                break  # Exit the retry loop upon success

            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for account {account_id}: {e}")
                if attempt < API_RETRY_ATTEMPTS:
                    await asyncio.sleep(API_RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for account {account_id}: {e}", exc_info=True)


# Entry point for testing
async def database_crud_testing():
    user_id = "2141ec7d-8156-4462-9a8e-0cf37b11997d"
    account_id = "1530240371"

    result = await get_user_accounts("94615a24-5243-41a3-8f27-5dae288d2c7e")
    print(result)

if __name__ == "__main__":
    asyncio.run(database_crud_testing())
