"""Show the row count and columns of a CSV or CKAN datastore JSON download."""
import argparse,csv,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("source",type=Path);a=p.parse_args()
with a.source.open(encoding="utf-8-sig",newline="") as h:
    first=h.read(1);h.seek(0);rows=json.load(h).get("result",{}).get("records",[]) if first=="{" else list(csv.DictReader(h))
print("rows:",len(rows));print("columns:");print("\n".join(rows[0].keys()) if rows else "(none)")
