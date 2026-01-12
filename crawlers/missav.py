import re
import logging
from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

class MissavCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(base_url="https://missav.ai")
        self.source_name = "MissAV"
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
            
            # Fallback title extraction
            video['title'] = link_tag.get('title') or ""
            if not video['title']:
                title_tag = card.find(['h3', 'h4', 'p'])
                if title_tag:
                    video['title'] = title_tag.get_text(strip=True)
                else:
                    img_tag = card.find('img')
                    if img_tag:
                        video['title'] = img_tag.get('alt') or ""
            
            video['title'] = video['title'].strip()
            
        code_match = self.CODE_PATTERN.search(video.get('title', ''))
        if not code_match and 'detail_url' in video:
            code_match = self.CODE_PATTERN.search(video['detail_url'])
        
        if code_match:
            video['code'] = code_match.group(1).upper()
        
        img_tag = card.find('img')
        if img_tag:
            video['cover_url'] = img_tag.get('data-src') or img_tag.get('src')
            
        video['source'] = self.source_name
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
        if title_el: 
            video['title'] = title_el.get_text(strip=True)
        else:
            logger.warning("Could not find <h1> title on page: %s", url)
            # Try a fallback for title
            og_title = soup.find('meta', property='og:title')
            if og_title:
                video['title'] = og_title.get('content')
        
        code_match = self.CODE_PATTERN.search(video.get('title', ''))
        video['code'] = code_match.group(1).upper() if code_match else None
        
        actress_tags = soup.select('a[href*="/actresses/"]')
        actresses = [a.get_text(strip=True) for a in actress_tags if "女优排行" not in a.get_text()]
        video['actresses'] = ", ".join(actresses)
        
        tag_tags = soup.select('a[href*="/genres/"]')
        video['tags'] = ", ".join([t.get_text(strip=True) for t in tag_tags])
        
        # Enhanced duration extraction for MissAV
        duration_minutes = None
        
        # Priority 1: Meta tags (MissAV often uses seconds in og:video:duration)
        meta_duration = soup.find('meta', attrs={'property': 'og:video:duration'}) or \
                        soup.find('meta', attrs={'itemprop': 'duration'})
        if meta_duration:
            content = meta_duration.get('content', '')
            num_match = re.search(r'(\d+)', content)
            if num_match:
                seconds = int(num_match.group(1))
                # MissAV duration in meta is usually seconds
                if seconds > 500: # Highly likely to be seconds
                    duration_minutes = seconds // 60
                else:
                    duration_minutes = seconds
        
        # Priority 2: Try finding in the text directly (e.g., "120 分" or "120 min")
        if not duration_minutes:
            duration_match = re.search(r'(\d+)\s*(分|min)', html)
            if duration_match:
                duration_minutes = int(duration_match.group(1))
            else:
                # Fallback: Look for span with specific patterns
                span_match = soup.find('span', string=re.compile(r'\d+\s*(分|min)'))
                if span_match:
                    duration_res = re.search(r'(\d+)', span_match.get_text())
                    if duration_res:
                        duration_minutes = int(duration_res.group(1))

        video['duration'] = duration_minutes
        
        video_tag = soup.find('video')
        if video_tag:
            video['preview_url'] = video_tag.get('src') or video_tag.get('data-src')
            
        video['source'] = self.source_name
        return video
