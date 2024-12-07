import asyncio
import base64
import hmac
import time
import json
import httpx
from fastapi import HTTPException

from src.app.proxy import BrightProxy


class BitgetLayerConnection():
    def __init__(self, api_key, api_secret_key, passphrase, proxy: BrightProxy, ip: str) -> None:
        self.api_key = api_key
        self.api_secret_key = api_secret_key 
        self.passphrase = passphrase
        self.proxy = proxy
        self.ip = ip
        self.api_url = "https://api.bitget.com"

    def generate_signature(self, prehash_string: str) -> str:
        mac = hmac.new(
            bytes(self.api_secret_key, encoding='utf8'),
            bytes(prehash_string, encoding='utf-8'),
            digestmod='sha256'
        )
        return base64.b64encode(mac.digest()).decode()

    def get_headers(self, method: str, request_path: str, query_params: dict, body_params: dict) -> dict:
        timestamp = str(int(time.time() * 1000))
        method = method.upper()  
        prehash_string = f"{timestamp}{method}{request_path}"

        # Sort and construct query string
        if query_params:
            sorted_params = sorted(query_params.items(), key=lambda x: x[0])
            query_string = '&'.join(f"{key}={value}" for key, value in sorted_params)
            prehash_string += f"?{query_string}"
            request_path += f"?{query_string}"
        else:
            query_string = ''

        # Serialize body if it's a dictionary
        if body_params:
            body = json.dumps(body_params)
        else:
            body = ''
        prehash_string += body

        sign = self.generate_signature(prehash_string)
        return {
            "Content-Type": "application/json",
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": sign,
            "ACCESS-PASSPHRASE": self.passphrase,
            "ACCESS-TIMESTAMP": timestamp,
            "locale": "en-US"
        }

    async def get_account_information(self) -> dict:
        """Get account information(SPOT read or SPOT read/write permission needed)"""
        request = "/api/v2/spot/account/info"
        url = f"{self.api_url}/api/v2/spot/account/info"
        headers = self.get_headers("GET", request, {}, {})
        account_information = await self.proxy.curl_api(
            url=url,
            body={}, 
            method="GET",
            headers=headers,
            ip=self.ip
        )
        if account_information.get('msg') == 'success':
            return account_information.get('data', None)
        else:
            raise HTTPException(status_code=400, detail=f"An error ocurred: {account_information}")

    async def account_assets(self):
        """Get account assets(SPOT read or SPOT read/write permission needed)."""
        request = "/api/v2/spot/account/assets"
        url = f"{self.api_url}{request}"
        parameters = {
            "coin": "USDT"  
        }
        headers = self.get_headers("GET", request, parameters, {})  
        account_assets = await self.proxy.curl_api(
            url=f"{url}?coin={parameters['coin']}",  
            body={}, 
            method="GET",
            headers=headers,
            ip=self.ip
        )
        
        return account_assets.get('data', None)


async def main_test_bitget():
    proxy = await BrightProxy.create()
    ip = "185.246.219.114"

    # Account Information
    bitget_connection = BitgetLayerConnection(
        api_key="bg_1cf35b8ca56123b1fc4fb00909cffa45",
        api_secret_key="26df4b9bb4e719028c3f4e02d19330121e10d3cb611a66300160be962b8120d0",
        passphrase="Skyfall97Zoom42",
        proxy=proxy,
        ip=ip
    )
    
    # Account Information
    acc_info = await bitget_connection.get_account_information()
    print("Account ID: ", acc_info.get('userId'))

    # Account assets
    # acc_assets = await bitget_connection.account_assets()
    # print(f"Account assets: {acc_assets}")


if __name__ == "__main__":
    asyncio.run(main_test_bitget())