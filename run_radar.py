"""Dependency-free ward property-tax gap radar. Use --demo, then real CSVs."""
import argparse, csv, math, random, statistics, sys
from pathlib import Path

F = ["built_volume_m3","building_count","mean_height_m","median_footprint_m2","recent_new_building_share"]
def num(x, default=None):
    try: return float(x)
    except (TypeError, ValueError): return default

def demo(seed=42):
    rng=random.Random(seed); bs=[]; ws=[]
    for w in range(1,61):
        wid=f"W{w:03d}"; n=rng.randint(180,520); vol=0
        for i in range(n):
            area=max(25,rng.lognormvariate(4.3,.62)); h=min(55,max(3,rng.gammavariate(2.1,4.3))); year=rng.randint(1980,2024); vol+=area*h
            bs.append(dict(ward_id=wid,building_id=f"{wid}-B{i:04d}",footprint_m2=area,height_m=h,construction_year=year))
        # Synthetic city: volume is deliberately a strong but imperfect tax-base signal.
        potential=200000+3.0*vol+rng.gauss(0,50000); gap=.03+(rng.uniform(.22,.48) if w%7==0 else rng.uniform(0,.06)); demand=max(100000,potential*(1-gap))
        ws.append(dict(ward_id=wid,ward_name=f"Ward {w}",properties_on_roll=int(n*(1-gap)),property_tax_demand_inr=demand,property_tax_collected_inr=demand*rng.uniform(.68,.91),survey_gap_fraction=gap))
    return bs,ws

def read(path):
    with path.open(newline="",encoding="utf-8-sig") as h: return list(csv.DictReader(h))
def inputs(demo_mode, data_dir):
    if demo_mode: return demo()
    a,b=data_dir/"buildings.csv",data_dir/"wards.csv"
    c=data_dir/"ward_features.csv"
    if c.exists() and b.exists(): return [],read(b),read(c)
    if not a.exists() or not b.exists(): raise ValueError("Provide data/buildings.csv + data/wards.csv, or data/ward_features.csv + data/wards.csv")
    return read(a),read(b)

def features(bs, asof):
    req={"ward_id","building_id","footprint_m2","height_m"}
    if not bs or not req <= set(bs[0]): raise ValueError("buildings.csv requires: ward_id, building_id, footprint_m2, height_m")
    g={}
    for r in bs:
        a,h=num(r.get("footprint_m2")),num(r.get("height_m")); wid=r.get("ward_id")
        if not wid or a is None or h is None or a<=0 or h<=0: continue
        z=g.setdefault(wid,[set(),[],[],[],[]]); z[0].add(r["building_id"]); z[1].append(a*h); z[2].append(h); z[3].append(a); z[4].append(int(num(r.get("construction_year"),0)>=asof-5))
    return {k:dict(built_volume_m3=sum(v[1]),building_count=len(v[0]),mean_height_m=statistics.mean(v[2]),median_footprint_m2=statistics.median(v[3]),recent_new_building_share=statistics.mean(v[4])) for k,v in g.items()}

def solve(a,b):
    n=len(b); z=[a[i][:]+[b[i]] for i in range(n)]
    for j in range(n):
        p=max(range(j,n),key=lambda i:abs(z[i][j]))
        if abs(z[p][j])<1e-12: raise ValueError("Model matrix singular; add more varied wards")
        z[j],z[p]=z[p],z[j]; q=z[j][j]; z[j]=[x/q for x in z[j]]
        for i in range(n):
            if i!=j:
                q=z[i][j]; z[i]=[z[i][k]-q*z[j][k] for k in range(n+1)]
    return [z[i][-1] for i in range(n)]

def predict(train,test):
    means=[statistics.mean(math.log1p(r[k]) for r in train) for k in F]; scales=[max(1e-9,statistics.pstdev(math.log1p(r[k]) for r in train)) for k in F]
    def row(r): return [1]+[(math.log1p(r[k])-means[i])/scales[i] for i,k in enumerate(F)]
    x=[row(r) for r in train]; y=[math.log1p(r["property_tax_demand_inr"]) for r in train]; n=len(F)+1
    a=[[sum(q[i]*q[j] for q in x)+(.25 if i==j and i else 0) for j in range(n)] for i in range(n)]; b=[sum(q[i]*v for q,v in zip(x,y)) for i in range(n)]
    c=solve(a,b); return [sum(v*q for v,q in zip(c,row(r))) for r in test]

