import asyncio
import base64
import hmac
import time
import json
import httpx
import sys
from typing import Dict


from fastapi import HTTPException

if len(sys.argv) > 1 and sys.argv[1] == "test":
    from src.app.proxy import BrightProxy
else:
    from app.proxy import BrightProxy

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

    async def future_assets(self) -> dict:
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
            account_list = []
            for asset in response_data.get('data', None):
                account_list.append({
                    "coin": asset.get("marginCoin"),
                    "available": asset.get("available"),
                    "frozen": asset.get("locked"),
                    "locked": asset.get("locked")
                })


            return account_list
        else:
        
            # Remove machine IP from blacklist, because this was an error it had in the past
            avariable_ip = await self.proxy.get_machine_ip()
            await self.proxy.remove_ip_blacklist(ip=avariable_ip)
            raise HTTPException(status_code=400, detail="An error ocurred, please try again later")
    


    async def spot_assets(self) -> dict:
        """Get account assets and whether are frozen or locked"""
        request = "/api/v2/spot/account/assets"
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
            asset_list = response_data.get('data', None)

            assets = [{"symbol": asset['coin'], 'available': asset['available'], 'limitAvailable': asset['limitAvailable'], 'frozen': asset['frozen'], 'locked': asset['locked']} for asset in asset_list]
            return assets

        else:
            # Remove machine IP from blacklist, because this was an error it had in the past
            avariable_ip = await self.proxy.get_machine_ip()
            await self.proxy.remove_ip_blacklist(ip=avariable_ip)
            raise HTTPException(status_code=400, detail="An error ocurred, please try again later")

    async def margin_assets_summary(self) -> Dict:
        """Get margin assets, both crossed and isolated, summary"""
        # Crossed Margin Request
        crossed_request = "/api/v2/margin/crossed/account/assets"
        crossed_url = f"{self.api_url}{crossed_request}"
        crossed_params = {"coin": "USDT"}
        crossed_headers = self.get_headers("GET", crossed_request, crossed_params, {})
        response_data1 = await self.proxy.curl_api(
            url=crossed_url,
            body=crossed_params,
            method="GET",
            headers=crossed_headers,
            ip=self.ip
        )
        
        # Isolated Margin Request
        isolated_request = "/api/v2/margin/isolated/account/assets"
        isolated_url = f"{self.api_url}{isolated_request}"
        isolated_params = {"coin": "BTCUSDT"}
        isolated_headers = self.get_headers("GET", isolated_request, isolated_params, {})
        response_data2 = await self.proxy.curl_api(
            url=isolated_url,
            body=isolated_params,
            method="GET",
            headers=isolated_headers,
            ip=self.ip
        )
        
        crossed = {}
        isolated = {}
        total = {
            "totalAmount": 0.0,
            "available": 0.0,
            "frozen": 0.0,
            "borrow": 0.0,
            "interest": 0.0,
            "net": 0.0
        }
        
        if response_data1.get('msg') == 'success' and response_data2.get('msg') == 'success':
            # Process Crossed Assets
            crossed_assets = response_data1.get('data', [])
            if crossed_assets:
                crossed_asset = crossed_assets[0]
                crossed = {
                    "coin": crossed_asset.get("coin"),
                    "totalAmount": float(crossed_asset.get("totalAmount", 0)),
                    "available": float(crossed_asset.get("available", 0)),
                    "frozen": float(crossed_asset.get("frozen", 0)),
                    "borrow": float(crossed_asset.get("borrow", 0)),
                    "interest": float(crossed_asset.get("interest", 0)),
                    "net": float(crossed_asset.get("net", 0))
                }
                # Update Total
                total["totalAmount"] += crossed["totalAmount"]
                total["available"] += crossed["available"]
                total["frozen"] += crossed["frozen"]
                total["borrow"] += crossed["borrow"]
                total["interest"] += crossed["interest"]
                total["net"] += crossed["net"]
            
            # Process Isolated Assets
            isolated_assets = response_data2.get('data', [])
            if isolated_assets:
                isolated_asset = isolated_assets[0]
                isolated = {
                    "coin": isolated_asset.get("coin"),
                    "totalAmount": float(isolated_asset.get("totalAmount", 0)),
                    "available": float(isolated_asset.get("available", 0)),
                    "frozen": float(isolated_asset.get("frozen", 0)),
                    "borrow": float(isolated_asset.get("borrow", 0)),
                    "interest": float(isolated_asset.get("interest", 0)),
                    "net": float(isolated_asset.get("net", 0))
                }
                # Update Total
                total["totalAmount"] += isolated["totalAmount"]
                total["available"] += isolated["available"]
                total["frozen"] += isolated["frozen"]
                total["borrow"] += isolated["borrow"]
                total["interest"] += isolated["interest"]
                total["net"] += isolated["net"]
            
            return {
                "crossed": crossed,
                "isolated": isolated,
                "total": total
            }
        else:
            # Handle API error and remove from blacklist
            available_ip = await self.proxy.get_machine_ip()
            await self.proxy.remove_ip_blacklist(ip=available_ip)            
            raise HTTPException(status_code=400, detail="An error occurred, please try again later")


    async def account_balance(self) -> dict:
        """Get account balance of each account"""
        request = "/api/v2/account/all-account-balance"
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
            balance_list = response_data.get('data', None)
            
            result = {
                "total": sum([float(balance['usdtBalance']) for balance in balance_list]),
                "accounts": {
                    balance['accountType']: float(balance['usdtBalance'])
                    for balance in balance_list
                }
            }

            return result
        else:
            print("An error ocurred: ",response_data)
            return None

async def main_test_bitget():
    proxy = await BrightProxy.create()
    ip = "58.97.135.175"


    bitget_account = BitgetLayerConnection(
        api_key="bg_7a55b38c349edfa10c66423cdf0817b0",
        api_secret_key="c30f1a5b694ebeaa5872f8e48fdcd3273ee961de025d967bc4a1b7b4104119e6",
        passphrase="EstoyHastaLaPutaPolla",
        proxy=proxy,
        ip=ip
    )
    
    balance = await bitget_account.future_assets()
    print("Balance: ", balance)

if __name__ == "__main__":
    asyncio.run(main_test_bitget())
