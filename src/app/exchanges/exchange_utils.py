import asyncio
from typing import Optional

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

        account_info = await bitget_account.account_list_info()
        return {
            "available": account_info.get('available', None),
            "unrealizedPL": account_info.get('unrealizedPL', None),
            "assetList": account_info.get('assetList', None)
        }

    elif exchange == 'binance':
        pass

    elif exchange == 'okx':
        pass

    elif exchange == 'kucoin':
        pass


async def exchange_utils_testing():
    proxy = await BrightProxy().create()
    res = await validate_account(

    )
    print(res)

if __name__ == "__main__":
    asyncio.run(exchange_utils_testing())