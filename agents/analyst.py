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
        self.model = "openai/gpt-oss-120b"

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
        prompt = f"""
You are a **multidisciplinary professor and reflective essayist** with deep expertise in social sciences, politics, economics, modern philosophy, and psychology.

Your task is to write a **reflective analytical essay in English (IELTS level 7.0–8.0)** based on the following news article.

The essay must:
- Use **a narrative-argumentative style**, similar to **George Orwell, Yuval Noah Harari, or Zadie Smith**.
- Be written in **natural, thoughtful, and literary English** (not robotic or mechanical).
- Contain a clear flow of reasoning — observation → interpretation → reflection.
- Integrate **3-4 relevant theoretical perspectives** (e.g., political economy, social psychology, media theory, etc.) — but do it organically within the prose.
- Maintain a balance between **fact and interpretation** — analytical yet humane.
- Avoid using bullet points or sections; make it **a single coherent essay**.
- Length: **500–1500 words**, depending on the significance of the news.

---

### 📰 NEWS DATA
**Title:** {news['title']}
**Source:** {news['source']}
**URL:** {news['url']}
**Summary:** {news['summary']}

---

### WRITING INSTRUCTIONS
1. Begin with an engaging opening that captures the essence or irony of the event.
2. Gradually expand to deeper layers — historical, psychological, or ideological.
3. Weave in theoretical insights subtly (e.g., “As Gramsci might argue…” or “In the spirit of Weber’s rationalization…”).
4. End with a reflective tone — what does this event say about our society, power, or human nature?
5. The essay should feel **like a conversation with an intelligent, curious reader**, not a lecture.

---
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2500,
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
