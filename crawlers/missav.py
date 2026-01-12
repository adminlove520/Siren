import re
import logging
from bs4 import BeautifulSoup
from .base import BaseCrawler

logger = logging.getLogger(__name__)

class MissavCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(base_url="https://missav.ai")
        self.CODE_PATTERN = re.compile(r'([A-Z]+-\d+)', re.IGNORECASE)

    async def crawl_new_videos(self, pages=1):
        all_videos = []
        new_url = f"{self.base_url}/new"
        for page in range(1, pages + 1):
            url = f"{new_url}?page={page}" if page > 1 else new_url
            html = await self.fetch_html(url)
            if not html: continue
            
            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.select('div.group') or soup.select('div.video-card')
            
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
            
        title_tag = card.find(['h3', 'h4', 'p'])
        if title_tag:
            video['title'] = title_tag.get_text(strip=True)
            
        code_match = self.CODE_PATTERN.search(video.get('title', ''))
        if not code_match and 'detail_url' in video:
            code_match = self.CODE_PATTERN.search(video['detail_url'])
        
        if code_match:
            video['code'] = code_match.group(1).upper()
        
        img_tag = card.find('img')
        if img_tag:
            video['cover_url'] = img_tag.get('data-src') or img_tag.get('src')
            
        return video

    async def search(self, keyword, limit=5):
        # MissAV search URL: https://missav.ai/cn/search/keyword
        url = f"{self.base_url}/cn/search/{keyword}"
        html = await self.fetch_html(url)
        if not html: return []
        
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('div.group') or soup.select('div.video-card')
        
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
        
        title_el = soup.find('h1')
        if title_el: video['title'] = title_el.get_text(strip=True)
        
        code_match = self.CODE_PATTERN.search(video.get('title', ''))
        video['code'] = code_match.group(1).upper() if code_match else None
        
        actress_tags = soup.select('a[href*="/actresses/"]')
        video['actresses'] = ", ".join([a.get_text(strip=True) for a in actress_tags])
        
        tag_tags = soup.select('a[href*="/genres/"]')
        video['tags'] = ", ".join([t.get_text(strip=True) for t in tag_tags])
        
        duration_match = re.search(r'(\d+)\s*分', html)
        video['duration'] = int(duration_match.group(1)) if duration_match else None
        
        video_tag = soup.find('video')
        if video_tag:
            video['preview_url'] = video_tag.get('src') or video_tag.get('data-src')
            
        return video
