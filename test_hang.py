import sys
import asyncio
import httpx

async def main():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get('http://127.0.0.1:8001/', timeout=5)
            print(f"Status: {res.status_code}")
            print(f"Content Length: {len(res.text)}")
            with open('dump.html', 'w', encoding='utf-8') as f:
                f.write(res.text)
            print("Successfully dumped HTML to dump.html")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
