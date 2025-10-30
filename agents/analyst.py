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
Anda adalah seorang **Profesor multidisipliner tingkat lanjut** dengan keahlian mendalam di bidang ilmu sosial, politik, ekonomi, filsafat, dan psikologi modern.
Tugas Anda adalah melakukan **analisis reflektif dan teoritis mendalam terhadap berita berikut**, dengan gaya penulisan yang menarik, bernuansa akademis, namun tetap komunikatif dan alami dalam bahasa Indonesia, dan jika ada istilah asing untuk suatu konsep, maka sangat disarankan untuk menggunakan bahasa asing tersebut (agar nuansa tepat) 

Gunakan struktur markdown dengan heading dan emoji untuk membuat hasil mudah dibaca.

---

### 📰 **DATA BERITA**
**Judul:** {news['title']}
**Sumber:** [{news['source']}]({news['url']})
**Ringkasan Singkat:** {news['summary']}

---

## 🧩 **Analisis Terstruktur (5W+1H)**
Jelaskan dengan detail dan reflektif:
- **What:** Apa inti peristiwa atau isu utama?
- **Who:** Siapa aktor atau institusi kunci yang terlibat, dan apa kepentingannya?
- **When:** Kapan peristiwa terjadi dan bagaimana konteks waktu mempengaruhinya?
- **Where:** Di mana terjadi, dan adakah signifikansi geopolitik atau sosial di balik lokasi tersebut?
- **Why:** Mengapa hal ini bisa terjadi, apa faktor penyebab mendalam (struktural, historis, ideologis)?
- **How:** Bagaimana prosesnya berlangsung, siapa memengaruhi siapa, dan bagaimana narasi dibentuk?

---

## 🧠 **Konteks, Teori, dan Penjelasan Istilah**
- Jika terdapat istilah, organisasi, kebijakan, atau nama tokoh, jelaskan secara singkat konteksnya (asal-usul, tujuan, atau perannya dalam isu ini).
- Kaitkan peristiwa dengan **berbagai teori sosial, politik, ekonomi, atau psikologi relevan**. 
  Misalnya teori hegemoni (Gramsci), framing media (Entman), perilaku kolektif (Durkheim), atau rasionalitas terbatas (Herbert Simon).
- Gunakan minimal **2-3 teori atau pendekatan** lintas disiplin untuk memperkaya analisis.
- Sertakan kutipan atau referensi konseptual (mis. *“menurut Pierre Bourdieu dalam Distinction (1979)…”* atau *“sesuai teori agenda-setting McCombs & Shaw (1972)”*).

---

## 🔍 **Analisis Mendalam Proses demi Proses**
Uraikan **alur sebab-akibat dan dinamika kekuasaan** yang muncul:
1. Identifikasi akar masalah.
2. Jelaskan proses berkembangnya isu.
3. Tunjukkan bagaimana faktor sosial, ekonomi, politik, dan psikologis saling mempengaruhi.
4. Analisis persepsi publik, framing media, serta narasi kekuasaan yang membentuk opini.
5. Sajikan **pandangan baru atau insight unik** yang jarang dibahas di media umum.

---

## ⚖️ **Pertimbangan Kritis & Multi-Perspektif**
- **Bias:** Apa potensi bias dari sumber berita atau framing narasi?
- **Dampak:** Siapa yang diuntungkan atau dirugikan (secara ekonomi, politik, sosial)?
- **Perspektif Alternatif:** Sajikan sudut pandang lain (mis. dari aktor, akademisi, atau rakyat biasa).
- **Nilai Etis:** Apakah ada dilema moral, hak asasi, atau nilai kemanusiaan yang terlibat?

---

## 💡 **Refleksi & Pembelajaran Pribadi**
Tuliskan 2–3 paragraf reflektif:
- Apa pesan moral dan nilai yang bisa dipetik dari isu ini?
- Bagaimana peristiwa ini bisa menginspirasi kita untuk berpikir lebih kritis, empatik, atau bertindak lebih bijak?
- Apa yang bisa dipelajari untuk pengembangan diri atau cara memandang masyarakat secara lebih luas?

---

## 🧭 **Rangkuman Akhir**
Berikan penutup yang merangkum:
- Inti berita dan implikasinya.
- Teori dan konsep kunci yang digunakan dalam analisis.
- Kesimpulan umum dari analisis mendalam.
- Nilai moral dan pembelajaran utama bagi pembaca.

---

**Gaya penulisan:**
- Bahasa Indonesia yang **natural, reflektif, cerdas, dan engaging.**
- dan jika ada istilah asing untuk suatu konsep, maka sangat disarankan untuk menggunakan bahasa asing tersebut (agar nuansa tepat)  
- Gunakan emoji di setiap bagian untuk menambah daya tarik visual.
- Panjang total **500 sampai 1500 kata tergantung seberapa penting berita ini**. 
- Hindari repetisi dan buat pembaca merasa mendapatkan “pandangan baru”.

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
