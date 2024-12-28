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
        
        # Build the pre-hash string: timestamp + method + requestPath (+ possible query) + body
        prehash_string = f"{timestamp}{method}{request_path}"

        if query_params:
            sorted_params = sorted(query_params.items(), key=lambda x: x[0])
            query_string = '&'.join(f"{k}={v}" for k, v in sorted_params)
            prehash_string += f"?{query_string}"
            request_path += f"?{query_string}"
        else:
            query_string = ''

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
        """Works because the endpoint is correct."""
        request = "/api/v2/spot/account/info"
        url = f"{self.api_url}{request}"
        headers = self.get_headers("GET", request, {}, {})
        response_data = await self.proxy.curl_api(
            url=url,
            body={}, 
            method="GET",
            headers=headers,
            ip=self.ip
        )
        
        if response_data.get('msg') == 'success':
            return response_data.get('data', None)
        else:
            print(response_data)
            await self.proxy.remove_ip_blacklist(ip=self.ip)
            raise HTTPException(status_code=400, detail="An error ocurred, please try again later")

    async def account_list_info(self):
        """Query all account information under a certain product type"""
        request = "/api/v2/mix/account/accounts"
        url = f"{self.api_url}{request}"
        params = {"productType": "USDT-FUTURES"}
        headers = self.get_headers("GET", request, params, {})
        response_data = await self.proxy.curl_api(
            url=url,
            body=params,
            method="GET",
            headers=headers,
            ip=self.ip
        )
        
        if response_data.get('msg') == 'success':
            account_list = response_data.get('data', None)[0]

            return account_list

        else:
            print(response_data)
            # Remove machine IP from blacklist, because this was an error it had in the past
            avariable_ip = await self.proxy.get_machine_ip()
            await self.proxy.remove_ip_blacklist(ip=avariable_ip)
            # raise HTTPException(status_code=400, detail="An error ocurred, please try again later")
    
async def main_test_bitget():
    proxy = await BrightProxy.create()
    ip = "58.97.135.175"


    
    # acc_info = await bitget_connection.get_account_information()
    # print(acc_info)

    # # Test the "assets" endpoint
    # acc_assets = await bitget_connection.account_list_info()
    # print("Account assets:", acc_assets)

if __name__ == "__main__":
    asyncio.run(main_test_bitget())
