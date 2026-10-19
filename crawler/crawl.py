#!/usr/bin/env python3
"""Polite metadata-only crawler. Does not download document bodies or binary assets."""
import argparse, hashlib, json, time
from collections import deque
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, urldefrag
import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

UA = "LearningHubIndexer/0.1 (+metadata indexing; contact: configure a project contact)"
ALLOW_HOSTS = {"thi247.com", "www.thi247.com"}

def now():
    return datetime.now(timezone.utc).isoformat()

def normalize(url):
    url, _ = urldefrag(url)
    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in ALLOW_HOSTS:
        return None
    # Strip tracking parameters; preserve query only if it appears structural.
    return p._replace(fragment="", query="").geturl().rstrip("/") + ("/" if p.path in ("", "/") else "")

def load_robots(base, session, ua):
    rp = RobotFileParser()
    url = urljoin(base, "/robots.txt")
    try:
        r = session.get(url, timeout=15, headers={"User-Agent": ua})
        if r.status_code == 200:
            rp.parse(r.text.splitlines())
        else:
            # Conservative default: no crawl if robots policy cannot be retrieved.
            rp.parse(["User-agent: *", "Disallow: /"])
    except requests.RequestException:
        rp.parse(["User-agent: *", "Disallow: /"])
    return rp

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="https://thi247.com/")
    ap.add_argument("--max-pages", type=int, default=100)
    ap.add_argument("--delay", type=float, default=2.0)
    ap.add_argument("--out", default="data/catalog.jsonl")
    ap.add_argument("--timeout", type=int, default=20)
    args = ap.parse_args()
    if args.max_pages < 1 or args.max_pages > 5000:
        ap.error("--max-pages must be between 1 and 5000")
    if args.delay < 1:
        ap.error("--delay must be >= 1 second")

    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    start = normalize(args.start)
    if not start:
        ap.error("Start URL must be an HTTP(S) URL on thi247.com")
    robots = load_robots("https://thi247.com", session, UA)
    if not robots.can_fetch(UA, start):
        raise SystemExit(f"robots.txt disallows start URL: {start}")

    queue, seen, records = deque([start]), set(), []
    while queue and len(seen) < args.max_pages:
        url = queue.popleft()
        if url in seen: continue
        seen.add(url)
        if not robots.can_fetch(UA, url):
            print("ROBOTS_SKIP", url); continue
        try:
            resp = session.get(url, timeout=args.timeout, allow_redirects=True)
            time.sleep(args.delay)
        except requests.RequestException as exc:
            print("FETCH_ERROR", url, str(exc)); continue
        final_url = normalize(resp.url)
        if not final_url or resp.status_code != 200:
            print("HTTP_SKIP", resp.status_code, url); continue
        ctype = resp.headers.get("Content-Type", "").lower()
        if "text/html" not in ctype:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        canonical_tag = soup.find("link", rel=lambda v: v and "canonical" in v)
        canonical = normalize(urljoin(final_url, canonical_tag.get("href"))) if canonical_tag and canonical_tag.get("href") else final_url
        desc_tag = soup.find("meta", attrs={"name": "description"})
        description = desc_tag.get("content", "").strip() if desc_tag else ""
        main_text = soup.find("main") or soup.find("article") or soup.body or soup
        description = (description or main_text.get_text(" ", strip=True)[:500]).strip()
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        path = urlparse(final_url).path.lower()
        resource_type = "textbook" if any(s in path for s in ("sach-giao-khoa", "sach-giao-khoa")) else (
            "exam" if any(s in path for s in ("de-thi", "de-kiem-tra", "thi-thu")) else "article")
        record = {
            "id": digest, "title": title[:300], "source_url": final_url, "canonical_url": canonical,
            "domain": urlparse(final_url).hostname, "resource_type": resource_type,
            "grade": None, "subject": None, "topic": None, "description": description[:800],
            "published_at": None, "discovered_at": now(), "checked_at": now(),
            "http_status": resp.status_code, "rights_status": "unknown",
            "rights_evidence_url": None, "license": None, "permission_notes": None,
            "content_stored": False, "download_url": None, "content_hash": None,
            "crawl_status": "indexed", "source_title": "THI247", "tags": []
        }
        records.append(record)
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            absolute = urljoin(final_url, href)
            # Never fetch binary files; record their existence only as an optional link later.
            candidate = normalize(absolute)
            if candidate and candidate not in seen and candidate not in queue and robots.can_fetch(UA, candidate):
                queue.append(candidate)
        print(f"[{len(seen)}/{args.max_pages}] {resp.status_code} {final_url}")
    with open(args.out, "w", encoding="utf-8") as f:
        for item in records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} metadata records to {args.out}")

if __name__ == "__main__":
    main()
