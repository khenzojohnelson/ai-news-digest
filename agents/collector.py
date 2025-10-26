import feedparser
import requests
import os
from datetime import datetime, timedelta

class CollectorAgent:
    def __init__(self):
        self.newsapi_key = os.environ.get('NEWSAPI_KEY')
        
        self.rss_feeds_id = [
            'https://www.kompas.com/rss',
            'https://www.tempo.co/rss/terbaru',
        ]
        
        self.rss_feeds_intl = [
            'http://feeds.bbci.co.uk/news/rss.xml',
            'https://feeds.reuters.com/reuters/topNews',
        ]
    
    def collect(self):
        print("📥 Mengumpulkan berita...")
        
        all_news = {
            'nasional': [],
            'internasional': []
        }
        
        for feed_url in self.rss_feeds_id:
            news = self._fetch_rss(feed_url)
            all_news['nasional'].extend(news)
        
        for feed_url in self.rss_feeds_intl:
            news = self._fetch_rss(feed_url)
            all_news['internasional'].extend(news)
        
        if self.newsapi_key:
            newsapi_data = self._fetch_newsapi()
            all_news['internasional'].extend(newsapi_data)
        
        all_news['nasional'] = sorted(
            all_news['nasional'], 
            key=lambda x: x.get('published', ''), 
            reverse=True
        )[:10]
        
        all_news['internasional'] = sorted(
            all_news['internasional'], 
            key=lambda x: x.get('published', ''), 
            reverse=True
        )[:20]
        
        print(f"✅ Terkumpul: {len(all_news['nasional'])} nasional, {len(all_news['internasional'])} internasional")
        
        return all_news
    
    def _fetch_rss(self, feed_url):
        try:
            feed = feedparser.parse(feed_url)
            news_list = []
            
            for entry in feed.entries[:10]:
                news_list.append({
                    'title': entry.get('title', 'No title'),
                    'url': entry.get('link', ''),
                    'source': feed.feed.get('title', 'Unknown'),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', '')[:300]
                })
            
            return news_list
        
        except Exception as e:
            print(f"❌ Error fetching RSS {feed_url}: {e}")
            return []
    
    def _fetch_newsapi(self):
        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            url = f"https://newsapi.org/v2/everything"
            params = {
                'apiKey': self.newsapi_key,
                'q': 'politics OR economy OR technology',
                'language': 'en',
                'from': yesterday,
                'sortBy': 'popularity',
                'pageSize': 10
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            news_list = []
            for article in data.get('articles', []):
                news_list.append({
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', 'NewsAPI'),
                    'published': article.get('publishedAt', ''),
                    'summary': article.get('description', '')[:300]
                })
            
            return news_list
        
        except Exception as e:
            print(f"❌ Error fetching NewsAPI: {e}")
            return []