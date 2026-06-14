import io
import json
import pandas as pd
from datetime import datetime
from translations import t

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


def build_excel_report(domain, score, label, results, ssl_info, robots_info, sitemap_info, all_checks, keywords=None, lang="ar") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df = pd.DataFrame([{
            t("excel_site", lang): domain,
            t("excel_score", lang): score,
            t("excel_rating", lang): label,
            t("excel_date", lang): datetime.now().strftime("%Y-%m-%d %H:%M"),
            t("excel_load_time", lang): results.get("load_time", {}).get("value", ""),
            t("excel_page_size", lang): results.get("page_size", {}).get("kb", ""),
            t("excel_ssl_status", lang): t("excel_ssl_valid", lang) if ssl_info.get("valid") else "❌",
            t("excel_robots_status", lang): "✅" if robots_info.get("exists") else "⚠️",
            t("excel_sitemap_status", lang): "✅" if sitemap_info.get("exists") else "⚠️",
        }])
        summary_df.to_excel(writer, sheet_name=t("excel_sheet_summary", lang), index=False)

        emojis = {"good": "✅", "warning": "⚠️", "bad": "❌"}
        details = [{
            t("col_element", lang): n,
            t("col_status", lang): emojis.get(s, "❓"),
            t("col_recommendation", lang): r,
        } for n, s, r in all_checks]
        pd.DataFrame(details).to_excel(writer, sheet_name=t("excel_sheet_details", lang), index=False)

        if keywords:
            kw_df = pd.DataFrame(keywords, columns=[t("excel_keyword", lang), t("excel_frequency", lang)])
            kw_df.to_excel(writer, sheet_name=t("excel_sheet_keywords", lang), index=False)
    return output.getvalue()


def generate_pdf_html(domain, score, label, score_color, results, all_checks, ssl_info, robots_info, sitemap_info, readability, keywords, lang="ar"):
    is_rtl = lang == "ar"
    direction = "rtl" if is_rtl else "ltr"
    html_lang = "ar" if is_rtl else "en"
    font_family = "Cairo" if is_rtl else "Inter"
    text_align = "right" if is_rtl else "left"

    emojis = {"good": "✅", "warning": "⚠️", "bad": "❌"}
    checks_html = ""
    for name, status, rec in all_checks:
        bg = "#dcfce7" if status == "good" else "#fef9c3" if status == "warning" else "#fee2e2"
        checks_html += f'<tr><td>{name}</td><td style="text-align:center">{emojis.get(status, "❓")}</td><td style="font-size:12px">{rec}</td></tr>'

    kw_html = ""
    if keywords:
        for word, count in keywords[:15]:
            kw_html += f"<tr><td>{word}</td><td style='text-align:center'>{count}</td></tr>"

    load_time_val = results.get("load_time", {}).get("value", "")
    page_size_val = results.get("page_size", {}).get("kb", "")
    content_words = results.get("content", {}).get("words", "")
    read_score = readability.get("score", "")
    time_suffix = t("time_suffix", lang)

    kw_section = ""
    if kw_html:
        kw_title = t("pdf_keywords_title", lang)
        kw_col1 = t("excel_keyword", lang)
        kw_col2 = t("excel_frequency", lang)
        kw_section = f"<h2>{kw_title}</h2><table><tr><th>{kw_col1}</th><th>{kw_col2}</th></tr>{kw_html}</table>"

    return f"""<!DOCTYPE html><html dir="{direction}" lang="{html_lang}"><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
<title>{t("pdf_report_title", lang)} - {domain}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'{font_family}',sans-serif;background:#fff;color:#1a202c;direction:{direction};font-size:13px;padding:24px}}
.header{{background:linear-gradient(135deg,#060d1a,#0d1d32);color:#fff;padding:24px 28px;border-radius:12px;margin-bottom:20px;display:flex;align-items:center;gap:20px}}
.big-score{{width:80px;height:80px;border-radius:50%;border:4px solid {score_color};display:flex;flex-direction:column;align-items:center;justify-content:center;flex-shrink:0}}
.big-score .n{{font-size:24px;font-weight:900;color:{score_color}}}
.big-score .l{{font-size:9px;color:#94a3b8}}
table{{width:100%;border-collapse:collapse;margin:12px 0}}
th,td{{padding:8px 12px;text-align:{text_align};border:1px solid #e2e8f0}}
th{{background:#f1f5f9;font-weight:700;font-size:12px}}
h2{{font-size:16px;margin:18px 0 8px;color:#0d1d32}}
.info-row{{display:flex;gap:12px;margin:8px 0;flex-wrap:wrap}}
.info-box{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 16px;flex:1;text-align:center;min-width:100px}}
.info-box .val{{font-size:18px;font-weight:900}}
.info-box .lbl{{font-size:11px;color:#64748b}}
.footer{{text-align:center;color:#94a3b8;font-size:11px;margin-top:20px;padding-top:12px;border-top:1px solid #e2e8f0}}
@media print{{body{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
</style></head><body>
<div class="header">
  <div class="big-score"><div class="n">{score}</div><div class="l">/ 100</div></div>
  <div><h1 style="font-size:22px;font-weight:900">{t("pdf_report_title", lang)}</h1>
  <p style="color:#94a3b8;font-size:13px">{domain}</p>
  <p style="color:#64748b;font-size:11px">{datetime.now().strftime("%Y-%m-%d %H:%M")} | {label}</p></div>
</div>

<div class="info-row">
  <div class="info-box"><div class="val" style="color:{score_color}">{score}%</div><div class="lbl">{t("pdf_score_label", lang)}</div></div>
  <div class="info-box"><div class="val">{load_time_val}{time_suffix}</div><div class="lbl">{t("pdf_speed_label", lang)}</div></div>
  <div class="info-box"><div class="val">{page_size_val} KB</div><div class="lbl">{t("pdf_size_label", lang)}</div></div>
  <div class="info-box"><div class="val">{content_words}</div><div class="lbl">{t("pdf_words_label", lang)}</div></div>
  <div class="info-box"><div class="val">{read_score}%</div><div class="lbl">{t("pdf_readability_label", lang)}</div></div>
</div>

<h2>{t("pdf_details_title", lang, count=len(all_checks))}</h2>
<table><tr><th>{t("col_element", lang)}</th><th>{t("col_status", lang)}</th><th>{t("col_recommendation", lang)}</th></tr>{checks_html}</table>

{kw_section}

<div class="footer">{t("pdf_footer", lang, domain=domain)}</div>
</body></html>"""


def build_json_report(url, domain, score, label, load_time, readability, keywords, broken_links, all_checks, ssl_info, robots_info, sitemap_info, lang="ar"):
    return {
        "url": url, "domain": domain, "score": score, "label": label,
        "analyzed_at": datetime.now().isoformat(), "load_time": load_time,
        "readability": readability, "keywords": keywords[:10] if keywords else [],
        "broken_links": broken_links,
        "checks": {n: {"status": s, "recommendation": r} for n, s, r in all_checks},
        "ssl": ssl_info, "robots": robots_info, "sitemap": sitemap_info,
    }


def build_csv(all_checks, lang="ar"):
    emojis = {"good": "✅", "warning": "⚠️", "bad": "❌"}
    report_data = [{
        t("col_element", lang): name,
        t("col_status", lang): emojis.get(status, "❓"),
        t("col_recommendation", lang): rec,
    } for name, status, rec in all_checks]
    df = pd.DataFrame(report_data)
    return df, df.to_csv(index=False, encoding="utf-8-sig")
