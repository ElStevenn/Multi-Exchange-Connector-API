import asyncio, logging
from typing import Optional
from aiohttp import ClientSession, ClientError

from fastapi import HTTPException

from ..proxy import BrightProxy
from .bitget_layer import BitgetLayerConnection
from .binance_layer import BinanceLayerConnection

logger = logging.getLogger(__name__)

async def validate_account(exchange, proxy: BrightProxy, apikey: Optional[str] = None, secret_key: Optional[str] = None, passphrase: Optional[str] = None, proxy_ip: Optional[str] = None):
    """Validate account credentials"""
    if exchange == 'bitget':
        bitget_account = BitgetLayerConnection(
            api_key=apikey,
            api_secret_key=secret_key,
            passphrase=passphrase,
            proxy=proxy,
            ip=proxy_ip
        )        

        account_information = await bitget_account.get_account_information()

        # USER_ID, PERMISSIONS
        return account_information.get('userId', None), account_information.get('authorities', None)
    
    elif exchange == 'binance':
        binance_account = BinanceLayerConnection(
            api_key=apikey,
            secret_key=secret_key,
            proxy=proxy,
            ip=proxy_ip
        )

    elif exchange == 'okx':
        raise HTTPException(status_code=400, detail="Exchange not supported yet")

    elif exchange == 'kucoin':
        raise HTTPException(status_code=400, detail="Exchange not supported yet")

    # Return -> account_permisions, account_id | 401 error | 400 error

async def get_account_balance_(account_id, exchange, proxy: BrightProxy, apikey: Optional[str] = None, secret_key: Optional[str] = None, passphrase: Optional[str] = None, proxy_ip: Optional[str] = None):
    """
        return -> total, accounts[spot, futures, margin, [...]]

    
    """
    if exchange == 'bitget':
        bitget_account = BitgetLayerConnection(
            api_key=apikey,
            api_secret_key=secret_key,
            passphrase=passphrase,
            proxy=proxy,
            ip=proxy_ip
        )

        # Get Bitget account balance
        balance = await bitget_account.account_balance()

        return balance

    elif exchange == 'binance':
        pass

    elif exchange == 'okx':
        okx_account = None
        pass

    elif exchange == 'kucoin':
        kucoin_account = None
        pass


async def get_asset_price_in_usd(asset: str) -> float:
    """
    Fetch the current price of an asset in USD from CoinGecko asynchronously using aiohttp.
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": asset.lower(), "vs_currencies": "usd"}
    
    try:
        async with ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get(asset.lower(), {}).get("usd", 0.0)
                else:
                    print(f"Error: Received status code {response.status} for asset {asset}")
                    return 0.0
    except ClientError as e:
        print(f"Network error fetching price for {asset}: {e}")
        return 0.0
    except Exception as e:
        print(f"Unexpected error fetching price for {asset}: {e}")
        return 0.0
    

async def exchange_utils_testing():
    proxy = await BrightProxy().create()
   

    
if __name__ == "__main__":
    asyncio.run(exchange_utils_testing())