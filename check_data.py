"""Fail-fast checks before modelling: joins, totals, and population correlation."""
import argparse,csv,math,sys
from pathlib import Path
def read(p):
    with p.open(encoding="utf-8-sig",newline="") as h:return list(csv.DictReader(h))
def num(x):
    try:return float(str(x).replace(",","").replace("₹",""))
    except:return None
def corr(x,y):
    mx=sum(x)/len(x);my=sum(y)/len(y);d=math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y));return sum((a-mx)*(b-my) for a,b in zip(x,y))/d if d else None
def main():
    p=argparse.ArgumentParser();p.add_argument("--data-dir",type=Path,default=Path("data"));p.add_argument("--reported-demand",type=float);p.add_argument("--population",type=Path);a=p.parse_args();d=a.data_dir
    if not (d/"wards.csv").exists(): raise SystemExit("Missing data/wards.csv. Run the city preparation step first.")
    if not (d/"ward_features.csv").exists() and not (d/"buildings.csv").exists(): raise SystemExit("Missing data/ward_features.csv or data/buildings.csv.")
    wards=read(d/"wards.csv"); feat=read(d/"ward_features.csv") if (d/"ward_features.csv").exists() else read(d/"buildings.csv")
    w={r["ward_id"] for r in wards};f={r["ward_id"] for r in feat}; orphan_w=sorted(w-f);orphan_f=sorted(f-w)
    print(f"WARD JOIN: tax wards={len(w)}, feature wards={len(f)}, unmatched tax={len(orphan_w)}, unmatched features={len(orphan_f)}")
    if orphan_w:print("Unmatched tax ward IDs:",", ".join(orphan_w[:20]))
    if orphan_f:print("Unmatched feature ward IDs:",", ".join(orphan_f[:20]))
    total=sum(num(r.get("property_tax_demand_inr")) or 0 for r in wards);print(f"DEMAND TOTAL: ₹{total:,.0f}")
    if a.reported_demand is not None:print(f"TOTAL CHECK: reported=₹{a.reported_demand:,.0f}; difference={100*(total-a.reported_demand)/a.reported_demand:.2f}%")
    if a.population:
        pop={r["ward_id"]:num(r.get("population")) for r in read(a.population)}
        pairs=[(num(r.get("building_count")),pop.get(r["ward_id"])) for r in feat if num(r.get("building_count")) is not None and pop.get(r["ward_id"]) is not None]
        print("BUILDINGS–POPULATION Pearson r:",f"{corr([x for x,y in pairs],[y for x,y in pairs]):.3f}" if len(pairs)>=3 else "not enough matched wards")
    if orphan_w or orphan_f:sys.exit("STOP: Fix ward-ID/boundary mismatches before modelling.")
if __name__=="__main__":main()
