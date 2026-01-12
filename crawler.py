import asyncio
import logging
from .crawlers.missav import MissavCrawler
from .crawlers.jable import JableCrawler
from .crawlers.hohoj import HohoJCrawler
from .crawlers.memo import MemoCrawler

logger = logging.getLogger(__name__)

class CrawlerManager:
    def __init__(self):
        self.crawlers = [
            MissavCrawler(),
            JableCrawler(),
            HohoJCrawler(),
            MemoCrawler()
        ]

    async def init_session(self):
        # We could initialize sessions for all, but typically they 
        # initialize on first request or have a warm-up.
        pass

    async def crawl_new_videos(self, pages=1):
        # By default, we use MissAV for the main "new videos" feed
        # but we could merge from others later.
        main_crawler = self.crawlers[0] # Missav
        return await main_crawler.crawl_new_videos(pages=pages)

    async def search(self, keyword, limit=5):
        tasks = [crawler.search(keyword, limit=limit) for crawler in self.crawlers]
        results = await asyncio.gather(*tasks)
        
        # Merge results and deduplicate by code
        merged = {}
        for res_list in results:
            for video in res_list:
                code = video.get('code')
                if code and code not in merged:
                    merged[code] = video
        
        return list(merged.values())[:limit]

    async def crawl_video_detail(self, url_or_code):
        if url_or_code.startswith('http'):
            for crawler in self.crawlers:
                if crawler.base_url in url_or_code:
                    return await crawler.crawl_video_detail(url_or_code)
        else:
            # Code search: try to find the video detail from any source
            code = url_or_code.upper()
            search_results = await self.search(code, limit=1)
            if search_results:
                video = search_results[0]
                detail = await self.crawl_video_detail(video['detail_url'])
                if detail:
                    video.update(detail)
                return video
        return None

    async def close(self):
        for crawler in self.crawlers:
            await crawler.close()

# For backward compatibility
MissavCrawler = CrawlerManager
