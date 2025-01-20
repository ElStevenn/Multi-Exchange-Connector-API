import asyncio
import base64
import hmac
import time
import json
import hashlib
import sys
from typing import Dict
from fastapi import HTTPException

if len(sys.argv) > 1 and sys.argv[1] == "test":
    from src.app.proxy import BrightProxy
else:
    from app.proxy import BrightProxy

class KucoinLayerConnection:
    def __init__(self, api_key, api_secret_key, passphrase, proxy: BrightProxy, ip: str) -> None:
        self.api_key = api_key
        self.api_secret_key = api_secret_key
        self.passphrase = passphrase
        self.proxy = proxy
        self.ip = ip
        self.api_url = "https://api.kucoin.com"

    def generate_signature(self, prehash_string: str) -> str:
        return base64.b64encode(
            hmac.new(
                self.api_secret_key.encode("utf-8"),
                prehash_string.encode("utf-8"),
                hashlib.sha256
            ).digest()
        ).decode()

    def generate_passphrase(self) -> str:
        return base64.b64encode(
            hmac.new(
                self.api_secret_key.encode("utf-8"),
                self.passphrase.encode("utf-8"),
                hashlib.sha256
            ).digest()
        ).decode()

    def get_headers(self, method: str, request_path: str, query_params: dict, body_params: dict) -> dict:
        timestamp = str(int(time.time() * 1000))
        method = method.upper()
        query_string = ""
        if query_params:
            sorted_params = sorted(query_params.items(), key=lambda x: x[0])
            query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
            request_path_with_params = request_path + "?" + query_string
        else:
            request_path_with_params = request_path

        if body_params:
            body = json.dumps(body_params)
        else:
            body = ""

        prehash_string = timestamp + method + request_path_with_params + body
        signature = self.generate_signature(prehash_string)
        passphrase = self.generate_passphrase()

        headers = {
            "Content-Type": "application/json",
            "KC-API-KEY": self.api_key,
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": timestamp,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-KEY-VERSION": "2"
        }
        return headers

    async def get_account_information(self) -> dict:
        request = "/api/v2/user-info"
        url = f"{self.api_url}{request}"
        headers = self.get_headers("GET", request, {}, {})
        response_data = await self.proxy.curl_api(
            url=url,
            body={},
            method="GET",
            headers=headers,
            ip=self.ip
        )
        if response_data.get("code") == "200000":
            return response_data.get("data", None)
        else:
            await self.proxy.remove_ip_blacklist(ip=self.ip)
            raise HTTPException(status_code=400, detail="An error ocurred, please try again later")

    async def furues_assets(self) -> dict:
        request = "/api/v1/account-overview"
        url = f"{self.api_url}{request}"
        params = {"currency": "USDT"}
        headers = self.get_headers("GET", request, params, {})
        response_data = await self.proxy.curl_api(
            url=url,
            body=params,
            method="GET",
            headers=headers,
            ip=self.ip
        )
        if response_data.get("code") == "200000":
            return response_data.get("data", None)
        else:
            avariable_ip = await self.proxy.get_machine_ip()
            await self.proxy.remove_ip_blacklist(ip=avariable_ip)
            raise HTTPException(status_code=400, detail="An error ocurred, please try again later")

    async def spot_assets(self) -> dict:
        request = "/api/v1/accounts"
        url = f"{self.api_url}{request}"
        params = {"type": "trade"}
        headers = self.get_headers("GET", request, params, {})
        response_data = await self.proxy.curl_api(
            url=url,
            body=params,
            method="GET",
            headers=headers,
            ip=self.ip
        )
        if response_data.get("code") == "200000":
            asset_list = response_data.get("data", [])
            assets = []
            for asset in asset_list:
                available = float(asset["balance"]) - float(asset["hold"])
                assets.append({
                    "symbol": asset["currency"],
                    "available": str(available),
                    "limitAvailable": str(available),
                    "frozen": asset["hold"],
                    "locked": "0"
                })
            return assets
        else:
            avariable_ip = await self.proxy.get_machine_ip()
            await self.proxy.remove_ip_blacklist(ip=avariable_ip)
            raise HTTPException(status_code=400, detail="An error ocurred, please try again later")

    async def margin_assets_summary(self) -> Dict:
        # Cross (Basic) Margin
        crossed_request = "/api/v1/margin/account"
        crossed_url = f"{self.api_url}{crossed_request}"
        crossed_headers = self.get_headers("GET", crossed_request, {}, {})
        response_data1 = await self.proxy.curl_api(
            url=crossed_url,
            body={},
            method="GET",
            headers=crossed_headers,
            ip=self.ip
        )

        # Isolated Margin
        isolated_request = "/api/v1/isolated/accounts"
        isolated_url = f"{self.api_url}{isolated_request}"
        isolated_params = {"symbols": "BTC-USDT"}
        isolated_headers = self.get_headers("GET", isolated_request, isolated_params, {})
        response_data2 = await self.proxy.curl_api(
            url=isolated_url,
            body=isolated_params,
            method="GET",
            headers=isolated_headers,
            ip=self.ip
        )

        crossed, isolated = {}, {}
        total = {
            "totalAmount": 0.0,
            "available": 0.0,
            "frozen": 0.0,
            "borrow": 0.0,
            "interest": 0.0,
            "net": 0.0
        }

        if response_data1.get("code") == "200000" and response_data2.get("code") == "200000":
            cross_data = response_data1.get("data", {})
            if cross_data:
                crossed = {
                    "coin": "USDT",  # or any currency you'd like to parse
                    "totalAmount": float(cross_data.get("totalBalance", 0)),
                    "available": float(cross_data.get("availableBalance", 0)),
                    "frozen": 0.0,
                    "borrow": float(cross_data.get("liability", 0)),
                    "interest": float(cross_data.get("interestBalance", 0)),
                    "net": float(cross_data.get("netBalance", 0))
                }
                total["totalAmount"] += crossed["totalAmount"]
                total["available"] += crossed["available"]
                total["frozen"] += crossed["frozen"]
                total["borrow"] += crossed["borrow"]
                total["interest"] += crossed["interest"]
                total["net"] += crossed["net"]

            iso_data = response_data2.get("data", {}).get("assets", [])
            if iso_data:
                # Taking the first symbol for demonstration
                asset = iso_data[0]
                isolated = {
                    "coin": asset.get("baseAsset", {}).get("currency"),
                    "totalAmount": float(asset.get("baseAsset", {}).get("totalBalance", 0)),
                    "available": float(asset.get("baseAsset", {}).get("availableBalance", 0)),
                    "frozen": 0.0,
                    "borrow": float(asset.get("baseAsset", {}).get("borrowBalance", 0)),
                    "interest": float(asset.get("baseAsset", {}).get("interestBalance", 0)),
                    "net": float(asset.get("baseAsset", {}).get("netBalance", 0))
                }
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
            available_ip = await self.proxy.get_machine_ip()
            await self.proxy.remove_ip_blacklist(ip=available_ip)
            raise HTTPException(status_code=400, detail="An error occurred, please try again later")

    async def account_balance(self) -> dict:
        # Fetch spot, margin, and main accounts
        request = "/api/v1/accounts"
        url = f"{self.api_url}{request}"
        headers = self.get_headers("GET", request, {}, {})
        response_data = await self.proxy.curl_api(
            url=url,
            body={},
            method="GET",
            headers=headers,
            ip=self.ip
        )
        
        if response_data.get("code") == "200000":
            balance_list = response_data.get("data", [])
            total_usdt = 0.0
            accounts = {}

            # Initialize specific categories
            spot_balance = 0.0
            margin_balance = 0.0

            for balance in balance_list:
                account_type = balance["type"]
                balance_value = float(balance["balance"])
                currency = balance["currency"]

                if account_type not in accounts:
                    accounts[account_type] = 0.0

                if currency == "USDT":
                    accounts[account_type] += balance_value
                    total_usdt += balance_value

                    # Sum up spot balances (main + trade)
                    if account_type in ["main", "trade"]:
                        spot_balance += balance_value

                    # Sum up margin balances
                    if account_type == "margin":
                        margin_balance += balance_value

            # Add explicit categories
            accounts["spot"] = round(spot_balance, 10)
            accounts["margin"] = round(margin_balance, 10)

            # Fetch futures account balance from Futures API
            futures_request = "/api/v1/account-overview"
            futures_url = f"https://api-futures.kucoin.com{futures_request}"
            futures_headers = self.get_headers("GET", futures_request, {}, {})  # Futures API headers
            futures_response = await self.proxy.curl_api(
                url=futures_url,
                body={},
                method="GET",
                headers=futures_headers,
                ip=self.ip
            )

            if futures_response.get("code") == "200000":
                futures_balance = float(futures_response["data"].get("accountEquity", 0.0))
                unrealized_pnl = float(futures_response["data"].get("unrealisedPNL", 0.0))
                accounts["futures"] = round(futures_balance, 10)
                total_usdt += futures_balance + unrealized_pnl
            else:
                accounts["futures"] = 0.0

            # Construct the result
            result = {
                "total": round(total_usdt, 10),
                "accounts": {k: round(v, 10) if v >= 1e-10 else 0.0 for k, v in accounts.items()}
            }
            return result
        else:
            return {"error": response_data.get("msg", "Unknown error")}






async def main_test_kucoin():
    proxy = await BrightProxy.create()
    ip = "94.139.50.252"
    kucoin_connection = KucoinLayerConnection(
        None, None, None, None
    )
    # Example usage:
    info = await kucoin_connection.account_balance()
    print("Account info:", info)

if __name__ == "__main__":
    asyncio.run(main_test_kucoin())
