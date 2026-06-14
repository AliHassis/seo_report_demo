# 🚀 Smart SEO Analyzer — محلل SEO الذكي

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-Private-red?style=for-the-badge)

**Bilingual (Arabic / English) SEO analysis tool with real-time website scanning.**

**أداة تحليل SEO ثنائية اللغة (عربي / إنجليزي) مع فحص حقيقي للمواقع.**

</div>

---

## 🇬🇧 English

### Features
- **Real Analysis** — scans any website using `requests` + `BeautifulSoup`, no external API needed
- **17+ SEO Criteria** — title, meta description, headings, images, links, speed, mobile, HTTPS, SSL, Schema, Open Graph, and more
- **Bilingual UI** — seamless Arabic ↔ English switching with RTL/LTR support
- **Compare Mode** — side-by-side SEO comparison of two websites
- **Interactive Charts** — radar and bar charts powered by Plotly
- **Export Reports** — Excel, PDF (HTML), CSV, and JSON — all in the selected language
- **Analysis History** — recent analyses stored in session

### Project Structure
```
seo_report_pro/
├── app.py              # Main UI (Streamlit sidebar, tabs, layout)
├── translations.py     # Complete AR/EN translation dictionary
├── analyzer.py         # SEO analysis logic & scoring
├── network_checks.py   # HTTP requests, SSL, robots, sitemap checks
├── charts.py           # Plotly radar & bar charts
├── exports.py          # Excel, PDF, CSV, JSON report builders
├── styles.py           # Dynamic CSS (RTL/LTR + fonts)
├── requirements.txt
├── .streamlit/config.toml
├── run.bat             # Windows quick launcher
└── README.md
```

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Deployment on Streamlit Cloud
1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select the repo and set `app.py` as the main file
4. Deploy — no API keys or secrets needed

---

## 🇸🇦 العربية

### المميزات
- **تحليل حقيقي** — يفحص أي موقع باستخدام `requests` + `BeautifulSoup`، بدون API خارجي
- **17+ معيار SEO** — العنوان، الوصف، العناوين، الصور، الروابط، السرعة، الجوال، HTTPS، SSL، Schema، Open Graph، والمزيد
- **واجهة ثنائية اللغة** — تبديل سلس بين العربية والإنجليزية مع دعم RTL/LTR
- **وضع المقارنة** — مقارنة SEO بين موقعين جنباً إلى جنب
- **رسوم بيانية تفاعلية** — مخططات رادار وأعمدة بواسطة Plotly
- **تصدير التقارير** — Excel، PDF (HTML)، CSV، و JSON — الكل باللغة المختارة
- **سجل التحليلات** — آخر التحليلات محفوظة في الجلسة

### التشغيل السريع
```bash
# تثبيت المكتبات
pip install -r requirements.txt

# تشغيل التطبيق
streamlit run app.py

# أو على Windows:
run.bat
```

### النشر على Streamlit Cloud
1. ارفع المشروع على GitHub
2. اذهب إلى [share.streamlit.io](https://share.streamlit.io)
3. اختر المستودع وحدد `app.py` كملف رئيسي
4. انشر — لا يحتاج مفاتيح API أو إعدادات سرية

---

*Built by Ali Alhassis — علي الهصيص*
