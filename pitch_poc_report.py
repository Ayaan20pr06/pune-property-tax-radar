"""Create an evidence-bounded, pitch-ready operational POC summary."""
import csv
from pathlib import Path

ROOT=Path('.')
def read(path):
    with path.open(encoding='utf-8-sig',newline='') as h:return list(csv.DictReader(h))
def n(v): return float(str(v).replace(',','').replace('₹',''))
def main():
    tax=read(ROOT/'data/wards.csv');admin=read(ROOT/'data/admin_wards.csv');building=read(ROOT/'data/ward_buildings.csv');results=read(ROOT/'outputs/pune/results_table.csv')
    ids={r['ward_id'] for r in admin};bids={r['ward_id'] for r in building};rids={r['ward_id'] for r in results}
    if len(tax)!=24 or len(admin)!=15 or len(building)!=15 or ids!=bids or ids!=rids:raise SystemExit('STOP: POC coverage check failed; do not create a pitch summary.')
    fields=['built_properties','total_arv','property_tax_demand_inr']
    for field in fields:
        source=sum(n(r[field]) for r in tax);aggregated=sum(n(r[field]) for r in admin)
        if abs(source-aggregated)>max(1,abs(source)*1e-9):raise SystemExit('STOP: POC total mismatch for '+field)
    if any(n(r['built_area_m2'])<=0 or n(r['volume_m3'])<=0 for r in building):raise SystemExit('STOP: non-positive building feature found.')
    out=ROOT/'outputs/pune/pitch_poc_summary.md'
    out.write_text(f'''# Pune operational POC\n\n## What was built\n\nA reproducible workflow that turns historical municipal tax records and satellite building layers into a ward-level screening queue.\n\n- {len(tax)}/24 Sampark tax rows mapped into {len(admin)}/15 historical administrative wards.\n- 15/15 administrative wards matched to satellite building-area and volume measures.\n- 15/15 wards have positive building measures.\n- Tax-roll totals reconcile after aggregation: built properties {sum(n(r['built_properties']) for r in admin):,.0f}; total ARV ₹{sum(n(r['total_arv']) for r in admin):,.0f}; annual demand ₹{sum(n(r['property_tax_demand_inr']) for r in admin):,.0f}.\n- The workflow produces a ranked, human-review queue rather than an automated assessment.\n\n## What the Pune run says\n\nThe data-integration workflow is operational. The small Pune sample does **not** establish that built form alone can rank tax-base gaps: n=15, built-area Spearman rho=0.300, and location value differences are not controlled.\n\n## Product thesis to test next\n\nWith a larger multi-city training set, a location-aware expected-ARV baseline, and independently observed inspection outcomes, the same workflow can prioritize field checks where observed value is low relative to built form and local market context.\n\n## Honest pitch line\n\n“Instead of commissioning a city-wide resurvey before knowing where to look, municipalities can begin with a repeatable screening layer that directs scarce inspection capacity. Pune demonstrates the end-to-end data and decision workflow; the next phase measures ranking quality across cities and inspection outcomes.”\n\n## Do not claim\n\n- That Pune’s current ranking identifies omissions.\n- That residuals represent non-compliance or tax evasion.\n- That 15 wards establish a general relationship.\n''')
    print(out.read_text())
if __name__=='__main__':main()
