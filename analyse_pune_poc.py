"""Pune-only ARV/building screening analysis; Python standard library only."""
import argparse,csv,math,random,statistics
from pathlib import Path

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as h:return list(csv.DictReader(h))
def number(v):
    try:return float(str(v).replace(',','').replace('₹',''))
    except:raise ValueError('Non-numeric required value: '+str(v))
def rank(values):
    order=sorted(range(len(values)),key=values.__getitem__);out=[0.0]*len(values);i=0
    while i<len(order):
        j=i
        while j+1<len(order) and values[order[j+1]]==values[order[i]]:j+=1
        for k in range(i,j+1):out[order[k]]=(i+j+2)/2
        i=j+1
    return out
def corr(x,y):
    mx=sum(x)/len(x);my=sum(y)/len(y);d=math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
    if not d:raise ValueError('Constant variable prevents correlation')
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/d
def fit(x,y):
    mx=sum(x)/len(x);my=sum(y)/len(y);ss=sum((a-mx)**2 for a in x)
    if not ss:raise ValueError('Constant predictor prevents regression')
    slope=sum((a-mx)*(b-my) for a,b in zip(x,y))/ss;intercept=my-slope*mx
    pred=[intercept+slope*a for a in x];r2=1-sum((a-b)**2 for a,b in zip(y,pred))/sum((a-my)**2 for a in y)
    return intercept,slope,r2,pred
def bootstrap_rho(x,y,n=2000):
    rng=random.Random(20261116);values=[]
    for _ in range(n):
        idx=[rng.randrange(len(x)) for _ in x]
        try:values.append(corr(rank([x[i] for i in idx]),rank([y[i] for i in idx])))
        except ValueError:raise ValueError('Bootstrap sample has no variation; stop and inspect data')
    values.sort();return values[49],values[1949]
def shoelace(coords,lat0):
    # Equirectangular local approximation adequate for a plausibility bound.
    points=[((lon*111320*math.cos(math.radians(lat0))),lat*110540) for lon,lat in coords]
    return abs(sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))/2)
def rings(geometry):
    if geometry['type']=='Polygon':return geometry['coordinates']
    if geometry['type']=='MultiPolygon':return [r for p in geometry['coordinates'] for r in p]
    raise ValueError('Unsupported geometry type: '+geometry['type'])
def svg_map(features,residuals,out):
    allpts=[p for f in features for r in rings(f['geometry']) for p in r];xs=[p[0] for p in allpts];ys=[p[1] for p in allpts];w,h,pad=900,700,35
    def xy(p):return (pad+(p[0]-min(xs))/(max(xs)-min(xs))*(w-2*pad),h-pad-(p[1]-min(ys))/(max(ys)-min(ys))*(h-2*pad))
    lo,hi=min(residuals.values()),max(residuals.values())
    def color(v):
        t=.5 if hi==lo else (v-lo)/(hi-lo);return '#%02x%02x%02x'%(int(49+205*t),int(130-85*t),int(189-149*t))
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="700"><rect width="100%" height="100%" fill="white"/><text x="25" y="28" font-family="Arial" font-size="18" font-weight="bold">Pune screening priority (hypothesis): LOO ARV residual</text>']
    for f in features:
        ward=str(f['properties']['name'])[11:13];fill=color(residuals[ward])
        for ring in rings(f['geometry']):parts.append('<path d="M '+' L '.join(f'{xy(p)[0]:.1f},{xy(p)[1]:.1f}' for p in ring)+' Z" fill="'+fill+'" stroke="white" stroke-width="1"/>')
    parts.append('<text x="25" y="680" font-family="Arial" font-size="12">Blue: lower relative ARV; orange: higher relative ARV</text></svg>');out.write_text(''.join(parts))
def scatter(rows,out):
    w,h,p=900,650,80;x=[r['log_built_area'] for r in rows];y=[r['log_arv'] for r in rows];mnx,mxx=min(x),max(x);mny,mxy=min(y),max(y)
    def xy(a,b):return p+(a-mnx)/(mxx-mnx)*(w-2*p),h-p-(b-mny)/(mxy-mny)*(h-2*p)
    s=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="650"><rect width="100%" height="100%" fill="white"/><text x="25" y="28" font-family="Arial" font-size="18" font-weight="bold">Log total ARV versus log built area</text><line x1="80" y1="570" x2="820" y2="570" stroke="black"/><line x1="80" y1="570" x2="80" y2="60" stroke="black"/>']
    for r in rows:
        a,b=xy(r['log_built_area'],r['log_arv']);s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="5" fill="#2171b5"/><text x="{a+7:.1f}" y="{b-6:.1f}" font-family="Arial" font-size="11">{r["ward_id"]}</text>')
    s.append('<text x="390" y="625" font-family="Arial">log built area →</text><text x="20" y="360" font-family="Arial" transform="rotate(-90 20 360)">log total ARV →</text></svg>');out.write_text(''.join(s))
