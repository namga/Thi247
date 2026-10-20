#!/usr/bin/env python3
"""Polite THI247 resource crawler. Optional direct-file downloads; never bypasses robots or access controls."""
import argparse, hashlib, json, os, re, time
from collections import deque
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, urldefrag
import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

UA = "LearningHubIndexer/0.2 (+respectful educational resource indexing)"
ALLOW_HOSTS = {"thi247.com", "www.thi247.com"}
FILE_EXTS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".odt", ".rtf"}
MIME_EXTS = {"application/pdf": ".pdf", "application/msword": ".doc",
             "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
             "application/vnd.ms-powerpoint": ".ppt", "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
             "application/vnd.ms-excel": ".xls", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
             "application/rtf": ".rtf", "text/rtf": ".rtf"}

def now(): return datetime.now(timezone.utc).isoformat()
def allowed_host(url): return urlparse(url).hostname in ALLOW_HOSTS

def normalize(url):
    url, _ = urldefrag(url); p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in ALLOW_HOSTS: return None
    return p._replace(fragment="", query="").geturl().rstrip("/") + ("/" if p.path in ("", "/") else "")

def load_robots(base, session, ua):
    rp = RobotFileParser(); url = urljoin(base, "/robots.txt")
    try:
        r = session.get(url, timeout=15, headers={"User-Agent": ua})
        if r.status_code == 200: rp.parse(r.text.splitlines())
        else: rp.parse(["User-agent: *", "Disallow: /"])
    except requests.RequestException: rp.parse(["User-agent: *", "Disallow: /"])
    return rp

def direct_file_candidate(url, anchor):
    path = urlparse(url).path.lower()
    text = (anchor.get_text(" ", strip=True) + " " + anchor.get("title", "")).lower()
    return os.path.splitext(path)[1] in FILE_EXTS or ("tải xuống" in text or "download" in text or "tải về" in text)