def pct(v):
    out=[0]*len(v)
    for rank,i in enumerate(sorted(range(len(v)),key=v.__getitem__),1): out[i]=rank/len(v)
    return out
def auc(y,s):
    p=[x for x,l in zip(s,y) if l]; n=[x for x,l in zip(s,y) if not l]
    return None if not p or not n else sum(1 if a>b else .5 if a==b else 0 for a in p for b in n)/(len(p)*len(n))

def run(bs,ws,asof,precomputed=None):
    req={"ward_id","ward_name","properties_on_roll","property_tax_demand_inr"}
    if not ws or not req <= set(ws[0]): raise ValueError("wards.csv requires: ward_id, ward_name, properties_on_roll, property_tax_demand_inr")
    if precomputed is None:
        ft=features(bs,asof)
    else:
        if not precomputed or not {"ward_id",*F} <= set(precomputed[0]): raise ValueError("ward_features.csv requires ward_id plus: "+", ".join(F))
        ft={r["ward_id"]:{k:num(r.get(k)) for k in F} for r in precomputed}
        if any(any(v is None or v < 0 for v in r.values()) for r in ft.values()): raise ValueError("ward_features.csv has missing or negative feature values")
    data=[]
    for w in ws:
        d,r=num(w.get("property_tax_demand_inr")),num(w.get("properties_on_roll")); wid=w.get("ward_id")
        if wid in ft and d and d>0 and r is not None: z=dict(w);z.update(ft[wid]);z["property_tax_demand_inr"]=d;z["properties_on_roll"]=r;data.append(z)
    if len(data)<12: raise ValueError(f"Need at least 12 matched wards; found {len(data)}")
    order=list(range(len(data)));random.Random(42).shuffle(order); preds=[None]*len(data); folds=min(5,len(data))
    for fold in range(folds):
        test=[i for j,i in enumerate(order) if j%folds==fold]; train=[i for i in range(len(data)) if i not in test]
        for i,x in zip(test,predict([data[j] for j in train],[data[j] for j in test])): preds[i]=math.expm1(x)
    logs=[math.log1p(r["property_tax_demand_inr"]) for r in data]; mu=statistics.mean(logs)
    for r,p in zip(data,preds): r["expected_tax_demand_inr"]=p;r["estimated_demand_gap_inr"]=max(0,p-r["property_tax_demand_inr"]);r["gap_pct_of_expected"]=r["estimated_demand_gap_inr"]/max(1,p);r["buildings_per_roll_property"]=r["building_count"]/max(1,r["properties_on_roll"])
    x,y=pct([r["gap_pct_of_expected"] for r in data]),pct([r["buildings_per_roll_property"] for r in data])
    for r,a,b in zip(data,x,y): r["inspect_priority_score"]=100*(.75*a+.25*b)
    data.sort(key=lambda r:r["inspect_priority_score"],reverse=True)
    for i,r in enumerate(data,1):r["inspect_priority_rank"]=i
    m=dict(wards_modelled=len(data),cv_r2=1-sum((a-math.log1p(b))**2 for a,b in zip(logs,preds))/sum((a-mu)**2 for a in logs),cv_mae_inr=sum(abs(r["property_tax_demand_inr"]-r["expected_tax_demand_inr"]) for r in data)/len(data),total_estimated_gap_inr=sum(r["estimated_demand_gap_inr"] for r in data))
    lab=[num(r.get("survey_gap_fraction"))>=.18 for r in data if num(r.get("survey_gap_fraction")) is not None];scores=[r["inspect_priority_score"] for r in data if num(r.get("survey_gap_fraction")) is not None]
    if len(set(lab))==2:m["survey_gap_auc"]=auc(lab,scores)
    return data,m

