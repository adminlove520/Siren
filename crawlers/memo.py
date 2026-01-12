import re
import logging
import json
from urllib.parse import unquote
from crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

class MemoCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(base_url="memojav.com")

    async def search(self, keyword, limit=5):
        # Memo search is a bit more complex, based on NASSAV logic:
        # https://{self.domain}/hls/get_video_info.php?id={avid}&sig=NTg1NTczNg&sts=7264825
        # This seems to be a direct info fetcher rather than search.
        # For consistency, let's just use it as a detail fetcher.
        return []

    async def crawl_video_detail(self, url_or_code):
        # Memo logic from NASSAV
        code = url_or_code.split('=')[-1] if '=' in url_or_code else url_or_code
        info_url = f"https://{self.base_url}/hls/get_video_info.php?id={code}&sig=NTg1NTczNg&sts=7264825"
        
        html = await self.fetch_html(info_url, referer=f"https://{self.base_url}")
        if not html: return None
        
        video = {'code': code.upper()}
        # Extract URL from JSON-like string
        pattern = r'"url":"(https?%3A%2F%2F[^"]+)"'
        match = re.search(pattern, html)
        if match:
            encoded_url = match.group(1)
            video['preview_url'] = unquote(encoded_url)
            
        return video
