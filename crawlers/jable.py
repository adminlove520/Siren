import re
import logging
from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

class JableCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(base_url="https://jable.tv")
        self.source_name = "Jable"
        self.CODE_PATTERN = re.compile(r'([A-Z]+-\d+)', re.IGNORECASE)

    async def crawl_new_videos(self, pages=1):
        all_videos = []
        new_url = f"{self.base_url}/latest-updates/"
        for page in range(1, pages + 1):
            url = f"{new_url}{page}/" if page > 1 else new_url
            html = await self.fetch_html(url)
            if not html: continue
            
            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.select('div.video-img-box')
            
            page_videos = []
            for card in cards:
                video = self.parse_video_card(card)
                if video.get('code'):
                    page_videos.append(video)
            all_videos.extend(page_videos)
        return all_videos

    def parse_video_card(self, card):
        video = {}
        link_tag = card.find('a', href=True)
        if link_tag:
            href = link_tag['href']
            video['detail_url'] = href if href.startswith('http') else f"{self.base_url}{href}"
            
        title_tag = link_tag.find('img') if link_tag else None
        if title_tag:
            video['title'] = title_tag.get('title') or title_tag.get('alt')
            video['cover_url'] = title_tag.get('data-src') or title_tag.get('src')
            
        code_tag = card.find('span', class_='absolute-center')
        if code_tag:
            video['code'] = code_tag.get_text(strip=True).upper()
            
        # Jable often has duration in span.label
        duration_tag = card.find('span', class_='label')
        if duration_tag:
            video['duration'] = self._parse_duration_string(duration_tag.get_text(strip=True))
            
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

    async def search(self, keyword, limit=5):
        # Jable search URL: https://jable.tv/search/keyword/
        url = f"{self.base_url}/search/{keyword}/"
        html = await self.fetch_html(url)
        if not html: return []
        
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('div.video-img-box')
        
        results = []
        for card in cards[:limit]:
            video = self.parse_video_card(card)
            if video.get('code'):
                results.append(video)
        return results

    async def crawl_video_detail(self, url):
        html = await self.fetch_html(url)
        if not html: return None
        
        soup = BeautifulSoup(html, 'html.parser')
        video = {'detail_url': url}
        
        title_el = soup.find('h4')
        if title_el: video['title'] = title_el.get_text(strip=True)
        
        code_match = self.CODE_PATTERN.search(video.get('title', ''))
        video['code'] = code_match.group(1).upper() if code_match else None
        
        # Jable has hlsUrl in script
        hls_match = re.search(r"var hlsUrl = '(https?://[^']+)'", html)
        if hls_match:
            video['preview_url'] = hls_match.group(1)
            
        # Enhanced duration extraction for Jable
        duration_minutes = None
        # Priority 1: Metadata
        meta_duration = soup.find('meta', attrs={'property': 'og:video:duration'}) or \
                        soup.find('meta', attrs={'itemprop': 'duration'}) or \
                        soup.find('meta', attrs={'name': 'twitter:data2'}) # Some sites use this
        if meta_duration:
            content = meta_duration.get('content', '') or meta_duration.get('value', '')
            num_match = re.search(r'(\d+)', content)
            if num_match:
                val = int(num_match.group(1))
                # Jable meta tags are often in seconds
                duration_minutes = val // 60 if val > 500 else val
        
        # Priority 2: Script tags (Jable often has video info in scripts)
        if not duration_minutes:
            script_match = re.search(r'duration\s*:\s*(\d+)', html, re.IGNORECASE)
            if script_match:
                val = int(script_match.group(1))
                duration_minutes = val // 60 if val > 500 else val
                
        # Priority 3: Text regex fallback
        if not duration_minutes:
            duration_match = re.search(r'(\d+)\s*(分|min)', html)
            if duration_match:
                duration_minutes = int(duration_match.group(1))
            else:
                # Try finding HH:MM:SS or MM:SS pattern
                time_match = re.search(r'(\d{1,2}:\d{2}(:\d{2})?)', html)
                if time_match:
                    duration_minutes = self._parse_duration_string(time_match.group(1))
        
        video['duration'] = duration_minutes
        video['source'] = self.source_name
        return video