def download_resource(session, robots, file_url, out_dir, delay, timeout, max_bytes):
    if not allowed_host(file_url) or not robots.can_fetch(UA, file_url):
        return None, "robots_or_host_blocked", None
    try:
        with session.get(file_url, timeout=timeout, stream=True, allow_redirects=True, headers={"Accept":"application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/octet-stream,*/*"}) as resp:
            time.sleep(delay)
            if resp.status_code != 200: return None, f"http_{resp.status_code}", None
            final = resp.url
            if not allowed_host(final) or not robots.can_fetch(UA, final): return None, "redirect_host_or_robots_blocked", None
            ctype = resp.headers.get("Content-Type", "").split(";",1)[0].strip().lower()
            ext = os.path.splitext(urlparse(final).path)[1].lower()
            if ext not in FILE_EXTS: ext = MIME_EXTS.get(ctype, "")
            if not ext: return None, f"unsupported_content_type:{ctype}", None
            length = resp.headers.get("Content-Length")
            if length and int(length) > max_bytes: return None, "file_too_large", None
            os.makedirs(out_dir, exist_ok=True)
            digest = hashlib.sha256(file_url.encode()).hexdigest()
            filename = digest + ext
            path = os.path.join(out_dir, filename)
            h = hashlib.sha256(); total = 0
            with open(path + ".part", "wb") as f:
                for chunk in resp.iter_content(64 * 1024):
                    if not chunk: continue
                    total += len(chunk)
                    if total > max_bytes:
                        f.close(); os.remove(path + ".part")
                        return None, "file_too_large", None
                    h.update(chunk); f.write(chunk)
            os.replace(path + ".part", path)
            return filename, "downloaded", h.hexdigest()
    except requests.RequestException as exc:
        return None, "download_error:" + str(exc)[:160], None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="https://thi247.com/")
    ap.add_argument("--max-pages", type=int, default=100)
    ap.add_argument("--delay", type=float, default=2.0)
    ap.add_argument("--out", default="data/catalog.jsonl")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--download-files", action="store_true", help="Download direct document links that robots.txt allows")
    ap.add_argument("--resources-dir", default="public/resources")
    ap.add_argument("--max-file-mb", type=int, default=20)
    args = ap.parse_args()
    if args.max_pages < 1 or args.max_pages > 5000: ap.error("--max-pages must be between 1 and 5000")
    if args.delay < 1: ap.error("--delay must be >= 1 second")
    if args.max_file_mb < 1 or args.max_file_mb > 100: ap.error("--max-file-mb must be 1..100")
    session = requests.Session(); session.headers.update({"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    start = normalize(args.start)
    if not start: ap.error("Start URL must be an HTTP(S) URL on thi247.com")
    robots = load_robots("https://thi247.com", session, UA)
    if not robots.can_fetch(UA, start): raise SystemExit(f"robots.txt disallows start URL: {start}")
    queue, seen, records = deque([start]), set(), []
    while queue and len(seen) < args.max_pages:
        url = queue.popleft()
        if url in seen: continue
        seen.add(url)
        if not robots.can_fetch(UA, url): print("ROBOTS_SKIP", url); continue
        try:
            resp = session.get(url, timeout=args.timeout, allow_redirects=True)
            time.sleep(args.delay)
        except requests.RequestException as exc: print("FETCH_ERROR", url, str(exc)); continue
        final_url = normalize(resp.url)
        if not final_url or resp.status_code != 200: print("HTTP_SKIP", resp.status_code, url); continue
        if "text/html" not in resp.headers.get("Content-Type", "").lower(): continue
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        canonical_tag = soup.find("link", rel=lambda v: v and "canonical" in v)
        canonical = normalize(urljoin(final_url, canonical_tag.get("href"))) if canonical_tag and canonical_tag.get("href") else final_url
        desc_tag = soup.find("meta", attrs={"name": "description"})
        main_text = soup.find("main") or soup.find("article") or soup.body or soup
        description = (desc_tag.get("content", "").strip() if desc_tag else "") or main_text.get_text(" ", strip=True)[:500]
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest(); path = urlparse(final_url).path.lower()
        resource_type = "textbook" if "sach-giao-khoa" in path else ("exam" if any(s in path for s in ("de-thi", "de-kiem-tra", "thi-thu")) else "article")
        records.append({"id":digest,"title":title[:300],"source_url":final_url,"canonical_url":canonical,"domain":urlparse(final_url).hostname,"resource_type":resource_type,"grade":None,"subject":None,"topic":None,"description":description[:800],"published_at":None,"discovered_at":now(),"checked_at":now(),"http_status":resp.status_code,"rights_status":"unknown","rights_evidence_url":None,"license":None,"permission_notes":"Download only from direct links allowed by robots.txt; redistribution rights remain unverified.","content_stored":False,"download_url":None,"local_file":None,"content_hash":None,"crawl_status":"indexed","source_title":"THI247","tags":[]})
        for a in soup.find_all("a", href=True):
            absolute = urljoin(final_url, a["href"].strip())
            if not allowed_host(absolute): continue
            if direct_file_candidate(absolute, a):
                file_ext = os.path.splitext(urlparse(absolute).path)[1].lower()
                # Only follow likely document links; actual MIME is checked after fetching.
                if args.download_files:
                    local_name, status, content_hash = download_resource(session, robots, absolute, args.resources_dir, args.delay, args.timeout, args.max_file_mb*1024*1024)
                    if status == "downloaded":
                        file_title = a.get_text(" ", strip=True) or title or "Tài liệu tải về"
                        records.append({"id":hashlib.sha256(absolute.encode()).hexdigest(),"title":file_title[:300],"source_url":final_url,"canonical_url":absolute,"domain":urlparse(final_url).hostname,"resource_type":resource_type,"grade":None,"subject":None,"topic":None,"description":description[:500],"published_at":None,"discovered_at":now(),"checked_at":now(),"http_status":200,"rights_status":"unknown","rights_evidence_url":None,"license":None,"permission_notes":"Downloaded from a public direct link; redistribution rights not verified.","content_stored":True,"download_url":absolute,"local_file":"/resources/"+local_name,"content_hash":content_hash,"crawl_status":"downloaded","source_title":"THI247","tags":[]})
                    else: print("FILE_SKIP", status, absolute)
            candidate = normalize(absolute)
            if candidate and candidate not in seen and candidate not in queue and robots.can_fetch(UA, candidate): queue.append(candidate)
        print(f"[{len(seen)}/{args.max_pages}] {resp.status_code} {final_url}")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for item in records: f.write(json.dumps(item, ensure_ascii=False) + "\n")
    downloaded = sum(1 for x in records if x.get("content_stored"))
    print(f"Wrote {len(records)} records; downloaded {downloaded} resource files")
if __name__ == "__main__": main()
