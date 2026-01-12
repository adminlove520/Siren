import asyncio
import logging
import random
from curl_cffi.requests import AsyncSession

logger = logging.getLogger(__name__)

class BaseCrawler:
    def __init__(self, base_url, user_agent=None):
        self.base_url = base_url
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        self.session = AsyncSession(
            impersonate="chrome120",
            timeout=30.0
        )

    async def fetch_html(self, url, referer=None):
        await asyncio.sleep(random.uniform(1, 2))
        try:
            headers = {"Referer": referer} if referer else {}
            response = await self.session.get(url, headers=headers, allow_redirects=True)
            if response.status_code == 200:
                return response.text
            logger.warning("Fetch failed: %s status %d", url, response.status_code)
        except Exception as e:
            logger.error("Error fetching %s: %s", url, e)
        return None

    def parse_video_card(self, card):
        """Parse a single video card from a list page"""
        raise NotImplementedError

    async def crawl_new_videos(self, pages=1):
        """Crawl latest videos"""
        raise NotImplementedError

    async def search(self, keyword, limit=5):
        """Search videos by keyword"""
        raise NotImplementedError

    async def crawl_video_detail(self, url):
        """Crawl full details of a video"""
        raise NotImplementedError

    async def close(self):
        pass
