import hmac
import asyncio
import hashlib
import base64
import httpx
import sys
import json
import random
from typing import Optional

from src.config import BRIGHTDATA_API_TOKEN
from src.app.utils import IpsManagement
from src.app.database.crud import select_used_ips

ips_management = IpsManagement()

class BrightProxy:
    """
    API documentation: https://docs.brightdata.com/api-reference/account-management-api
    Select specific IP: https://docs.brightdata.com/api-reference/proxy/select_a_specific_ip
    """
    def __init__(self) -> None:
        self.base_url = "https://api.brightdata.com"
        self.zones = ["main_zone"]

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
        url = "https://api.brightdata.com/proxies"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()  
            else:
                return {"error": response.text}

    async def curl_api(self, url: str, proxy_address: str, customer_id: str, proxy_pass: str, ip: Optional[str] = None):
        """Send CURL sol using static PROXY and ensure JSON response"""
        proxy_url = f"http://{customer_id}{'-ip-' + ip if ip else ''}:{proxy_pass}@{proxy_address}"

        proxies = {
            "http://": proxy_url,
            "https://": proxy_url,
        }

        async with httpx.AsyncClient(proxies=proxies) as client:
            try:
                response = await client.get(url)
                try:
                    return response.json()
                except ValueError:
                    # If not JSON, wrap response in a JSON object
                    return {
                        "status": response.status_code,
                        "content": response.text.strip() 
                    }
            except httpx.RequestError as e:
                # Return error in JSON format
                return {
                    "error": str(e)
                }


    async def get_zones(self) -> list:
        """Get all active zones"""
        url = "https://api.brightdata.com/zone/get_active_zones"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        return [zn.get('name') for zn in response.json()]
        

    async def get_allocated_ips(self) -> list:
        """Get allocated IPs"""
        url = f"https://api.brightdata.com/zone/ips?zone={self.zones[0]}"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        json_ips = response.json()

        return [ip['ip'] for ip in json_ips['ips']]

    async def select_ip(self):
        """Select IP to set user new IP"""
        used_ips = await select_used_ips()
        alocated_ips = await self.get_allocated_ips()

        ip_usage = {ip: 0 for ip in alocated_ips}
        for entry in used_ips:
            if entry['ip'] in ip_usage:
                ip_usage[entry['ip']] = entry['used']

        # Find minimum usage count and collect IPs with minumum usage count
        min_usage = min(ip_usage.values())
        least_used_ips = [ip for ip, usage in ip_usage.items() if usage == min_usage]

        select_ip = random.choice(least_used_ips)

        return select_ip


    async def add_static_ip(self, ):
        pass
        

async def main_testings():
    proxy = BrightProxy()

    # Test PROXY with static IP
    """
    result = await proxy.curl_api(
        url="https://ifconfig.me/all.json",
        proxy_address="brd.superproxy.io:22225",
        customer_id="brd-customer-hl_b6ea2507-zone-main_zone",
        proxy_pass="m02xj2u0a186",
        ip="58.97.235.32"
    );print(result)
    """

    # Scripts
    res = await proxy.select_ip()
    print("result -> ",res)

if __name__ == "__main__":
    asyncio.run(main_testings())
