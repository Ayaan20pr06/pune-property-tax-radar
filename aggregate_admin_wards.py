"""Aggregate Pune Sampark tax rows into verified administrative wards."""
import argparse,csv
from pathlib import Path
def read(p):
    with p.open(encoding="utf-8-sig",newline="") as h:return list(csv.DictReader(h))
def main():
    p=argparse.ArgumentParser();p.add_argument("--wards",type=Path,default=Path("data/wards.csv"));p.add_argument("--lookup",type=Path,required=True);p.add_argument("--output",type=Path,default=Path("data/admin_wards.csv"));a=p.parse_args()
    rows=read(a.wards); lookup=read(a.lookup)
    if not lookup or not {"ward_id","admin_ward_id","admin_ward_name"} <= set(lookup[0]):raise SystemExit("Lookup needs ward_id, admin_ward_id, admin_ward_name")
    m={r["ward_id"]:r for r in lookup};missing=[r["ward_id"] for r in rows if r["ward_id"] not in m]
    if missing:raise SystemExit("STOP: missing mappings: "+", ".join(missing))
    extras=set(m)-{r["ward_id"] for r in rows}
    if extras:raise SystemExit("STOP: mapping contains tax-ward IDs absent from source: "+", ".join(sorted(extras)))
    sums=["total_assessments_count","open_plot_count","built_properties","properties_on_roll","total_arv","property_tax_demand_inr","property_tax_collected_inr"]
    groups={}
    for r in rows:
        q=m[r["ward_id"]];g=groups.setdefault(q["admin_ward_id"],{"ward_id":q["admin_ward_id"],"ward_name":q["admin_ward_name"],**{x:0.0 for x in sums}})
        for x in sums:g[x]+=float(r[x] or 0)
    out=list(groups.values())
    for r in out:
        for x in ["total_assessments_count","open_plot_count","built_properties","properties_on_roll"]:r[x]=round(r[x])
    for x in sums:
        source=sum(float(r[x] or 0) for r in rows); aggregated=sum(float(r[x] or 0) for r in out)
        if abs(source-aggregated) > max(1, abs(source)*1e-9):
            raise SystemExit(f"STOP: aggregation total mismatch for {x}: source={source}, aggregated={aggregated}")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("w",newline="") as h:w=csv.DictWriter(h,fieldnames=out[0].keys());w.writeheader();w.writerows(out)
    print(f"AGGREGATION CHECK OK — {len(rows)} source rows mapped exactly once into {len(out)} administrative wards.")
    for x in sums: print(f"TOTAL CHECK OK — {x}: {sum(float(r[x] or 0) for r in out):,.2f}")
if __name__=="__main__":main()
