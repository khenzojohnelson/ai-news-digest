import requests
import os
from datetime import datetime

class MessengerAgent:
    def __init__(self):
        self.webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
        
        if not self.webhook_url:
            raise ValueError("❌ DISCORD_WEBHOOK_URL tidak ditemukan!")
    
    def send_link(self, doc_url, date=None):
        if date is None:
            date = datetime.now()
        
        message = f"""
🗞️ **AI Daily News Digest - {date.strftime('%A, %d %B %Y')}**

📄 **Berita hari ini sudah siap!**

Klik link di bawah untuk membaca analisis lengkap:
👉 {doc_url}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 **Arsip:** Semua berita tersimpan rapi di Google Drive
🤖 **Powered by:** AI Multi-Agent System
⏰ **Generated at:** {datetime.now().strftime('%H:%M WIB')}
"""
        
        try:
            payload = {"content": message.strip()}
            response = requests.post(self.webhook_url, json=payload)
            
            if response.status_code == 204:
                print(f"✅ Link terkirim ke Discord")
                return True
            else:
                print(f"❌ Gagal kirim: {response.status_code}")
                print(response.text)
                return False
        
        except Exception as e:
            print(f"❌ Error saat kirim pesan: {e}")
            return False