import asyncio
import httpx
from bs4 import BeautifulSoup
import re
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class MissavCrawler:
    BASE_URL = "https://missav.ai"
    NEW_VIDEOS_URL = f"{BASE_URL}/new"
    
    CODE_PATTERN = re.compile(r'([A-Z]+-\d+)', re.IGNORECASE)
    
    def __init__(self, user_agent=None):
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.client = httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
            timeout=30.0
        )
        self.cookies = {}

    async def init_session(self):
        """Warm up session to handle anti-bot"""
        try:
            for _ in range(2):
                response = await self.client.get(f"{self.NEW_VIDEOS_URL}?page=2")
                self.cookies.update(response.cookies)
                await asyncio.sleep(random.uniform(1, 2))
            logger.info("Session initialized with cookies: %s", self.cookies)
        except Exception as e:
            logger.warning("Failed to initialize session: %s", e)

    async def fetch_html(self, url):
        await asyncio.sleep(random.uniform(1, 3))
        try:
            response = await self.client.get(url, cookies=self.cookies)
            if response.status_code == 200:
                return response.text
            logger.warn("Fetch failed: %s status %d", url, response.status_code)
        except Exception as e:
            logger.error("Error fetching %s: %s", url, e)
        return None

    def parse_video_card(self, card):
        video = {}
        # Detail link
        link_tag = card.find('a', href=True)
        if link_tag:
            href = link_tag['href']
            video['detail_url'] = href if href.startswith('http') else f"{self.BASE_URL}{href}"
            
        # Title
        title_tag = card.find(['h3', 'h4', 'p'])
        if title_tag:
            video['title'] = title_tag.get_text(strip=True)
            
        # Extract code (番号)
        code_match = self.CODE_PATTERN.search(video.get('title', ''))
        if not code_match and 'detail_url' in video:
            code_match = self.CODE_PATTERN.search(video['detail_url'])
        
        if code_match:
            video['code'] = code_match.group(1).upper()
        else:
            # Fallback for code extraction from URL
            if 'detail_url' in video:
                parts = video['detail_url'].split('/')
                last_part = parts[-1] if parts[-1] else parts[-2]
                video['code'] = last_part.upper()

        # Cover image
        img_tag = card.find('img')
        if img_tag:
            video['cover_url'] = img_tag.get('data-src') or img_tag.get('src')
            
        return video

    async def crawl_new_videos(self, pages=1):
        all_videos = []
        for page in range(1, pages + 1):
            url = f"{self.NEW_VIDEOS_URL}?page={page}" if page > 1 else self.NEW_VIDEOS_URL
            html = await self.fetch_html(url)
            if not html:
                continue
                
            soup = BeautifulSoup(html, 'html.parser')
            # Look for video cards (the markers might vary, adjusting based on Java logic)
            cards = soup.select('div.group') or soup.select('div.video-card')
            
            page_videos = []
            for card in cards:
                video = self.parse_video_card(card)
                if video.get('code'):
                    page_videos.append(video)
            
            all_videos.extend(page_videos)
            logger.info("Crawled page %d, found %d videos", page, len(page_videos))
            
        return all_videos

    async def crawl_video_detail(self, url):
        html = await self.fetch_html(url)
        if not html: return None
        
        soup = BeautifulSoup(html, 'html.parser')
        video = {'detail_url': url}
        
        # Title
        title_el = soup.find('h1')
        if title_el: video['title'] = title_el.get_text(strip=True)
        
        # Code
        video['code'] = self.CODE_PATTERN.search(video.get('title', '')).group(1).upper() if self.CODE_PATTERN.search(video.get('title', '')) else None
        
        # Actresses
        actress_tags = soup.select('a[href*="/actresses/"]')
        video['actresses'] = ", ".join([a.get_text(strip=True) for a in actress_tags])
        
        # Tags
        tag_tags = soup.select('a[href*="/genres/"]')
        video['tags'] = ", ".join([t.get_text(strip=True) for t in tag_tags])
        
        # Duration
        match = re.search(r'(\d+)\s*分', html)
        video['duration'] = int(match.group(1)) if match else None
        
        # Preview
        video_tag = soup.find('video')
        if video_tag:
            video['preview_url'] = video_tag.get('src') or video_tag.get('data-src')
            
        return video

    async def close(self):
        await self.client.aclose()
