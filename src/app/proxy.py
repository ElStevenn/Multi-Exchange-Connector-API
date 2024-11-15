import hmac
import asyncio
import hashlib
import base64
import httpx
import sys

from config import BRIGHTDATA_API_TOKEN

class BrightProxy:
    """
    API documentation: https://docs.brightdata.com/api-reference/account-management-api
    """
    def __init__(self) -> None:
        self.base_url = "https://api.brightdata.com"

    async def configure_proxy(self, proxy_address: str, proxy_user: str, proxy_pass: str, test_url: str):
        """Configure and test proxy"""
        proxies = {
            "http": f"http://{proxy_user}:{proxy_pass}@{proxy_address}",
            "https": f"http://{proxy_user}:{proxy_pass}@{proxy_address}",
        }

        async with httpx.AsyncClient(proxies=proxies) as client:
            try:
                response = await client.get(test_url)
                return {
                    "status": response.status_code,
                    "text": response.text
                }
            except httpx.RequestError as e:
                return {
                    "error": str(e)
                }
 
    async def get_zone_details(self):
        url = "https://api.brightdata.com/zone?zone=main_zone"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()  
            else:
                return {"error": response.text}

    async def test_proxy(self, proxy_address: str, proxy_user: str, proxy_pass: str):
        """Test the proxy by sending a request to Bright Data's test endpoint"""
        test_url = "https://geo.brdtest.com/welcome.txt?product=dc&method=native"
        proxies = {
            "http": f"http://{proxy_user}:{proxy_pass}@{proxy_address}",
            "https": f"http://{proxy_user}:{proxy_pass}@{proxy_address}",
        }
        async with httpx.AsyncClient(proxies=proxies) as client:
            try:
                response = await client.get(test_url)
                return {
                    "status": response.status_code,
                    "text": response.text
                }
            except httpx.RequestError as e:
                return {
                    "error": str(e)
                }


async def main_testings():
    proxy = BrightProxy()

    # Fetch zone details
    zone_details = await proxy.get_zone_details()
    print("Zone Details:", zone_details)

    # Test the proxy
    if "ips" in zone_details and zone_details["ips"] != ["any"]:
        proxy_address = "brd.superproxy.io:22225"
        proxy_user = f"brd-customer-hl_b6ea2507-zone-main_zone-ip-{zone_details['ips'][0]}"
        proxy_pass = zone_details['password'][0]
        proxy_test = await proxy.test_proxy(proxy_address, proxy_user, proxy_pass)
        print("Proxy Test:", proxy_test)
    else:
        print("Zone is dynamically assigned (ips: 'any'), cannot test static IPSecurity settings.")


if __name__ == "__main__":
    asyncio.run(main_testings())
