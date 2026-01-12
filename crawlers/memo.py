import re
import logging
import json
from urllib.parse import unquote
from crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

class MemoCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(base_url="https://memojav.com")
        self.source_name = "Memo"

    async def search(self, keyword, limit=5):
        # Memo search URL: https://memojav.com/browse/search?q=keyword
        url = f"{self.base_url}/browse/search?q={keyword}"
        html = await self.fetch_html(url)
        if not html: return []
        
        # Simple regex to find video links: /video/CODE
        matches = re.findall(r'/video/([A-Z0-9-]+)', html)
        results = []
        for code in list(set(matches))[:limit]:
            results.append({
                'code': code.upper(),
                'detail_url': f"{self.base_url}/video/{code}",
                'source': self.source_name
            })
        return results

    async def crawl_video_detail(self, url_or_code):
        code = url_or_code.split('/')[-1] if '/' in url_or_code else url_or_code
        detail_url = url_or_code if url_or_code.startswith('http') else f"{self.base_url}/video/{code}"
        
        html = await self.fetch_html(detail_url)
        if not html: return None
        
        video = {'code': code.upper(), 'detail_url': detail_url, 'source': self.source_name}
        
        # Meta parsing for duration (ISO 8601 format: PT141M0S)
        duration_minutes = None
        duration_match = re.search(r'<meta itemprop="duration" content="PT(\d+)M', html)
        if duration_match:
            duration_minutes = int(duration_match.group(1))
        else:
            # Fallback search
            duration_match = re.search(r'(\d+)\s*(分|min)', html)
            if duration_match:
                duration_minutes = int(duration_match.group(1))

        video['duration'] = duration_minutes
        
        # Fetch preview URL using the existing PHP logic if needed, 
        # but let's see if it's in the page first
        hls_match = re.search(r'"url":"(https?%3A%2F%2F[^"]+)"', html)
        if hls_match:
            video['preview_url'] = unquote(hls_match.group(1))
        else:
            # Fallback to PHP info fetcher
            info_url = f"{self.base_url}/hls/get_video_info.php?id={code}&sig=NTg1NTczNg&sts=7264825"
            info_html = await self.fetch_html(info_url, referer=detail_url)
            if info_html:
                hls_match = re.search(r'"url":"(https?%3A%2F%2F[^"]+)"', info_html)
                if hls_match:
                    video['preview_url'] = unquote(hls_match.group(1))

        return video
