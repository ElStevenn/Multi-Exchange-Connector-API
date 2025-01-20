import asyncio, logging
from typing import Optional
from aiohttp import ClientSession, ClientError

from fastapi import HTTPException

from ..proxy import BrightProxy
from .bitget_layer import BitgetLayerConnection
from .binance_layer import BinanceLayerConnection
from .kucoin_layer import KucoinLayerConnection
from ..database.crud import get_balance_history
from ..utils import generate_id

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
        kucoin_account = KucoinLayerConnection(
            api_key=apikey,
            api_secret_key=secret_key,
            proxy=proxy,
            passphrase=passphrase,
            ip=proxy_ip
        )
       
        account_information = await kucoin_account.get_account_information()

        permisions = str(['GeneralFutures', 'TradingSpot', 'TradingKuCoin', 'EarnAllow', 'FlexTransfersMargin', 'Trading'])
        user_id = generate_id(apikey)


        return user_id, permisions

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

        # Get current account balance
        current_balance_data = await bitget_account.account_balance()
        current_balance = current_balance_data['total']

        # Attempt to get the 24h balance, fall back if not available
        offset_hours = 24
        previous_balance = None

        while offset_hours > 0:
            balance_24h_data = await get_balance_history(account_id=account_id, limit=1, offset=offset_hours)
            
            if balance_24h_data.size > 0 and balance_24h_data[0][1] is not None:
                previous_balance = balance_24h_data[0][1]
                break
            
            offset_hours -= 1 

        if previous_balance is None:
            raise ValueError("Could not retrieve balance history data even after reducing the offset.")

        if previous_balance == 0:
            raise ValueError("Previous balance is zero, cannot calculate percentage change.")

        balance_24h_percentage_change = ((current_balance - previous_balance) / previous_balance) * 100
        balance_24h_absolute_change = current_balance - previous_balance

        current_balance_data['24h_change_percentage'] = balance_24h_percentage_change
        current_balance_data['24h_change'] = balance_24h_absolute_change

        return current_balance_data
    
    
    elif exchange == 'binance':
        pass

    elif exchange == 'okx':
        okx_account = None
        pass

    elif exchange == 'kucoin':
        kucoin_account = KucoinLayerConnection(
            api_key=apikey,
            api_secret_key=secret_key,
            proxy=proxy,
            passphrase=passphrase,
            ip=proxy_ip
        )

        current_balance_data = await kucoin_account.account_balance()

        return current_balance_data

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
    

async def get_account_assets_(exchange, proxy: BrightProxy, apikey: Optional[str] = None, secret_key: Optional[str] = None, passphrase: Optional[str] = None, proxy_ip: Optional[str] = None):
    """Get account assets"""
    
    if exchange == 'bitget':
        pass

    elif exchange == 'binance':
        pass
        
    elif exchange == 'okx':
        pass

    elif exchange == 'kucoin':
       pass

async def exchange_utils_testing():
    proxy = await BrightProxy().create()
    
    await get_account_balance_(exchange='', proxy=proxy, apikey='apikey', secret_key='secret_key', passphrase='passphrase', proxy_ip='proxy_ip')
    
if __name__ == "__main__":
    asyncio.run(exchange_utils_testing())