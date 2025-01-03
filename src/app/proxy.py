# src/app/proxy.py

import asyncio
import hashlib
import base64
import httpx
import sys
import json
import random
from typing import Optional, Literal
from fastapi import HTTPException
import logging

from src.config import BRIGHTDATA_API_TOKEN
from src.app.database.crud import get_used_ips

logger = logging.getLogger(__name__)

class BrightProxy:
    """
    API documentation: https://docs.brightdata.com/api-reference/account-management-api
    Select specific IP: https://docs.brightdata.com/api-reference/proxy/select_a_specific_ip
    """
    def __init__(self) -> None:
        # Debug: Log the actual HTTPX version in use
        logger.info(f"HTTPX VERSION IS: {httpx.__version__}")

        self.base_url = "https://api.brightdata.com"
        self.zones = ["main_zone"]
        self.proxy_address = "brd.superproxy.io:33335"
        self.proxy_pass = None
        self.customer_id = "hl_b6ea2507"

    @classmethod
    async def create(cls):
        instance = cls()
        try:
            await instance.set_password()
            if instance.proxy_pass is None:
                logger.error("Proxy password was not set.")
                raise Exception("Failed to set proxy password.")
            logger.info("BrightProxy instance created successfully.")
            return instance
        except Exception as e:
            logger.error(f"Failed to create BrightProxy instance: {e}", exc_info=True)
            raise

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
                    passwords = response_data.get("password", None)
                    if passwords and len(passwords) > 0:
                        self.proxy_pass = passwords[0]
                        logger.info("Proxy password set successfully.")
                    else:
                        logger.error("Password not found in the response.")
                        raise Exception("Password not found in the response.")
                else:
                    logger.error(f"API returned error: {response.status_code}, {response.text}")
                    raise Exception(f"API returned error: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Error during set_password: {e}", exc_info=True)
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
        logger.info(f"curl_api called with URL: {url}, Method: {method}, IP: {ip}")

        """
        Send a request using a static proxy and ensure JSON response.
        Uses a single proxy for both HTTP and HTTPS traffic by creating
        an AsyncHTTPTransport and specifying `proxy=...`.
        """
        try:
            proxy_url = (
                f"http://brd-customer-{self.customer_id}-zone-{self.zones[0]}"
                f"{'-ip-' + ip if ip else ''}:{self.proxy_pass}@{self.proxy_address}"
            )

            transport = httpx.AsyncHTTPTransport(proxy=proxy_url)

            async with httpx.AsyncClient(transport=transport) as client:
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
        except Exception as e:
            logger.error(f"Error during curl_api: {e}", exc_info=True)
            
            if e == '401 Auth Failed (code: ip_blacklisted)':
                machine_ip = await self.get_machine_ip()
                await self.remove_ip_blacklist(machine_ip)
                raise HTTPException(status_code=401, detail="Your IP address has been blacklisted, reload again the page to see your response")

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
        selected_ip = random.choice(least_used_ips)
        logger.info(f"Selected IP: {selected_ip}")
        return selected_ip
    
    async def status(self):
        """Get recent proxy status"""
        url = f"https://brightdata.com/api/zone/route_ips/zone={self.zones[0]}"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        logger.info(f"Proxy Status: {response.text}")
    
    async def remove_ip_blacklist(self, ip: str):
        """Remove an IP from the blacklist"""
        url = "https://api.brightdata.com/zone/blacklist"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}
        payload = {"ip": ip, "zone": self.zones[0]}

        async with httpx.AsyncClient() as client:
            response = await client.request(
                "DELETE",
                url,
                headers=headers,
                json=payload
            )
        
        logger.info(f"Remove IP Blacklist Response: Status Code: {response.status_code}, Content: {response.text}")
    
    async def get_blacklisted_ips(self):
        """Get all blacklisted IPs"""
        url = "https://api.brightdata.com/zone/blacklist"
        headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params={"zone": self.zones[0]})
            logger.info(f"Blacklisted IPs: {response.json()}")
    
    async def get_machine_ip(self):
        """Get the IP of the machine"""
        async with httpx.AsyncClient() as client:
            response = await client.get("https://ifconfig.me/all.json")
            result = response.json()
            machine_ip = result.get("ip_addr", None)
            logger.info(f"Machine IP: {machine_ip}")
            return machine_ip

async def proxy_testing():
    proxy = await BrightProxy.create()

    res = await proxy.get_machine_ip()
    print(f"Machine IP: {res}")
    # Uncomment below lines to test curl_api
    result = await proxy.curl_api(
        url="https://ifconfig.me/all.json",
        method="GET",
        ip="58.97.135.175"
    )
    print("Result from curl_api:", result)

if __name__ == "__main__":
    # Make sure to explicitly run this using the venv python,
    # e.g., ./venv/bin/python -m src.app.proxy
    asyncio.run(proxy_testing())
