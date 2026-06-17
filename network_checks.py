import requests
import ssl
import socket
import time
import urllib3
from datetime import datetime
from urllib.parse import urljoin

urllib3.disable_warnings()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def fetch_page(url: str, timeout: int = 15):
    try:
        start = time.time()
        resp = requests.get(url, headers=HEADERS, timeout=timeout, verify=False, allow_redirects=True)
        load_time = round(time.time() - start, 2)
        return resp, load_time, None
    except requests.exceptions.SSLError:
        try:
            resp = requests.get(url.replace("https://", "http://"), headers=HEADERS, timeout=timeout)
            load_time = round(time.time() - start, 2)
            return resp, load_time, "ssl_error_fallback"
        except Exception as e:
            return None, 0, str(e)
    except Exception as e:
        return None, 0, str(e)


def check_ssl(domain: str) -> dict:
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(15)
            s.connect((domain, 443))
            cert = s.getpeercert()
            exp = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            days_left = (exp - datetime.utcnow()).days
            issuer_info = dict(x[0] for x in cert.get("issuer", []))
            issuer = issuer_info.get("organizationName", "")
            return {"valid": True, "expires": exp.strftime("%Y-%m-%d"), "days_left": days_left, "issuer": issuer}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def check_robots(base_url: str) -> dict:
    try:
        r = requests.get(f"{base_url}/robots.txt", headers=HEADERS, timeout=15, verify=False)
        if r.status_code == 200 and len(r.text) > 10:
            has_sitemap = "sitemap" in r.text.lower()
            has_disallow = "disallow" in r.text.lower()
            return {"exists": True, "has_sitemap": has_sitemap, "has_disallow": has_disallow, "content": r.text[:800]}
        return {"exists": False}
    except:
        return {"exists": False}


def check_sitemap(base_url: str) -> dict:
    paths = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap/sitemap.xml", "/sitemap/"]
    for path in paths:
        try:
            r = requests.get(f"{base_url}{path}", headers=HEADERS, timeout=15, verify=False)
            if r.status_code == 200 and ("<url" in r.text or "<sitemap" in r.text):
                urls_count = r.text.count("<url>") + r.text.count("<sitemap>")
                return {"exists": True, "path": path, "urls_count": urls_count}
        except:
            pass
    return {"exists": False, "path": "", "urls_count": 0}


def check_broken_links(soup, base_url: str, domain: str, max_links: int = 20, lang: str = "ar") -> tuple:
    from translations import t

    all_links = soup.find_all("a", href=True)
    broken = []
    checked = 0
    seen = set()

    for a in all_links:
        if checked >= max_links:
            break
        href = a.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = urljoin(base_url, href)
        if full_url in seen:
            continue
        seen.add(full_url)

        text = a.get_text(strip=True)[:40] or t("no_text", lang)
        try:
            r = requests.head(full_url, headers=HEADERS, timeout=15, verify=False, allow_redirects=True)
            status_code = r.status_code
        except:
            status_code = 0

        checked += 1
        time.sleep(0.5)
        link_type = t("broken_internal", lang) if domain in full_url else t("broken_external", lang)
        if status_code >= 400 or status_code == 0:
            broken.append({
                "url": full_url[:80],
                "text": text,
                "status": status_code,
                "type": link_type,
            })

    return broken, checked