def main():
    p=argparse.ArgumentParser();p.add_argument('--admin',type=Path,default=Path('data/admin_wards.csv'));p.add_argument('--buildings',type=Path,default=Path('data/ward_buildings.csv'));p.add_argument('--geojson',type=Path,default=Path('data/raw/pune_wards/GeoData/pune-admin-wards.geojson'));p.add_argument('--out',type=Path,default=Path('outputs/pune'));a=p.parse_args()
    tax={r['ward_id']:r for r in read(a.admin)};building={r['ward_id']:r for r in read(a.buildings)};gj=__import__('json').load(a.geojson.open(encoding='utf-8-sig'));features=gj['features'];poly={str(f['properties']['name'])[11:13] for f in features}
    if len(tax)!=15 or len(building)!=15 or len(poly)!=15 or set(tax)!=set(building) or set(tax)!=poly:raise SystemExit(f'STOP: ward match failure. tax={len(tax)}, buildings={len(building)}, polygons={len(poly)}, unmatched_tax={sorted(set(tax)-set(building))}, unmatched_buildings={sorted(set(building)-set(tax))}')
    rows=[]
    for ward in sorted(tax):
        area=number(building[ward]['built_area_m2']);volume=number(building[ward]['volume_m3']);arv=number(tax[ward]['total_arv'])
        if area<=0 or volume<=0:raise SystemExit('STOP: zero or negative building measure in ward '+ward)
        rows.append({'ward_id':ward,'ward_name':tax[ward]['ward_name'],'built_area_m2':area,'volume_m3':volume,'total_arv':arv,'log_built_area':math.log(area),'log_volume':math.log(volume),'log_arv':math.log(arv)})
    lat0=statistics.mean(p[1] for f in features for r in rings(f['geometry']) for p in r);city_area=sum(shoelace(r,lat0) for f in features for r in rings(f['geometry']));total_area=sum(r['built_area_m2'] for r in rows)
    if total_area>city_area:raise SystemExit(f'STOP: total built area {total_area:,.0f} exceeds polygon area {city_area:,.0f}')
    rho_area=corr(rank([r['log_built_area'] for r in rows]),rank([r['log_arv'] for r in rows]));rho_volume=corr(rank([r['log_volume'] for r in rows]),rank([r['log_arv'] for r in rows]));ia,sa,r2a,pred=fit([r['log_built_area'] for r in rows],[r['log_arv'] for r in rows]);iv,sv,r2v,_=fit([r['log_volume'] for r in rows],[r['log_arv'] for r in rows]);ci=bootstrap_rho([r['log_built_area'] for r in rows],[r['log_arv'] for r in rows])
    for i,r in enumerate(rows):
        leave=[q for j,q in enumerate(rows) if j!=i];intercept,slope,_,_=fit([q['log_built_area'] for q in leave],[q['log_arv'] for q in leave]);r['loo_log_arv_residual']=r['log_arv']-(intercept+slope*r['log_built_area'])
    rows.sort(key=lambda r:r['loo_log_arv_residual'])
    for i,r in enumerate(rows,1):r['screening_priority_hypothesis_rank']=i
    a.out.mkdir(parents=True,exist_ok=True)
    cols=['screening_priority_hypothesis_rank','ward_id','ward_name','built_area_m2','volume_m3','total_arv','loo_log_arv_residual']
    with (a.out/'results_table.csv').open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=cols);w.writeheader();w.writerows([{k:r[k] for k in cols} for r in rows])
    residuals={r['ward_id']:r['loo_log_arv_residual'] for r in rows};svg_map(features,residuals,a.out/'ward_map.svg');scatter(rows,a.out/'scatter.svg')
    low='YES — rho below 0.7; state this plainly.' if rho_area<.7 else 'NO'
    report=f'''PUNE SCREENING RESULTS (HYPOTHESIS)\n\nn: 15\nWard match check: 15 tax rows, 15 building rows, 15 polygons — PASS\nZero-building check: PASS\nTotal built area: {total_area:,.0f} m²\nPolygon area (local approximation): {city_area:,.0f} m²\nBuilt-area share of polygon area: {total_area/city_area:.3%}\n\nlog(total ARV) ~ log(built area)\nSpearman rho: {rho_area:.3f}\nR-squared: {r2a:.3f}\n95% bootstrap interval for rho (2,000 resamples): [{ci[0]:.3f}, {ci[1]:.3f}]\n\nlog(total ARV) ~ log(volume)\nSpearman rho: {rho_volume:.3f}\nR-squared: {r2v:.3f}\n\nIs built-area rho below 0.7? {low}\n\nRanking label: screening priority (hypothesis). Lower leave-one-out residual means lower ARV relative to built area.\n'''
    (a.out/'results.txt').write_text(report);(a.out/'LIMITATIONS.md').write_text('# Limitations\n\n- n=15 administrative wards.\n- Building measures are footprint/presence-based proxies from modelled satellite layers.\n- Location value differences are not controlled.\n- The 2018–2019 satellite proxy is adjacent to, rather than identical to, FY2017–18.\n- No ground truth is included.\n')
    print(report)
if __name__=='__main__':main()
