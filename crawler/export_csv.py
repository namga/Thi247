import csv, json, sys
src = sys.argv[1] if len(sys.argv)>1 else "data/catalog.jsonl"
dst = sys.argv[2] if len(sys.argv)>2 else "data/catalog.csv"
rows=[]
with open(src,encoding="utf-8") as f:
    for line in f:
        if line.strip(): rows.append(json.loads(line))
fields=["id","title","source_url","canonical_url","resource_type","grade","subject","description","rights_status","license","rights_evidence_url","checked_at","crawl_status"]
with open(dst,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print(f"Exported {len(rows)} rows to {dst}")
