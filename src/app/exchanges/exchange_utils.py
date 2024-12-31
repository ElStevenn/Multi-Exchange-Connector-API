import asyncio
from typing import Optional
from aiohttp import ClientSession, ClientError

from fastapi import HTTPException

from ..proxy import BrightProxy
from .bitget_layer import BitgetLayerConnection
from .binance_layer import BinanceLayerConnection

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

async def get_account_assets_(account_id, exchange, proxy: BrightProxy, apikey: Optional[str] = None, secret_key: Optional[str] = None, passphrase: Optional[str] = None, proxy_ip: Optional[str] = None):
    """
        return -> avariable_accounts, unrealizedPL, asset_list
    
    """
    if exchange == 'bitget':
            bitget_account = BitgetLayerConnection(
                api_key=apikey,
                api_secret_key=secret_key,
                passphrase=passphrase,
                proxy=proxy,
                ip=proxy_ip
            )

            # Run all asset fetch calls concurrently
            future_assets_task = bitget_account.furues_assets()
            spot_assets_task = bitget_account.spot_assets()
            margin_account_task = bitget_account.margin_assets_summary()
            
            future_assets, spot_assets, margin_account = await asyncio.gather(
                future_assets_task,
                spot_assets_task,
                margin_account_task
            )

            # Process Futures Account
            future_account = {
                "available": float(future_assets.get('available', 0.0)),
                "unrealizedPL": float(future_assets.get('unrealizedPL', 0.0)),
                "assetList": future_assets.get('assetList', [])
            }

            # Process Spot Account
            spot_account = {
                "available": float(spot_assets.get('available', 0.0)),
                "limitAvailable": float(spot_assets.get('limitAvailable', 0.0)),
                "frozen": float(spot_assets.get('frozen', 0.0)),
                "locked": float(spot_assets.get('locked', 0.0)),
            }

            # Final Response
            final_return = {
                "exchange": "bitget",
                "account_id": account_id,
                "total_balance": (
                    future_account["available"] +
                    spot_account["available"] +
                    margin_account["total"]["totalAmount"]
                ),
                "future_account": future_account,
                "spot_account": spot_account,
                "margin_account": margin_account
            }

            return final_return

    elif exchange == 'binance':
        pass

    elif exchange == 'okx':
        pass

    elif exchange == 'kucoin':
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
   
    res = await get_asset_price_in_usd("usd")
    print(res)
    
if __name__ == "__main__":
    asyncio.run(exchange_utils_testing())