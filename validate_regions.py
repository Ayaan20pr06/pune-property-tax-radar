"""Retrospective validation of ward rankings against a later regional survey."""
import argparse,csv,math
from pathlib import Path
def read(p):
    with p.open(encoding="utf-8-sig",newline="") as h:return list(csv.DictReader(h))
def num(x):
    try:return float(str(x).replace(",","").replace("₹",""))
    except:return None
def ranks(v):
    order=sorted(range(len(v)),key=v.__getitem__);out=[0]*len(v);i=0
    while i<len(order):
        j=i
        while j+1<len(order) and v[order[j+1]]==v[order[i]]:j+=1
        for k in range(i,j+1):out[order[k]]=(i+j+2)/2
        i=j+1
    return out
def pearson(x,y):
    mx=sum(x)/len(x);my=sum(y)/len(y);d=math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y));return sum((a-mx)*(b-my) for a,b in zip(x,y))/d if d else None
def main():
    p=argparse.ArgumentParser();p.add_argument("--ranking",type=Path,default=Path("outputs/ward_inspection_ranking.csv"));p.add_argument("--ward-to-region",type=Path,required=True);p.add_argument("--survey",type=Path,required=True);p.add_argument("--out",type=Path,default=Path("outputs/region_validation.csv"));a=p.parse_args()
    rank=read(a.ranking);mapping={r["ward_id"]:r["region"] for r in read(a.ward_to_region)};survey={r["region"]:r for r in read(a.survey)}
    absent=[r["ward_id"] for r in rank if r["ward_id"] not in mapping]
    if absent:raise SystemExit("STOP: missing region mapping for: "+", ".join(absent[:20]))
    g={}
    for r in rank:g.setdefault(mapping[r["ward_id"]],[]).append(num(r["estimated_demand_gap_inr"]) or 0)
    rows=[]
    for region,gaps in g.items():
        if region not in survey:raise SystemExit("STOP: no survey row for region: "+region)
        s=survey[region]; rows.append({"region":region,"ranked_estimated_gap_inr":sum(gaps),"unregistered_properties":num(s.get("unregistered_properties")),"estimated_recovery_inr":num(s.get("estimated_recovery_inr"))})
    usable=[r for r in rows if r["unregistered_properties"] is not None]
    rho=pearson(ranks([r["ranked_estimated_gap_inr"] for r in usable]),ranks([r["unregistered_properties"] for r in usable])) if len(usable)>=3 else None
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("w",newline="") as h:w=csv.DictWriter(h,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    print(f"Regions compared: {len(usable)}")
    print("Spearman rank correlation (estimated gap vs later unregistered-property count):", "not enough regions" if rho is None else f"{rho:.3f}")
    print("Interpretation: positive is necessary but not sufficient; report the value, source, geography mapping, and failures.")
if __name__=="__main__":main()
