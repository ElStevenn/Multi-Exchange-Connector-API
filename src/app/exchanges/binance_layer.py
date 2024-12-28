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

    async def get_account_information(self):
        request = "/api/v3/account"
        url = f"{self.base_url}{request}"
        headers = {
            "Content-Type": "application/json",
            "X-MBX-APIKEY": self.api_key
        }
        account_information = await self.proxy.curl_api(
            url=url,
            body={}, 
            method="GET",
            headers=headers,
            ip=self.ip
        )
        return account_information
    
    async def get_account_balance(self):
        request = "/api/v3/account"
        url = f"{self.base_url}{request}"
        headers = {
            "Content-Type": "application/json",
            "X-MBX-APIKEY": self.api_key
        }
        account_balance = await self.proxy.curl_api(
            url=url,
            body={},
            method="GET",
            headers=headers,
            ip=self.ip
        )
        return account_balance
    


    

async def main_test_binance():
    proxy = await BrightProxy.create()
    ip = "185.246.219.114"

    bitget_connection = BinanceLayerConnection()

    

if __name__ == "__main__":
    asyncio.run(main_test_binance())