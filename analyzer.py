import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter
from translations import t


def extract_keywords(soup: BeautifulSoup, top_n: int = 20) -> list:
    stop_words = {
        "في", "من", "على", "إلى", "عن", "مع", "هذا", "هذه", "التي", "الذي", "كان", "كانت",
        "أن", "إن", "لا", "ما", "هو", "هي", "هم", "نحن", "أنا", "أو", "و", "ب", "ل", "ف", "ق",
        "ذلك", "هنا", "هناك", "كل", "بعض", "عند", "قد", "حتى", "بين", "ثم", "لكن", "بل",
        "the", "and", "or", "is", "are", "in", "of", "to", "a", "an", "it", "for", "on", "with",
        "this", "that", "was", "be", "have", "has", "not", "at", "by", "from", "but", "as", "do",
        "will", "would", "can", "could", "should", "may", "might", "your", "you", "our", "we",
        "they", "them", "their", "its", "all", "more", "also", "new", "about", "than", "just",
    }
    body = soup.find("body")
    if not body:
        return []
    text = body.get_text(separator=" ", strip=True).lower()
    words = re.findall(r'\b[؀-ۿa-zA-Z]{3,}\b', text)
    filtered = [w for w in words if w not in stop_words]
    return Counter(filtered).most_common(top_n)


