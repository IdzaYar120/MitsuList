import httpx
import asyncio
from django.core.cache import cache
import time

async def fetch_jikan_data(cache_key, url, timeout=300):
    """
    Asynchronously fetch data from Jikan API with caching and non-blocking throttling.
    """
    # Check cache first
    data = await asyncio.to_thread(cache.get, cache_key)
    if data:
        return data

    # Non-blocking throttling (approx 3 requests/sec)
    await asyncio.sleep(0.4)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                await asyncio.to_thread(cache.set, cache_key, data, timeout)
                return data
            elif response.status_code == 429:
                print(f"Rate limited on {url}")
            else:
                print(f"Error {response.status_code} for {url}")
        except httpx.RequestError as exc:
            print(f"Connection error: {exc}")
    
    return {'data': []}
