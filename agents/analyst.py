import os
from datetime import datetime
import httpx
from groq import Groq


class AnalystAgent:
    def __init__(self):
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY tidak ditemukan!")

        # ✅ Gunakan httpx.Client() manual tanpa proxies
        self.http_client = httpx.Client(timeout=60.0)
        self.client = Groq(api_key=api_key, http_client=self.http_client)
        self.model = "groq/compound"

        # (opsional, buat debugging)
        try:
            import groq
            print(f"🧩 Groq SDK version aktif: {groq.__version__}")
        except Exception:
            pass

    def analyze(self, verified_news):
        print("🧠 Menganalisis berita...")

        selected = self._select_top_news(verified_news)
        analyses = []

        for i, news in enumerate(selected, 1):
            category = "NASIONAL" if i == 1 else f"INTERNASIONAL #{i-1}"
            print(f"  Menganalisis berita {i}/3...")

            analysis = self._generate_analysis(news, category)
            analyses.append(analysis)

        final_message = self._format_message(analyses)

        print("✅ Analisis selesai!")
        return final_message

    def _select_top_news(self, verified_news):
        selected = []

        if verified_news.get('nasional'):
            selected.append(verified_news['nasional'][0])

        selected.extend(verified_news.get('internasional', [])[:2])

        return selected

    def _generate_analysis(self, news, category):
        prompt = f"""Kamu adalah analis berita yang sangat cerdas dan reflektif. Analisis berita ini dengan struktur berikut:

BERITA:
Judul: {news['title']}
Sumber: {news['source']}
Ringkasan: {news['summary']}

TUGAS:
Buat analisis dalam format markdown. Gunakan emoji untuk readability.

STRUKTUR (Setiap poin-poin diberikan analisis jelas dan detail agar berita tidak membosankan)

📰 **{news['title']}**
🔗 [{news['source']}]({news['url']})

🧩 **Analisis 5W+1H:**
- **What:** [Apa yang terjadi?]
- **Who:** [Siapa yang terlibat?]
- **When:** [Kapan kejadiannya?]
- **Where:** [Di mana lokasinya?]
- **Why:** [Mengapa hal ini terjadi?]
- **How:** [Bagaimana prosesnya?]

🧠 **Konteks & Teori:**
[Kaitkan dengan teori ekonomi/politik/psikologi yang relevan. Jelaskan dalam 2-3 kalimat.]

💡 **Insight & Refleksi:**
[Apa pembelajaran personal yang bisa diambil? Bagaimana relevansinya dengan kehidupan sehari-hari? 2-3 kalimat.]

⚖️ **Pertimbangan Kritis:**
- **Bias:** [Potensi bias dari sumber?]
- **Dampak:** [Siapa yang diuntungkan/dirugikan?]
- **Perspektif Alternatif:** [Sudut pandang lain yang mungkin?]

PENTING:
- Gunakan bahasa Indonesia yang natural dan engaging
- Total panjang: 250-400 kata
- Fokus pada insight, bukan hanya ringkasan
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500,
            )

            # Groq SDK kadang pakai format message atau content berbeda
            message = response.choices[0].message
            analysis = getattr(message, "content", str(message))

            return f"{'🇮🇩' if 'NASIONAL' in category else '🌍'} **BERITA {category}**\n\n{analysis}"

        except Exception as e:
            print(f"❌ Error analisis: {e}")
            return f"❌ Gagal menganalisis berita: {news.get('title', 'Tidak diketahui')}"

    def _format_message(self, analyses):
        header = f"""🗞️ **AI Daily Digest — {datetime.now().strftime('%A, %d %B %Y')}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        separator = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        footer = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 *Powered by AI Multi-Agent System | Generated at {datetime.now().strftime('%H:%M WIB')}*
"""

        body = separator.join(analyses)

        return header + body + footer
