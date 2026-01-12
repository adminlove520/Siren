import asyncio
import logging
from curl_cffi.requests import AsyncSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_memojav")

async def test_memojav():
    url = "https://memojav.com"
    # Testing with several impersonations to see which one works
    impersonations = ["chrome110", "safari15_5", "chrome120"]
    
    for imp in impersonations:
        logger.info(f"Testing {url} with impersonation: {imp}")
        async with AsyncSession(impersonate=imp, timeout=20.0, verify=False) as session:
            try:
                response = await session.get(url)
                title_snippet = response.text[:100].replace('\n', ' ')
                logger.info(f"✅ [{imp}] Success! Title: {title_snippet}")
            except Exception as e:
                logger.error(f"❌ [{imp}] Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_memojav())
