import os
import sys
from datetime import datetime

from agents.collector import CollectorAgent
from agents.verifier import VerifierAgent
from agents.analyst import AnalystAgent
from agents.google_docs import GoogleDocsAgent
from agents.messenger import MessengerAgent

def main():
    print("=" * 60)
    print("🚀 AI NEWS DIGEST SYSTEM (Google Docs Edition)")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        print("\n[1/5] 📥 COLLECTING NEWS...")
        collector = CollectorAgent()
        raw_news = collector.collect()
        
        if not raw_news['nasional'] and not raw_news['internasional']:
            print("❌ Tidak ada berita yang terkumpul!")
            sys.exit(1)
        
        print("\n[2/5] ✅ VERIFYING NEWS...")
        verifier = VerifierAgent()
        verified_news = verifier.verify(raw_news)
        
        if not verified_news['nasional'] and not verified_news['internasional']:
            print("❌ Tidak ada berita yang lolos verifikasi!")
            sys.exit(1)
        
        print("\n[3/5] 🧠 ANALYZING NEWS...")
        analyst = AnalystAgent()
        final_content = analyst.analyze(verified_news)
        
        print("\n[4/5] 📄 CREATING GOOGLE DOC...")
        google_docs = GoogleDocsAgent()
        doc_url = google_docs.create_and_save(final_content)
        
        if not doc_url:
            print("❌ Gagal membuat Google Doc!")
            sys.exit(1)
        
        print("\n[5/5] 📤 SENDING LINK TO DISCORD...")
        messenger = MessengerAgent()
        messenger.send_link(doc_url)
        
        print("\n" + "=" * 60)
        print("🎉 PROCESS COMPLETED SUCCESSFULLY!")
        print(f"📄 Google Doc: {doc_url}")
        print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()