def calculate_readability(soup: BeautifulSoup, lang: str = "ar") -> dict:
    body = soup.find("body")
    if not body:
        return {"score": 0, "label": t("readability_no_content", lang), "sentences": 0, "avg_words": 0}

    text = body.get_text(separator=" ", strip=True)
    sentences = re.split(r'[.!?。؟!٫]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    total_sentences = len(sentences)

    if total_sentences == 0:
        return {"score": 0, "label": t("readability_insufficient", lang), "sentences": 0, "avg_words": 0}

    words = text.split()
    total_words = len(words)
    avg_words_per_sentence = round(total_words / total_sentences, 1)

    if avg_words_per_sentence <= 15:
        score = 90
        label = t("readability_easy", lang)
    elif avg_words_per_sentence <= 20:
        score = 70
        label = t("readability_medium", lang)
    elif avg_words_per_sentence <= 30:
        score = 50
        label = t("readability_hard", lang)
    else:
        score = 30
        label = t("readability_very_hard", lang)

    return {
        "score": score,
        "label": label,
        "sentences": total_sentences,
        "avg_words": avg_words_per_sentence,
        "total_words": total_words,
    }


def extract_og_data(soup: BeautifulSoup) -> dict:
    og = {}
    for prop in ["og:title", "og:description", "og:image", "og:url", "og:type", "og:site_name"]:
        tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        og[prop] = tag.get("content", "").strip() if tag else ""

    tw = {}
    for name in ["twitter:card", "twitter:title", "twitter:description", "twitter:image"]:
        tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", property=name)
        tw[name] = tag.get("content", "").strip() if tag else ""

    return {"og": og, "twitter": tw}


def analyze_page(soup: BeautifulSoup, url: str, load_time: float, resp, lang: str = "ar") -> dict:
    results = {}
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    domain = parsed.netloc

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    title_len = len(title)

    desc_tag = soup.find("meta", attrs={"name": re.compile("description", re.I)})
    desc = desc_tag.get("content", "").strip() if desc_tag else ""
    desc_len = len(desc)

    results["title"] = {
        "value": title[:80] + "..." if len(title) > 80 else title,
        "length": title_len,
        "status": "good" if 30 <= title_len <= 65 else "warning" if title_len > 0 else "bad",
        "recommendation": (
            t("rec_title_good", lang) if 30 <= title_len <= 65 else
            t("rec_title_warn", lang, length=title_len) if title_len > 0 else
            t("rec_title_bad", lang)
        )
    }

    results["description"] = {
        "value": desc[:100] + "..." if len(desc) > 100 else desc,
        "length": desc_len,
        "status": "good" if 120 <= desc_len <= 160 else "warning" if desc_len > 0 else "bad",
        "recommendation": (
            t("rec_desc_good", lang) if 120 <= desc_len <= 160 else
            t("rec_desc_warn", lang, length=desc_len) if desc_len > 0 else
            t("rec_desc_bad", lang)
        )
    }

    h_counts = {}
    for level in range(1, 7):
        h_counts[f"h{level}"] = len(soup.find_all(f"h{level}"))
    h1_tags = soup.find_all("h1")
    h1_count = len(h1_tags)
    h1_text = h1_tags[0].get_text(strip=True)[:60] if h1_tags else ""

    results["headings"] = {
        "h1_count": h1_count, "h1_text": h1_text,
        "h2_count": h_counts["h2"], "h3_count": h_counts["h3"],
        "h4_count": h_counts["h4"], "h5_count": h_counts["h5"], "h6_count": h_counts["h6"],
        "all_counts": h_counts,
        "status": "good" if h1_count == 1 else "warning" if h1_count > 1 else "bad",
        "recommendation": (
            t("rec_h1_good", lang, text=h1_text[:40]) if h1_count == 1 else
            t("rec_h1_warn", lang, count=h1_count) if h1_count > 1 else
            t("rec_h1_bad", lang)
        )
    }

    images = soup.find_all("img")
    imgs_total = len(images)
    imgs_no_alt = sum(1 for img in images if not img.get("alt", "").strip())
    imgs_pct = round((imgs_total - imgs_no_alt) / imgs_total * 100) if imgs_total > 0 else 100
    imgs_no_size = sum(1 for img in images if not img.get("width") and not img.get("height"))

    results["images"] = {
        "total": imgs_total, "without_alt": imgs_no_alt, "with_alt_pct": imgs_pct,
        "without_size": imgs_no_size,
        "status": "good" if imgs_no_alt == 0 else "warning" if imgs_no_alt <= 3 else "bad",
        "recommendation": (
            t("rec_img_good", lang, total=imgs_total) if imgs_no_alt == 0 else
            t("rec_img_warn", lang, without=imgs_no_alt, total=imgs_total)
        )
    }

    all_links = soup.find_all("a", href=True)
    internal_links = [a for a in all_links if domain in a["href"] or a["href"].startswith("/")]
    external_links = [a for a in all_links if a["href"].startswith("http") and domain not in a["href"]]
    broken_pattern = ["#", "javascript:", "mailto:", "tel:"]
    clean_int = [a for a in internal_links if not any(p in a["href"] for p in broken_pattern)]
    nofollow_count = sum(1 for a in all_links if "nofollow" in a.get("rel", []))

    results["links"] = {
        "total": len(all_links), "internal": len(clean_int),
        "external": len(external_links), "nofollow": nofollow_count,
        "status": "good" if len(clean_int) >= 5 else "warning" if len(clean_int) >= 2 else "bad",
        "recommendation": (
            t("rec_links_good", lang, internal=len(clean_int), external=len(external_links)) if len(clean_int) >= 5 else
            t("rec_links_warn", lang, internal=len(clean_int))
        )
    }

    results["load_time"] = {
        "value": load_time,
        "status": "good" if load_time < 2 else "warning" if load_time < 4 else "bad",
        "recommendation": (
            t("rec_speed_good", lang, time=load_time) if load_time < 2 else
            t("rec_speed_warn", lang, time=load_time) if load_time < 4 else
            t("rec_speed_bad", lang, time=load_time)
        )
    }

    viewport = soup.find("meta", attrs={"name": "viewport"})
    has_viewport = viewport is not None and "width=device-width" in viewport.get("content", "")

    results["mobile"] = {
        "has_viewport": has_viewport,
        "status": "good" if has_viewport else "bad",
        "recommendation": (
            t("rec_mobile_good", lang) if has_viewport else
            t("rec_mobile_bad", lang)
        )
    }

    canonical = soup.find("link", rel="canonical")
    canon_url = canonical.get("href", "") if canonical else ""

    results["canonical"] = {
        "exists": canonical is not None, "url": canon_url[:80] if canon_url else "",
        "status": "good" if canonical else "warning",
        "recommendation": (
            t("rec_canonical_good", lang) if canonical else
            t("rec_canonical_warn", lang)
        )
    }

    og_title = soup.find("meta", property="og:title")
    og_desc = soup.find("meta", property="og:description")
    og_image = soup.find("meta", property="og:image")
    og_count = sum(1 for tag in [og_title, og_desc, og_image] if tag)

    results["opengraph"] = {
        "has_title": og_title is not None,
        "has_desc": og_desc is not None,
        "has_image": og_image is not None,
        "count": og_count,
        "status": "good" if og_count == 3 else "warning" if og_count >= 1 else "bad",
        "recommendation": (
            t("rec_og_good", lang) if og_count == 3 else
            t("rec_og_warn", lang, count=og_count) if og_count >= 1 else
            t("rec_og_bad", lang)
        )
    }

    schemas = soup.find_all("script", attrs={"type": "application/ld+json"})
    schema_types = []
    for s in schemas:
        try:
            data = json.loads(s.string or "")
            if isinstance(data, dict) and "@type" in data:
                schema_types.append(data["@type"])
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "@type" in item:
                        schema_types.append(item["@type"])
        except:
            pass

    results["schema"] = {
        "count": len(schemas), "types": schema_types,
        "status": "good" if len(schemas) >= 1 else "warning",
        "recommendation": (
            t("rec_schema_good", lang, types=", ".join(schema_types[:3])) if schema_types else
            t("rec_schema_warn", lang)
        )
    }

    page_size_kb = round(len(resp.content) / 1024, 1) if resp else 0
    results["page_size"] = {
        "kb": page_size_kb,
        "status": "good" if page_size_kb < 500 else "warning" if page_size_kb < 1500 else "bad",
        "recommendation": (
            t("rec_size_good", lang, size=page_size_kb) if page_size_kb < 500 else
            t("rec_size_warn", lang, size=page_size_kb) if page_size_kb < 1500 else
            t("rec_size_bad", lang, size=page_size_kb)
        )
    }

    is_https = url.startswith("https://")
    results["https"] = {
        "enabled": is_https,
        "status": "good" if is_https else "bad",
        "recommendation": (
            t("rec_https_good", lang) if is_https else
            t("rec_https_bad", lang)
        )
    }

    body = soup.find("body")
    text = body.get_text(separator=" ", strip=True) if body else ""
    words = len(text.split())

    results["content"] = {
        "words": words,
        "status": "good" if words >= 300 else "warning" if words >= 100 else "bad",
        "recommendation": (
            t("rec_content_good", lang, words=words) if words >= 300 else
            t("rec_content_warn", lang, words=words) if words >= 100 else
            t("rec_content_bad", lang, words=words)
        )
    }

    html_tag = soup.find("html")
    page_lang = html_tag.get("lang", "") if html_tag else ""
    results["language"] = {
        "value": page_lang,
        "status": "good" if page_lang else "warning",
        "recommendation": (
            t("rec_lang_good", lang, detected_lang=page_lang) if page_lang else
            t("rec_lang_warn", lang)
        )
    }

    favicon = soup.find("link", rel=re.compile("icon", re.I))
    results["favicon"] = {
        "exists": favicon is not None,
        "status": "good" if favicon else "warning",
        "recommendation": (
            t("rec_favicon_good", lang) if favicon else
            t("rec_favicon_warn", lang)
        )
    }

    return results


def calculate_score(results: dict, ssl_info: dict, robots: dict, sitemap: dict, lang: str = "ar") -> tuple:
    weights = {
        "title":       (12, results.get("title",       {}).get("status")),
        "description": (10, results.get("description", {}).get("status")),
        "headings":    (8,  results.get("headings",    {}).get("status")),
        "images":      (7,  results.get("images",      {}).get("status")),
        "links":       (7,  results.get("links",       {}).get("status")),
        "load_time":   (12, results.get("load_time",   {}).get("status")),
        "mobile":      (10, results.get("mobile",      {}).get("status")),
        "https":       (10, results.get("https",       {}).get("status")),
        "canonical":   (4,  results.get("canonical",   {}).get("status")),
        "opengraph":   (4,  results.get("opengraph",   {}).get("status")),
        "schema":      (4,  results.get("schema",      {}).get("status")),
        "content":     (4,  results.get("content",     {}).get("status")),
        "language":    (2,  results.get("language",    {}).get("status")),
        "favicon":     (1,  results.get("favicon",     {}).get("status")),
    }
    ssl_status = "good" if ssl_info.get("valid") else "bad"
    robots_status = "good" if robots.get("exists") else "warning"
    weights["ssl"]    = (4, ssl_status)
    weights["robots"] = (1, robots_status)

    total_weight = sum(w for w, _ in weights.values())
    earned = sum(w * (1 if s == "good" else 0.5 if s == "warning" else 0) for w, s in weights.values())

    score = round((earned / total_weight) * 100)
    label = (
        t("score_excellent", lang) if score >= 80 else
        t("score_good", lang) if score >= 60 else
        t("score_needs_work", lang) if score >= 40 else
        t("score_poor", lang)
    )
    color = "#00c896" if score >= 80 else "#22c55e" if score >= 60 else "#f59e0b" if score >= 40 else "#ef4444"
    return score, label, color


def render_badge(status: str, lang: str = "ar") -> str:
    colors = {"good": "#00c896", "warning": "#f59e0b", "bad": "#ef4444"}
    labels = {
        "good": t("badge_good", lang),
        "warning": t("badge_warning", lang),
        "bad": t("badge_bad", lang),
    }
    c = colors.get(status, "#64748b")
    l = labels.get(status, status)
    return f'<span style="background:{c}22;color:{c};border:1px solid {c}44;border-radius:5px;padding:2px 8px;font-size:12px;font-weight:700">{l}</span>'
