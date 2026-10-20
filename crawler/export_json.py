import json, sys
from pathlib import Path
src = sys.argv[1] if len(sys.argv)>1 else "data/catalog.jsonl"
dst = sys.argv[2] if len(sys.argv)>2 else "public/data/catalog.json"
seed_path = Path("public/data/seed-catalog.json")
rows=[]
if seed_path.exists():
    rows.extend(json.loads(seed_path.read_text(encoding="utf-8")))
if Path(src).exists():
    with open(src, encoding="utf-8") as f:
        for line in f:
            if line.strip(): rows.append(json.loads(line))
# Deduplicate by canonical URL, preferring a crawled record when available.
by_url = {}
for row in rows:
    key = row.get("canonical_url") or row.get("source_url") or row.get("id")
    if key in by_url and by_url[key].get("crawl_status") != "seed_metadata":
        continue
    by_url[key] = row
rows = list(by_url.values())
with open(dst, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(f"Exported {len(rows)} records (including seed metadata) to {dst}")
