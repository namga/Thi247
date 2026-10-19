import json, sys
src = sys.argv[1] if len(sys.argv)>1 else "data/catalog.jsonl"
dst = sys.argv[2] if len(sys.argv)>2 else "public/data/catalog.json"
rows=[]
with open(src, encoding="utf-8") as f:
    for line in f:
        if line.strip(): rows.append(json.loads(line))
with open(dst, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
    f.write("\\n")
print(f"Exported {len(rows)} records to {dst}")
