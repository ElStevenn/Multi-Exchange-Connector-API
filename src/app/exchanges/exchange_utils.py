import asyncio
from typing import Optional

from ..proxy import BrightProxy
from ..exchanges.bitget_layer import BitgetLayerConnection
from ..exchanges.binance_layer import BinanceLayerConnection

async def validate_account(exchange, proxy: BrightProxy, apikey: Optional[str] = None, secret_key: Optional[str] = None, passphrase: Optional[str] = None, proxy_ip: Optional[str] = None):
    if exchange == 'bitget':
        bitget_account = BitgetLayerConnection(
            api_key=apikey,
            api_secret_key=secret_key,
            passphrase=passphrase,
            proxy=proxy,
            ip=proxy_ip
        )        

        account_information = await bitget_account.get_account_information()

        print(account_information)

    elif exchange == 'binance':
        binance_account = BinanceLayerConnection(
            api_key=apikey,
            secret_key=secret_key,
            proxy=proxy,
            ip=proxy_ip
        )

    # Return -> account_permisions, account_id | 401 error | 400 error


async def exchange_utils_testing():
    proxy = await BrightProxy().create()
    res = await validate_account(
        exchange="bitget",
        proxy=proxy,
        apikey="bg_4f7b2d4d2d0e4b6b8f1b1b1b1b1b1b1b",
        secret_key="XXXXXXXXXXXXXXXXXXXX",
        passphrase="123456",
        proxy_ip="192.168.1.1"

    )

if __name__ == "__main__":
    asyncio.run(exchange_utils_testing())