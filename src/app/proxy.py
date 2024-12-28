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
        # Debug: Print the actual HTTPX version in use
        print("HTTPX VERSION IS:", httpx.__version__)

        self.base_url = "https://api.brightdata.com"
        self.zones = ["main_zone"]
        self.proxy_address = "brd.superproxy.io:33335"
        self.proxy_pass = None
        self.customer_id = "hl_b6ea2507"

    @classmethod
    async def create(cls):
        instance = cls()
        await instance.set_password()
        return instance
    
    async def set_password(self):
        try:
            url = f"{self.base_url}/zone?zone={self.zones[0]}"
            headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
            
            # Custom timeouts: 10s total, 5s for connect
            timeout = httpx.Timeout(10.0, connect=5.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    response_data = response.json()
                    self.proxy_pass = response_data.get("password", None)[0]
                else:
                    raise Exception(f"API returned error: {response.status_code}, {response.text}")
        except Exception as e:
            raise Exception(f"Error during set_password: {e}")

    async def configure_proxy(self, proxy_address: str, proxy_user: str, proxy_pass: str, test_url: str):
        """Configure and test proxy"""
        proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_address}"
        transport = httpx.AsyncHTTPTransport(proxy=proxy_url)

        async with httpx.AsyncClient(transport=transport) as client:
            try:
                response = await client.get(test_url)
                return {"status": response.status_code, "text": response.text}
            except httpx.RequestError as e:
                return {"error": str(e)}
            
    async def curl_api(
        self,
        url: str,
        method: Literal['GET', 'POST', 'PUT', 'DELETE'] = 'GET',
        body: Optional[dict] = {},
        headers: Optional[dict] = {},
        ip: Optional[str] = None
    ):
        """
        Send a request using a static proxy and ensure JSON response.
        Uses a single proxy for both HTTP and HTTPS traffic by creating
        an AsyncHTTPTransport and specifying `proxy=...`.
        """
        proxy_url = (
            f"http://brd-customer-{self.customer_id}-zone-{self.zones[0]}"
            f"{'-ip-' + ip if ip else ''}:{self.proxy_pass}@{self.proxy_address}"
        )

        transport = httpx.AsyncHTTPTransport(proxy=proxy_url)

        async with httpx.AsyncClient(transport=transport) as client:
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
                    return {
                        "status": response.status_code,
                        "content": response.text.strip()
                    }
            except httpx.RequestError as e:
                return {"error": str(e)}

    async def get_zones(self) -> list:
        """Get all active zones"""
        url = "https://api.brightdata.com/zone/get_active_zones"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        return [zn.get("name") for zn in response.json()]

    async def get_allocated_ips(self) -> list:
        """Get allocated IPs in the first zone."""
        url = f"https://api.brightdata.com/zone/ips?zone={self.zones[0]}"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        json_ips = response.json()
        return [ip["ip"] for ip in json_ips["ips"]]

    async def select_ip(self):
        """Select an IP with the least usage"""
        used_ips = await get_used_ips()
        allocated_ips = await self.get_allocated_ips()

        ip_usage = {ip: 0 for ip in allocated_ips}
        for entry in used_ips:
            if entry["ip"] in ip_usage:
                ip_usage[entry["ip"]] = entry["used"]

        min_usage = min(ip_usage.values())
        least_used_ips = [ip for ip, usage in ip_usage.items() if usage == min_usage]
        return random.choice(least_used_ips)

    async def status(self):
        """Get recent proxy status"""
        url = f"https://brightdata.com/api/zone/route_ips/zone={self.zones[0]}"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        print(response.text)

    async def remove_ip_blacklist(self, ip: str):
        """Remove an IP from the blacklist"""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                "DELETE",
                "https://api.brightdata.com/zone/blacklist",
                headers={"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"},
                json={"ip": ip, "zone": self.zones[0]}
            )
        
        print("Status Code:", response.status_code)
        print("Response Content:", response.text)

        if response.status_code == 204:
            print("IP successfully removed. No content returned.")
        elif response.headers.get("content-type") == "application/json":
            print(response.json())
        else:
            print("Unexpected response content.")

    async def get_blacklisted_ips(self):
        """Get all blacklisted IPs"""
        url = "https://api.brightdata.com/zone/blacklist"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params={"zone": self.zones[0]})
            print(response.text)
            print(response.status_code)
            res = response.json()
            print(res)

    async def get_machine_ip(self):
        """Get the IP of the machine"""
        async with httpx.AsyncClient() as client:
            response = await client.get("https://ifconfig.me/all.json")

            result =  response.json()

            return result.get("ip_addr", None)

async def proxy_testing():
    proxy = await BrightProxy.create()

    res = await proxy.get_machine_ip(); print(res)
    # result = await proxy.curl_api(
    #     url="https://ifconfig.me",
    #     method="GET",
    #     ip="58.97.135.175"
    # )
    # print("Result from curl_api:", result)

if __name__ == "__main__":
    # Make sure to explicitly run this using the venv python,
    # e.g., ./venv/bin/python -m src.app.proxy
    asyncio.run(proxy_testing())
