import re
import logging
from bs4 import BeautifulSoup
from .base import BaseCrawler

logger = logging.getLogger(__name__)

class JableCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(base_url="https://jable.tv")
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
            
        return video

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
            
        return video
