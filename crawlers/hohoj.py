import re
import logging
from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

class HohoJCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(base_url="https://hohoj.tv")
        self.source_name = "HohoJ"

    async def crawl_new_videos(self, pages=1):
        # HohoJ doesn't seem to have a simple 'new' page like MissAV
        # For now, let's just implement search.
        return []

    async def search(self, keyword, limit=5):
        search_url = f"{self.base_url}/search?text={keyword}"
        html = await self.fetch_html(search_url)
        if not html: return []
        
        # HohoJ search results are direct links like /video?id=...
        ids = re.findall(r'/video\?id=(\d+)', html)
        results = []
        for vid in ids[:limit]:
            # We don't have titles in the ID list, but we can return basic info
            results.append({
                'code': keyword.upper(), # Assuming search was by code
                'detail_url': f"{self.base_url}/video?id={vid}",
                'source': 'HohoJ'
            })
        return results

    async def crawl_video_detail(self, url):
        # Extract ID from URL
        match = re.search(r'id=(\d+)', url)
        if not match: return None
        vid = match.group(1)
        
        embed_url = f"{self.base_url}/embed?id={vid}"
        html = await self.fetch_html(embed_url, referer=url)
        if not html: return None
        
        video = {'detail_url': url, 'code': vid} # ID as fallback code
        
        # Extract m3u8
        hls_match = re.search(r'var videoSrc\s*=\s*"([^"]+)"', html)
        if hls_match:
            video['preview_url'] = hls_match.group(1)
            
        # HohoJ duration (often in script or meta)
        duration_minutes = None
        soup = BeautifulSoup(html, 'html.parser')
        # Try metadata
        meta = soup.find('meta', attrs={'property': 'og:video:duration'}) or \
               soup.find('meta', attrs={'itemprop': 'duration'})
        if meta:
            num = re.search(r'(\d+)', meta.get('content', ''))
            if num:
                v = int(num.group(1))
                duration_minutes = v // 60 if v > 500 else v

        if not duration_minutes:
            duration_match = re.search(r'duration\s*:\s*(\d+)', html, re.IGNORECASE)
            if not duration_match:
                duration_match = re.search(r'(\d+)\s*(分|min)', html)
                
            if duration_match:
                v = int(duration_match.group(1))
                duration_minutes = v // 60 if v > 500 else v
        
        if not duration_minutes:
            # Try finding HH:MM:SS or MM:SS pattern
            time_match = re.search(r'(\d{1,2}:\d{2}(:\d{2})?)', html)
            if time_match:
                duration_minutes = self._parse_duration_string(time_match.group(1))
            
        video['duration'] = duration_minutes
        video['source'] = self.source_name
        return video

    def _parse_duration_string(self, s):
        """Convert HH:MM:SS or MM:SS to minutes"""
        parts = s.split(':')
        if len(parts) == 3: # HH:MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 2: # MM:SS
            return int(parts[0])
        return None