def money(x):return "₹{:,.0f}".format(x)
def charts(d,o):
    W,H,M=840,560,70; mx=max(max(r["property_tax_demand_inr"],r["expected_tax_demand_inr"]) for r in d);s=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="100%" height="100%" fill="white"/><text x="30" y="30" font-family="Arial" font-size="18" font-weight="bold">Recorded versus expected property-tax demand</text><line x1="{M}" y1="{H-M}" x2="{W-M}" y2="{H-M}" stroke="black"/><line x1="{M}" y1="{H-M}" x2="{M}" y2="{M}" stroke="black"/>'
    for r in d:
        x=M+(W-2*M)*r["property_tax_demand_inr"]/mx;y=H-M-(H-2*M)*r["expected_tax_demand_inr"]/mx;c="#d55e00" if r["inspect_priority_rank"]<=10 else "#4e79a7";s+=f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{c}"/>'
    (o/"demand_vs_expected.svg").write_text(s+"</svg>");top=list(reversed(d[:12]));s=f'<svg xmlns="http://www.w3.org/2000/svg" width="840" height="560"><rect width="100%" height="100%" fill="white"/><text x="30" y="30" font-family="Arial" font-size="18" font-weight="bold">Start field verification in these wards</text>'
    for i,r in enumerate(top):
        y=65+i*38;w=550*r["inspect_priority_score"]/100;s+=f'<text x="30" y="{y+18}" font-family="Arial" font-size="13">{r["ward_name"]}</text><rect x="190" y="{y}" width="{w:.1f}" height="24" fill="#d55e00"/><text x="{200+w:.1f}" y="{y+18}" font-family="Arial" font-size="12">{r["inspect_priority_score"]:.1f}</text>'
    (o/"top_wards.svg").write_text(s+"</svg>")

def output(d,m,o):
    o.mkdir(parents=True,exist_ok=True);cols=["inspect_priority_rank","ward_id","ward_name","inspect_priority_score","building_count","properties_on_roll","built_volume_m3","property_tax_demand_inr","expected_tax_demand_inr","estimated_demand_gap_inr","gap_pct_of_expected","buildings_per_roll_property"]
    with (o/"ward_inspection_ranking.csv").open("w",newline="") as h: z=csv.DictWriter(h,fieldnames=cols);z.writeheader();z.writerows([{k:r[k] for k in cols} for r in d])
    lines=["PROPERTY-TAX GAP RADAR — PROOF-OF-CONCEPT RESULTS","",f"Wards modelled: {m['wards_modelled']}",f"Cross-validated R² (log demand): {m['cv_r2']:.3f}",f"Cross-validated MAE: {money(m['cv_mae_inr'])}",f"Estimated aggregate demand gap: {money(m['total_estimated_gap_inr'])}"]
    if "survey_gap_auc" in m:lines.append(f"Validation AUC against independently surveyed gap label: {m['survey_gap_auc']:.3f}")
    lines += ["","Top wards to inspect first:"]+[f"{r['inspect_priority_rank']:>2}. {r['ward_name']} — estimated gap {money(r['estimated_demand_gap_inr'])}; score {r['inspect_priority_score']:.1f}/100" for r in d[:10]];(o/"summary.txt").write_text("\n".join(lines)+"\n");charts(d,o)

def main():
    p=argparse.ArgumentParser();p.add_argument("--demo",action="store_true");p.add_argument("--data-dir",type=Path,default=Path("data"));p.add_argument("--output-dir",type=Path,default=Path("outputs"));p.add_argument("--as-of-year",type=int,default=2025);a=p.parse_args()
    try:
        inp=inputs(a.demo,a.data_dir)
        d,m=run(inp[0],inp[1],a.as_of_year,inp[2] if len(inp)==3 else None);output(d,m,a.output_dir)
    except ValueError as e:print("ERROR:",e,file=sys.stderr);return 2
    print((a.output_dir/"summary.txt").read_text());print("Saved:",a.output_dir/"ward_inspection_ranking.csv")
if __name__=="__main__":main()
