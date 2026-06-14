import streamlit as st
import json
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from translations import t
from styles import get_css
from network_checks import normalize_url, fetch_page, check_ssl, check_robots, check_sitemap, check_broken_links
from analyzer import analyze_page, calculate_score, extract_keywords, calculate_readability, extract_og_data, render_badge
from charts import create_radar_chart, create_scores_bar, create_comparison_radar, PLOTLY_AVAILABLE
from exports import build_excel_report, build_json_report, build_csv, generate_pdf_html, EXCEL_AVAILABLE

st.set_page_config(page_title="SEO Pro Analyzer", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

if "lang" not in st.session_state:
    st.session_state.lang = "ar"
if "history" not in st.session_state:
    st.session_state.history = []

lang = st.session_state.lang
st.markdown(get_css(lang), unsafe_allow_html=True)


def save_to_history(domain, score, label, url):
    entry = {"domain": domain, "score": score, "label": label, "url": url, "time": datetime.now().strftime("%H:%M - %Y/%m/%d")}
    st.session_state.history.insert(0, entry)
    if len(st.session_state.history) > 15:
        st.session_state.history = st.session_state.history[:15]


def build_all_checks(results, ssl_info, robots_info, sitemap_info, check_ssl_opt, check_robots_opt, check_sitemap_opt):
    checks = [
        (t("check_page_title", lang),    results["title"]["status"],       results["title"]["recommendation"]),
        (t("check_meta_desc", lang),     results["description"]["status"], results["description"]["recommendation"]),
        (t("check_headings", lang),      results["headings"]["status"],    results["headings"]["recommendation"]),
        (t("check_images_alt", lang),    results["images"]["status"],      results["images"]["recommendation"]),
        (t("check_internal_links", lang), results["links"]["status"],      results["links"]["recommendation"]),
        (t("check_load_time", lang),     results["load_time"]["status"],   results["load_time"]["recommendation"]),
        (t("check_mobile", lang),        results["mobile"]["status"],      results["mobile"]["recommendation"]),
        (t("check_https", lang),         results["https"]["status"],       results["https"]["recommendation"]),
        (t("check_canonical", lang),     results["canonical"]["status"],   results["canonical"]["recommendation"]),
        (t("check_og", lang),            results["opengraph"]["status"],   results["opengraph"]["recommendation"]),
        (t("check_schema", lang),        results["schema"]["status"],      results["schema"]["recommendation"]),
        (t("check_page_size", lang),     results["page_size"]["status"],   results["page_size"]["recommendation"]),
        (t("check_content_size", lang),  results["content"]["status"],     results["content"]["recommendation"]),
        (t("check_language", lang),      results["language"]["status"],    results["language"]["recommendation"]),
        (t("check_favicon", lang),       results["favicon"]["status"],     results["favicon"]["recommendation"]),
    ]
    if check_ssl_opt and ssl_info.get("valid") is not None:
        checks.append((t("check_ssl_cert", lang), "good" if ssl_info.get("valid") else "bad",
                        t("valid_until", lang, date=ssl_info.get("expires", "")) if ssl_info.get("valid") else t("problem", lang)))
    if check_robots_opt and robots_info.get("exists") is not None:
        checks.append((t("check_robots_txt", lang), "good" if robots_info.get("exists") else "warning",
                        t("exists", lang) if robots_info.get("exists") else t("not_exists", lang)))
    if check_sitemap_opt and sitemap_info.get("exists") is not None:
        checks.append((t("check_sitemap_xml", lang), "good" if sitemap_info.get("exists") else "warning",
                        t("sitemap_found", lang, count=sitemap_info.get("urls_count", 0)) if sitemap_info.get("exists") else t("not_exists", lang)))
    return checks


# ── Sidebar ──
with st.sidebar:
    lang_toggle = st.radio("🌐", ["العربية", "English"], index=0 if lang == "ar" else 1, horizontal=True, label_visibility="collapsed")
    new_lang = "ar" if lang_toggle == "العربية" else "en"
    if new_lang != lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown(f"## 🚀 {t('sidebar_title', lang)}")
    st.markdown(f"*{t('version', lang)}*")
    st.markdown("---")

    app_mode = st.radio(t("sidebar_mode", lang), [t("mode_single", lang), t("mode_compare", lang)], horizontal=True)
    st.markdown("---")

    st.markdown(f"### {t('settings_title', lang)}")
    check_ssl_opt = st.toggle(t("check_ssl", lang), value=True)
    check_robots_opt = st.toggle(t("check_robots", lang), value=True)
    check_sitemap_opt = st.toggle(t("check_sitemap", lang), value=True)
    check_broken_opt = st.toggle(t("check_broken", lang), value=False)
    advanced_mode = st.toggle(t("advanced_mode", lang), value=False)
    timeout_val = st.slider(t("timeout_label", lang), 5, 30, 15)
    max_broken = st.slider(t("broken_count_label", lang), 5, 50, 20) if check_broken_opt else 20
    st.markdown("---")

    if st.session_state.history:
        st.markdown(f"### {t('history_title', lang)}")
        for h in st.session_state.history[:8]:
            sc = h["score"]
            c = "#00c896" if sc >= 80 else "#f59e0b" if sc >= 50 else "#ef4444"
            st.markdown(f"<div style='background:#0d1d32;border:1px solid #152236;border-radius:8px;padding:8px 12px;margin:4px 0;display:flex;justify-content:space-between;align-items:center'><div><div style='color:#e2e8f0;font-size:12px;font-weight:600'>{h['domain']}</div><div style='color:#4a6080;font-size:10px'>{h['time']}</div></div><div style='color:{c};font-weight:900;font-size:16px'>{sc}</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"### {t('test_sites', lang)}")
    for ex in ["bbc.com/arabic", "aljazeera.net", "argaam.com", "amazon.sa"]:
        if st.button(f"🔗 {ex}", key=f"ex_{ex}", use_container_width=True):
            st.session_state["url_input"] = ex

    st.markdown("---")
    st.markdown(f"<div style='color:#4a6080;font-size:10px;text-align:center'>{t('footer_text', lang)}</div>", unsafe_allow_html=True)


# ── Header ──
dir_attr = "rtl" if lang == "ar" else "ltr"
st.markdown(f"<div style='text-align:center;padding:20px 0 10px;direction:{dir_attr}'><h1 style='color:#f8fafc;font-size:2.2rem;font-weight:900;unicode-bidi:plaintext'>{t('page_title', lang)} 🚀</h1><p style='color:#4a6080;font-size:1rem;unicode-bidi:plaintext'>{t('app_subtitle', lang)}</p></div>", unsafe_allow_html=True)


# ── Single Analysis ──
if app_mode == t("mode_single", lang):
    col_inp, col_btn = st.columns([5, 1])
    with col_inp:
        url_input = st.text_input("🔗", value=st.session_state.get("url_input", ""), placeholder=t("url_placeholder", lang), label_visibility="collapsed")
    with col_btn:
        analyze_btn = st.button(t("analyze_btn", lang), type="primary", use_container_width=True)

    if analyze_btn and url_input.strip():
        url = normalize_url(url_input.strip())
        parsed = urlparse(url)
        domain = parsed.netloc
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        progress = st.progress(0)
        status_msg = st.empty()

        try:
            status_msg.info(t("progress_fetching", lang))
            progress.progress(10)
            resp, load_time, err = fetch_page(url, timeout=timeout_val)

            if err or resp is None:
                err_msg = t("ssl_error_fallback", lang) if err == "ssl_error_fallback" else err
                st.error(t("access_error", lang, error=err_msg))
                st.stop()
            if resp.status_code >= 400:
                st.error(t("status_code_error", lang, code=resp.status_code))
                st.stop()

            status_msg.info(t("progress_analyzing", lang))
            progress.progress(25)
            soup = BeautifulSoup(resp.content, "html.parser")

            status_msg.info(t("progress_ssl", lang))
            progress.progress(40)
            ssl_info = check_ssl(domain) if check_ssl_opt else {"valid": None}
            robots_info = check_robots(base_url) if check_robots_opt else {"exists": None}
            sitemap_info = check_sitemap(base_url) if check_sitemap_opt else {"exists": None}

            status_msg.info(t("progress_seo", lang))
            progress.progress(55)
            results = analyze_page(soup, url, load_time, resp, lang)

            status_msg.info(t("progress_content", lang))
            progress.progress(65)
            readability = calculate_readability(soup, lang)
            keywords = extract_keywords(soup, top_n=20)
            og_data = extract_og_data(soup)

            broken_links, links_checked = [], 0
            if check_broken_opt:
                status_msg.info(t("progress_broken", lang))
                progress.progress(75)
                broken_links, links_checked = check_broken_links(soup, base_url, domain, max_broken, lang)

            status_msg.info(t("progress_score", lang))
            progress.progress(90)
            score, label_txt, score_color = calculate_score(results, ssl_info, robots_info, sitemap_info, lang)
            save_to_history(domain, score, label_txt, url)
            progress.progress(100)
            status_msg.empty()
            progress.empty()

            ts = t("time_suffix", lang)

            # Score hero
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.markdown(f"<div class='score-hero' style='border-top:4px solid {score_color}'><div style='font-size:4rem;font-weight:900;color:{score_color}'>{score}</div><div style='color:#94a3b8;font-size:1rem'>/ 100</div><div style='color:{score_color};font-size:1.2rem;font-weight:700;margin-top:8px'>{label_txt}</div><div style='color:#4a6080;font-size:0.85rem;margin-top:6px;font-family:monospace'>{domain}</div><div style='color:#4a6080;font-size:0.75rem;margin-top:4px'>⏱ {load_time}{ts} &nbsp;|&nbsp; 📦 {results['page_size']['kb']} KB &nbsp;|&nbsp; 📖 {readability['score']}% {t('readability_pct', lang)} &nbsp;|&nbsp; 🕐 {datetime.now().strftime('%H:%M')}</div></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Quick overview
            st.markdown(f"### {t('quick_overview', lang)}")
            q1, q2, q3, q4, q5, q6 = st.columns(6)
            quick_items = [
                (q1, t("title_label", lang),  results["title"]["status"],       f"{results['title']['length']} {t('chars', lang)}"),
                (q2, t("desc_label", lang),   results["description"]["status"], f"{results['description']['length']} {t('chars', lang)}"),
                (q3, t("mobile_label", lang), results["mobile"]["status"],      t("compatible", lang) if results["mobile"]["has_viewport"] else "✗"),
                (q4, t("https_label", lang),  results["https"]["status"],       t("secure", lang) if results["https"]["enabled"] else "✗"),
                (q5, t("images_label", lang), results["images"]["status"],      f"{results['images']['with_alt_pct']}% alt"),
                (q6, t("speed_label", lang),  results["load_time"]["status"],   f"{load_time}{ts}"),
            ]
            for col, name, status, val in quick_items:
                c = {"good": "#00c896", "warning": "#f59e0b", "bad": "#ef4444"}.get(status, "#64748b")
                with col:
                    st.markdown(f"<div class='metric-card score-{status}'><div style='color:#94a3b8;font-size:11px'>{name}</div><div style='color:{c};font-size:13px;font-weight:700;margin-top:4px'>{val}</div></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if PLOTLY_AVAILABLE:
                ch1, ch2 = st.columns(2)
                with ch1:
                    st.markdown(f"##### {t('radar_title', lang)}")
                    radar = create_radar_chart(results, ssl_info, robots_info, lang)
                    if radar:
                        st.plotly_chart(radar, use_container_width=True)
                with ch2:
                    st.markdown(f"##### {t('bar_title', lang)}")
                    bar = create_scores_bar(results, ssl_info, lang)
                    if bar:
                        st.plotly_chart(bar, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Tabs
            tab_labels = [t(k, lang) for k in ["tab_technical", "tab_content", "tab_performance", "tab_links", "tab_keywords", "tab_social", "tab_broken_links", "tab_full_report"]]
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(tab_labels)

            with tab1:
                st.markdown(f"#### {t('tech_title', lang)}")
                tech_items = [
                    ("HTTPS / SSL",           results["https"],       results["https"]["recommendation"]),
                    (t("check_page_title", lang), results["title"],   results["title"]["recommendation"]),
                    (t("check_meta_desc", lang),  results["description"], results["description"]["recommendation"]),
                    ("Canonical Tag",         results["canonical"],   results["canonical"]["recommendation"]),
                    ("Open Graph",            results["opengraph"],   results["opengraph"]["recommendation"]),
                    ("Schema Markup",         results["schema"],      results["schema"]["recommendation"]),
                    ("Mobile Viewport",       results["mobile"],      results["mobile"]["recommendation"]),
                    ("Language Tag",          results["language"],    results["language"]["recommendation"]),
                    ("Favicon",               results["favicon"],     results["favicon"]["recommendation"]),
                ]
                for name, data, rec in tech_items:
                    badge = render_badge(data.get("status", "warning"), lang)
                    css = f"alert-{'good' if data.get('status') == 'good' else 'warning' if data.get('status') == 'warning' else 'danger'}"
                    st.markdown(f"<div class='{css}'><div style='display:flex;justify-content:space-between;align-items:center'><span style='color:#e2e8f0;font-weight:600'>{name}</span>{badge}</div><div style='color:#94a3b8;font-size:12px;margin-top:6px'>{rec}</div></div>", unsafe_allow_html=True)

                if check_ssl_opt and ssl_info.get("valid") is not None:
                    st.markdown(f"##### {t('ssl_label', lang)}")
                    if ssl_info.get("valid"):
                        days = ssl_info.get("days_left", 0)
                        ss = "good" if days > 30 else "warning" if days > 7 else "bad"
                        issuer = ssl_info.get("issuer", "") or t("ssl_issuer_unknown", lang)
                        st.markdown(f"<div class='alert-good'><div style='display:flex;justify-content:space-between'><span style='color:#e2e8f0'>{t('ssl_valid', lang, issuer=issuer)}</span>{render_badge(ss, lang)}</div><div style='color:#94a3b8;font-size:12px;margin-top:4px'>{t('ssl_expires', lang, date=ssl_info.get('expires'), days=days)}</div></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='alert-danger'><span style='color:#ef4444'>{t('ssl_problem', lang)}</span></div>", unsafe_allow_html=True)

                if check_robots_opt and robots_info.get("exists") is not None:
                    rs = "good" if robots_info.get("exists") else "warning"
                    alert_css = "alert-good" if rs == "good" else "alert-warning"
                    st.markdown(f"<div class='{alert_css}'><div style='display:flex;justify-content:space-between'><span style='color:#e2e8f0'>{t('robots_label', lang)}</span>{render_badge(rs, lang)}</div></div>", unsafe_allow_html=True)

                if check_sitemap_opt and sitemap_info.get("exists") is not None:
                    ss2 = "good" if sitemap_info.get("exists") else "warning"
                    alert_css2 = "alert-good" if ss2 == "good" else "alert-warning"
                    detail = t("sitemap_path", lang, path=sitemap_info.get("path"), count=sitemap_info.get("urls_count", 0)) if sitemap_info.get("exists") else t("not_exists", lang)
                    st.markdown(f"<div class='{alert_css2}'><div style='display:flex;justify-content:space-between'><span style='color:#e2e8f0'>{t('sitemap_label', lang)}</span>{render_badge(ss2, lang)}</div><div style='color:#94a3b8;font-size:12px;margin-top:4px'>{detail}</div></div>", unsafe_allow_html=True)

            with tab2:
                st.markdown(f"#### {t('content_title', lang)}")
                h = results["headings"]
                css_h = f"alert-{'good' if h['status'] == 'good' else 'warning' if h['status'] == 'warning' else 'danger'}"
                st.markdown(f"<div class='{css_h}'><b style='color:#e2e8f0'>{t('heading_hierarchy', lang)}</b><div style='color:#94a3b8;font-size:12px;margin-top:6px'>H1: {h['h1_count']} | H2: {h['h2_count']} | H3: {h['h3_count']} | H4: {h['h4_count']} | H5: {h['h5_count']} | H6: {h['h6_count']}<br>{h['recommendation']}</div></div>", unsafe_allow_html=True)

                c_data = results["content"]
                pct = min(c_data["words"] / 1000 * 100, 100)
                c_col = "#00c896" if c_data["status"] == "good" else "#f59e0b" if c_data["status"] == "warning" else "#ef4444"
                css_c = f"alert-{'good' if c_data['status'] == 'good' else 'warning' if c_data['status'] == 'warning' else 'danger'}"
                st.markdown(f"<div class='{css_c}'><div style='display:flex;justify-content:space-between'><b style='color:#e2e8f0'>{t('content_size', lang)}</b><span style='color:#94a3b8;font-size:12px'>{c_data['words']} {t('words_label', lang)}</span></div><div class='progress-bar-container' style='margin:8px 0'><div class='progress-bar-fill' style='width:{pct}%;background:{c_col}'></div></div><div style='color:#94a3b8;font-size:12px'>{c_data['recommendation']}</div></div>", unsafe_allow_html=True)

                rd = readability
                rd_col = "#00c896" if rd["score"] >= 70 else "#f59e0b" if rd["score"] >= 40 else "#ef4444"
                st.markdown(f"<div class='metric-card' style='border-right:4px solid {rd_col};margin-top:8px'><div style='font-size:2rem;font-weight:900;color:{rd_col}'>{rd['score']}%</div><div style='color:#e2e8f0;margin:4px 0'>{rd['label']}</div><div style='color:#4a6080;font-size:12px'>{rd['sentences']} {t('sentences_label', lang)} | {t('avg_words_sentence', lang, avg=rd['avg_words'])}</div></div>", unsafe_allow_html=True)

                img = results["images"]
                css_img = f"alert-{'good' if img['status'] == 'good' else 'warning' if img['status'] == 'warning' else 'danger'}"
                st.markdown(f"<div class='{css_img}' style='margin-top:8px'><b style='color:#e2e8f0'>{t('images_section', lang)}</b><div style='color:#94a3b8;font-size:12px;margin-top:6px'>{img['recommendation']}<br>{t('total_label', lang)}: {img['total']} | {t('no_dimensions', lang)}: {img['without_size']}</div></div>", unsafe_allow_html=True)

            with tab3:
                st.markdown(f"#### {t('perf_title', lang)}")
                speed_pct = max(0, 100 - (load_time / 10 * 100))
                speed_color = "#00c896" if load_time < 2 else "#f59e0b" if load_time < 4 else "#ef4444"
                st.markdown(f"<div class='score-hero' style='margin-bottom:12px'><div style='font-size:2.5rem;font-weight:900;color:{speed_color}'>{load_time}{ts}</div><div style='color:#94a3b8'>{t('page_load_time', lang)}</div><div class='progress-bar-container' style='margin:12px auto;max-width:300px'><div class='progress-bar-fill' style='width:{speed_pct}%;background:{speed_color}'></div></div><div style='color:#94a3b8;font-size:12px'>{results['load_time']['recommendation']}</div></div>", unsafe_allow_html=True)

                ps = results["page_size"]
                size_pct = min(ps["kb"] / 2000 * 100, 100)
                ps_col = "#00c896" if ps["status"] == "good" else "#f59e0b" if ps["status"] == "warning" else "#ef4444"
                css_ps = f"alert-{'good' if ps['status'] == 'good' else 'warning' if ps['status'] == 'warning' else 'danger'}"
                st.markdown(f"<div class='{css_ps}'><div style='display:flex;justify-content:space-between'><b style='color:#e2e8f0'>{t('page_size_label', lang)}</b><span style='color:#94a3b8'>{ps['kb']} KB</span></div><div class='progress-bar-container' style='margin:8px 0'><div class='progress-bar-fill' style='width:{size_pct}%;background:{ps_col}'></div></div></div>", unsafe_allow_html=True)

                st.markdown(f"##### {t('speed_tips_title', lang)}")
                for tip in t("speed_tips", lang):
                    st.markdown(f"<div style='background:#0d1d32;border:1px solid #152236;border-radius:8px;padding:10px 14px;margin:5px 0;color:#94a3b8;font-size:13px'>{tip}</div>", unsafe_allow_html=True)

            with tab4:
                st.markdown(f"#### {t('links_title', lang)}")
                lk = results["links"]
                lc1, lc2, lc3, lc4 = st.columns(4)
                for col, lbl, val, clr in [(lc1, t("links_total", lang), lk["total"], "#38bdf8"), (lc2, t("links_internal", lang), lk["internal"], "#00c896"), (lc3, t("links_external", lang), lk["external"], "#f59e0b"), (lc4, t("links_nofollow", lang), lk["nofollow"], "#a78bfa")]:
                    with col:
                        st.markdown(f"<div class='metric-card'><div style='color:#94a3b8;font-size:12px'>{lbl}</div><div style='color:{clr};font-size:2rem;font-weight:900'>{val}</div></div>", unsafe_allow_html=True)

            with tab5:
                st.markdown(f"#### {t('keywords_title', lang)}")
                if keywords:
                    max_count = keywords[0][1]
                    for word, count in keywords:
                        pct = int(count / max_count * 100)
                        bar_c = "#00c896" if pct >= 60 else "#f59e0b" if pct >= 30 else "#64748b"
                        st.markdown(f"<div style='background:#0d1d32;border:1px solid #152236;border-radius:8px;padding:10px 14px;margin:5px 0;display:flex;align-items:center;gap:14px'><span style='color:#e2e8f0;font-weight:600;min-width:120px'>{word}</span><div style='flex:1;background:#152236;border-radius:4px;height:8px;overflow:hidden'><div style='width:{pct}%;height:100%;background:{bar_c};border-radius:4px'></div></div><span style='color:{bar_c};font-weight:700;min-width:30px;text-align:left'>{count}</span></div>", unsafe_allow_html=True)
                else:
                    st.warning(t("no_keywords", lang))

            with tab6:
                st.markdown(f"#### {t('social_title', lang)}")
                og = og_data["og"]
                tw = og_data["twitter"]

                st.markdown(f"##### {t('fb_og_title', lang)}")
                og_img = og.get("og:image", "")
                og_t = og.get("og:title", "") or results["title"]["value"]
                og_d = og.get("og:description", "") or results["description"]["value"]
                og_site = og.get("og:site_name", "") or domain
                img_html = f"<img src='{og_img}' onerror=\"this.style.display='none'\">" if og_img else f"<div style='height:200px;background:#e2e8f0;display:flex;align-items:center;justify-content:center;color:#94a3b8'>{t('no_og_image', lang)}</div>"
                st.markdown(f"<div class='og-preview'>{img_html}<div class='og-preview-body'><div class='og-preview-domain'>{og_site}</div><div class='og-preview-title'>{og_t}</div><div class='og-preview-desc'>{og_d[:100]}...</div></div></div>", unsafe_allow_html=True)

                st.markdown(f"##### {t('twitter_card_title', lang)}")
                tw_card = tw.get("twitter:card", "") or t("not_specified", lang)
                tw_t = tw.get("twitter:title", "") or og_t
                tw_d = tw.get("twitter:description", "") or og_d
                st.markdown(f"<div style='background:#0d1d32;border:1px solid #152236;border-radius:10px;padding:14px;margin:8px 0'><div style='color:#94a3b8;font-size:12px'>{t('card_type', lang)}: <b style='color:#38bdf8'>{tw_card}</b></div><div style='color:#e2e8f0;font-weight:600;margin-top:6px'>{tw_t}</div><div style='color:#4a6080;font-size:12px;margin-top:4px'>{tw_d[:80]}...</div></div>", unsafe_allow_html=True)

                tags_check = [("og:title", bool(og.get("og:title"))), ("og:description", bool(og.get("og:description"))), ("og:image", bool(og.get("og:image"))), ("twitter:card", bool(tw.get("twitter:card"))), ("twitter:title", bool(tw.get("twitter:title"))), ("twitter:image", bool(tw.get("twitter:image")))]
                st.markdown(f"##### {t('tags_status', lang)}")
                for tag, exists in tags_check:
                    st.markdown(f"`{tag}`: {'✅' if exists else '❌'}")

            with tab7:
                st.markdown(f"#### {t('broken_title', lang)}")
                if not check_broken_opt:
                    st.info(t("broken_enable_hint", lang))
                elif broken_links:
                    st.error(t("broken_found", lang, count=len(broken_links), total=links_checked))
                    for bl in broken_links:
                        status_txt = t("broken_code", lang, code=bl["status"]) if bl["status"] > 0 else t("broken_no_response", lang)
                        st.markdown(f"<div class='alert-danger'><div style='display:flex;justify-content:space-between'><span style='color:#e2e8f0;font-weight:600'>{bl['text']}</span><span style='color:#ef4444;font-size:12px'>{bl['type']} — {status_txt}</span></div><div style='color:#4a6080;font-size:11px;margin-top:4px;font-family:monospace;direction:ltr;text-align:left'>{bl['url']}</div></div>", unsafe_allow_html=True)
                else:
                    st.success(t("broken_none", lang, count=links_checked))

            with tab8:
                st.markdown(f"#### {t('report_title', lang)}")
                all_checks = build_all_checks(results, ssl_info, robots_info, sitemap_info, check_ssl_opt, check_robots_opt, check_sitemap_opt)

                df, csv_data = build_csv(all_checks, lang)
                st.dataframe(df, use_container_width=True, hide_index=True)

                report_json = build_json_report(url, domain, score, label_txt, load_time, readability, keywords, broken_links, all_checks, ssl_info, robots_info, sitemap_info, lang)
                date_str = datetime.now().strftime("%Y%m%d")
                ec1, ec2, ec3, ec4 = st.columns(4)
                with ec1:
                    st.download_button(t("export_json", lang), data=json.dumps(report_json, ensure_ascii=False, indent=2), file_name=f"seo-{domain}-{date_str}.json", mime="application/json", use_container_width=True)
                with ec2:
                    st.download_button(t("export_csv", lang), data=csv_data, file_name=f"seo-{domain}-{date_str}.csv", mime="text/csv", use_container_width=True)
                with ec3:
                    if EXCEL_AVAILABLE:
                        xl = build_excel_report(domain, score, label_txt, results, ssl_info, robots_info, sitemap_info, all_checks, keywords, lang)
                        st.download_button(t("export_excel", lang), data=xl, file_name=f"seo-{domain}-{date_str}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                    else:
                        st.info(t("install_openpyxl", lang))
                with ec4:
                    pdf_html = generate_pdf_html(domain, score, label_txt, score_color, results, all_checks, ssl_info, robots_info, sitemap_info, readability, keywords, lang)
                    st.download_button(t("export_pdf", lang), data=pdf_html, file_name=f"seo-{domain}-{date_str}.html", mime="text/html", use_container_width=True)

        except Exception as e:
            progress.empty()
            status_msg.empty()
            st.error(f"{t('error_prefix', lang)} {str(e)}")
            if advanced_mode:
                st.exception(e)

    elif not url_input.strip() and analyze_btn:
        st.warning(t("enter_url_warning", lang))
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        cards = [
            (c1, "🔍", t("card_real_analysis", lang), t("card_real_analysis_desc", lang)),
            (c2, "📊", t("card_criteria", lang), t("card_criteria_desc", lang)),
            (c3, "⬇️", t("card_export", lang), t("card_export_desc", lang)),
        ]
        for col, icon, title, desc in cards:
            with col:
                st.markdown(f"<div class='metric-card' style='padding:20px'><div style='font-size:2rem'>{icon}</div><div style='color:#f8fafc;font-weight:700;margin:8px 0'>{title}</div><div style='color:#4a6080;font-size:13px'>{desc}</div></div>", unsafe_allow_html=True)


# ── Compare Mode ──
elif app_mode == t("mode_compare", lang):
    st.markdown(f"### {t('compare_title', lang)}")

    cmp1, cmp2 = st.columns(2)
    with cmp1:
        url1 = st.text_input(t("site1_label", lang), placeholder="example1.com", key="cmp_url1")
    with cmp2:
        url2 = st.text_input(t("site2_label", lang), placeholder="example2.com", key="cmp_url2")

    if st.button(t("compare_btn", lang), type="primary", use_container_width=True):
        if url1.strip() and url2.strip():
            u1, u2 = normalize_url(url1.strip()), normalize_url(url2.strip())
            d1, d2 = urlparse(u1).netloc, urlparse(u2).netloc

            progress = st.progress(0)
            status_msg = st.empty()
            ts = t("time_suffix", lang)

            try:
                status_msg.info(t("progress_analyzing_domain", lang, domain=d1))
                progress.progress(15)
                r1, lt1, e1 = fetch_page(u1, timeout=timeout_val)
                if e1 or r1 is None:
                    st.error(t("access_error_domain", lang, domain=d1, error=e1))
                    st.stop()

                status_msg.info(t("progress_analyzing_domain", lang, domain=d2))
                progress.progress(40)
                r2, lt2, e2 = fetch_page(u2, timeout=timeout_val)
                if e2 or r2 is None:
                    st.error(t("access_error_domain", lang, domain=d2, error=e2))
                    st.stop()

                progress.progress(60)
                soup1, soup2 = BeautifulSoup(r1.content, "html.parser"), BeautifulSoup(r2.content, "html.parser")
                ssl1 = check_ssl(d1) if check_ssl_opt else {"valid": None}
                ssl2 = check_ssl(d2) if check_ssl_opt else {"valid": None}
                rob1 = check_robots(f"{urlparse(u1).scheme}://{d1}") if check_robots_opt else {"exists": None}
                rob2 = check_robots(f"{urlparse(u2).scheme}://{d2}") if check_robots_opt else {"exists": None}

                progress.progress(75)
                res1, res2 = analyze_page(soup1, u1, lt1, r1, lang), analyze_page(soup2, u2, lt2, r2, lang)
                sc1, lb1, cl1 = calculate_score(res1, ssl1, rob1, {"exists": None}, lang)
                sc2, lb2, cl2 = calculate_score(res2, ssl2, rob2, {"exists": None}, lang)

                progress.progress(100)
                status_msg.empty()
                progress.empty()

                mc1, mc_vs, mc2 = st.columns([2, 1, 2])
                with mc1:
                    st.markdown(f"<div class='score-hero' style='border-top:4px solid {cl1}'><div style='font-size:3rem;font-weight:900;color:{cl1}'>{sc1}</div><div style='color:{cl1};margin-top:4px'>{lb1}</div><div style='color:#4a6080;font-family:monospace;font-size:13px;margin-top:4px'>{d1}</div><div style='color:#4a6080;font-size:11px'>⏱ {lt1}{ts} | 📦 {res1['page_size']['kb']} KB</div></div>", unsafe_allow_html=True)
                with mc_vs:
                    winner = d1 if sc1 > sc2 else d2 if sc2 > sc1 else t("compare_tie", lang)
                    st.markdown(f"<div style='text-align:center;padding:30px 0'><div style='font-size:2rem'>⚖️</div><div style='color:#f59e0b;font-weight:900;font-size:1.5rem;margin:12px 0'>{t('compare_vs', lang)}</div><div style='color:#00c896;font-size:12px;font-weight:700'>{t('compare_winner', lang, winner=winner)}</div></div>", unsafe_allow_html=True)
                with mc2:
                    st.markdown(f"<div class='score-hero' style='border-top:4px solid {cl2}'><div style='font-size:3rem;font-weight:900;color:{cl2}'>{sc2}</div><div style='color:{cl2};margin-top:4px'>{lb2}</div><div style='color:#4a6080;font-family:monospace;font-size:13px;margin-top:4px'>{d2}</div><div style='color:#4a6080;font-size:11px'>⏱ {lt2}{ts} | 📦 {res2['page_size']['kb']} KB</div></div>", unsafe_allow_html=True)

                if PLOTLY_AVAILABLE:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"##### {t('compare_radar_title', lang)}")
                    cmp_radar = create_comparison_radar(res1, res2, d1, d2, lang)
                    if cmp_radar:
                        st.plotly_chart(cmp_radar, use_container_width=True)

                st.markdown(f"##### {t('compare_details_title', lang)}")
                compare_keys = ["title", "description", "headings", "images", "links", "load_time", "mobile", "https", "canonical", "opengraph", "schema", "content"]
                label_map = {
                    "title": "radar_cat_title", "description": "radar_cat_desc", "headings": "radar_cat_headings",
                    "images": "radar_cat_images", "links": "radar_cat_links", "load_time": "radar_cat_speed",
                    "mobile": "radar_cat_mobile", "https": "radar_cat_https", "canonical": "radar_cat_canonical",
                    "opengraph": "radar_cat_og", "schema": "radar_cat_schema", "content": "radar_cat_content",
                }
                emj = {"good": "✅", "warning": "⚠️", "bad": "❌"}
                for key in compare_keys:
                    item_name = t(label_map[key], lang)
                    s1 = res1.get(key, {}).get("status", "bad")
                    s2 = res2.get(key, {}).get("status", "bad")
                    v1 = {"good": 100, "warning": 50, "bad": 10}.get(s1, 0)
                    v2 = {"good": 100, "warning": 50, "bad": 10}.get(s2, 0)
                    w1 = "🏆" if v1 > v2 else ""
                    w2 = "🏆" if v2 > v1 else ""
                    st.markdown(f"<div style='display:grid;grid-template-columns:1fr 100px 1fr;gap:8px;align-items:center;background:#0d1d32;border:1px solid #152236;border-radius:8px;padding:10px 14px;margin:4px 0'><div style='text-align:center;color:#e2e8f0'>{emj.get(s1, '')} {w1}</div><div style='text-align:center;color:#94a3b8;font-size:12px'>{item_name}</div><div style='text-align:center;color:#e2e8f0'>{emj.get(s2, '')} {w2}</div></div>", unsafe_allow_html=True)

            except Exception as e:
                progress.empty()
                status_msg.empty()
                st.error(f"{t('error_prefix', lang)} {str(e)}")
        else:
            st.warning(t("enter_both_warning", lang))
