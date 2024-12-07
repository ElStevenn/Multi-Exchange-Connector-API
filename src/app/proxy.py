import asyncio
import hashlib
import base64
import httpx
import sys
import json
import random
from typing import Optional, Literal
from fastapi import HTTPException

from src.config import BRIGHTDATA_API_TOKEN
from src.app.database.crud import get_used_ips


class BrightProxy:
    """
    API documentation: https://docs.brightdata.com/api-reference/account-management-api
    Select specific IP: https://docs.brightdata.com/api-reference/proxy/select_a_specific_ip
    """
    def __init__(self) -> None:
        self.base_url = "https://api.brightdata.com"
        self.zones = ["isp_proxy1"]
        self.proxy_address = f"brd.superproxy.io:33335"
        self.proxy_pass = None     
        self.customer_id = "hl_9f87e5f6"

    @classmethod
    async def create(cls):
        instance = cls()
        await instance.set_password()
        return instance
    
    async def set_password(self):
        try:
            url = f"{self.base_url}/zone?zone={self.zones[0]}"
            headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    response_data = response.json()

                    # Set proxy password
                    self.proxy_pass = response_data.get('password', None)[0]

                else:
                    raise Exception(f"API returned error: {response.status_code}, {response.text}")
        except Exception as e:
            raise Exception(f"Error during set_password: {e}")

    async def configure_proxy(self, proxy_address: str, proxy_user: str, proxy_pass: str, test_url: str):
        """Configure and test proxy"""
        proxies = {
            "http": f"http://{proxy_user}:{proxy_pass}t{proxy_address}",
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
            
    async def curl_api(self, url: str, method: Literal['GET', 'POST', 'PUT', 'DELETE'] = 'GET',  body: Optional[dict] = {}, headers: Optional[dict] = {}, ip: Optional[str] = None):
        """Send CURL sol using static PROXY and ensure JSON response"""
        proxy_url = f"http://brd-customer-{self.customer_id}-zone-{self.zones[0]}{'-ip-' + ip if ip else ''}:{self.proxy_pass}@{self.proxy_address}"
        print("proxy url", proxy_url)
        proxies = {
            "http://": proxy_url,
            "https://": proxy_url,
        }

        async with httpx.AsyncClient(proxies=proxies) as client:
            try:
                if method == "GET":
                    response = await client.get(url, params=body, headers=headers)
                elif method == "POST":
                    response = await client.post(url, json=body, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, json=body, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, json=body, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
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
        used_ips = await get_used_ips()
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


    async def status(self):
        """Get recent proxy status"""
        url = f"https://brightdata.com/api/zone/route_ips/zone={self.zones[0]}"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        print(response.text)


 

async def proxy_testing():
    proxy = await BrightProxy.create()

    
    # Proxy Status
    # status = await proxy.status(); print(status)
    
    # Zones
    zones = await proxy.get_zones(); print("Zones:", zones)

    # Current asociated Ips
    ips = await proxy.get_allocated_ips(); print("Asociated Ips:", ips)

    # Curl Test
    result = await proxy.curl_api(
        url="https://ifconfig.me/all.json",
        method='GET',
        ip="185.246.219.114"
    );print(result)

    # Get IP
    ip = await proxy.select_ip(); print("ip selected", ip)
    


  

if __name__ == "__main__":
    asyncio.run(proxy_testing())
