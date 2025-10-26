from datetime import datetime, timedelta

class VerifierAgent:
    def __init__(self):
        self.trusted_sources = [
            'Kompas.com', 'TEMPO.CO', 'detikcom',
            'BBC News', 'Reuters', 'Associated Press', 'The Guardian'
        ]
    
    def verify(self, news_data):
        print("✅ Memverifikasi berita...")
        
        verified = {
            'nasional': self._filter_news(news_data['nasional']),
            'internasional': self._filter_news(news_data['internasional'])
        }
        
        print(f"✅ Setelah filter: {len(verified['nasional'])} nasional, {len(verified['internasional'])} internasional")
        
        return verified
    
    def _filter_news(self, news_list):
        filtered = []
        
        for news in news_list:
            source_ok = any(trusted in news.get('source', '') for trusted in self.trusted_sources)
            is_recent = self._check_recency(news.get('published', ''))
            has_content = news.get('title') and news.get('url')
            
            if source_ok and is_recent and has_content:
                news['credibility_score'] = 8.5
                filtered.append(news)
        
        return filtered
    
    def _check_recency(self, published_date):
        if not published_date:
            return False
        
        try:
            for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S%z']:
                try:
                    pub_date = datetime.strptime(published_date.split('+')[0].strip(), fmt.split('%z')[0].strip())
                    age = datetime.now() - pub_date.replace(tzinfo=None)
                    return age.days <= 2
                except:
                    continue
            return True
        except:
            return True