import asyncio
from fastapi import FastAPI

from src.app.proxy import BrightProxy



class BinanceLayerConnection():
    """
    Layer that connects Binance API with this API
    """
    def __init__(self, api_key, secret_key: str, proxy: BrightProxy, ip: str) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.proxy = proxy
        self.ip = ip
        self.base_url = "https://api.binance.com"

    

async def main_test_binance():
    pass

if __name__ == "__main__":
    asyncio.run(main_test_binance())