"""Turn the OpenCity Pune FY2017-18 CSV into the radar's wards.csv contract."""
import argparse, csv, json, re
from pathlib import Path

def money(x):
    x=re.sub(r"[^0-9.-]","",str(x or ""))
    return float(x) if x else None
def main():
    p=argparse.ArgumentParser();p.add_argument("source",type=Path);p.add_argument("--output",type=Path,default=Path("data/wards.csv"));a=p.parse_args()
    # CKAN's downloadable file may return 403, while its datastore API returns JSON.
    # Accept either format so the rest of the workflow stays unchanged.
    with a.source.open(encoding="utf-8-sig",newline="") as h:
        first=h.read(1);h.seek(0)
        rows=(json.load(h).get("result",{}).get("records",[]) if first=="{" else list(csv.DictReader(h)))
    need={"WARD/SAMPARK NAME","Total Count","Open Plot Count","Total ARV","ORIGINAL DEMAND 2017-18","COLLECTION 2017-18"}
    if not rows or not need <= set(rows[0]): raise SystemExit("Unexpected columns. Required: "+", ".join(sorted(need)))
    total_rows=[]; out=[]
    for r in rows:
        ward=r["WARD/SAMPARK NAME"].strip(); serial=str(r.get("SR NO", "")).strip().casefold(); demand=money(r["ORIGINAL DEMAND 2017-18"]); count=money(r["Total Count"]); collected=money(r["COLLECTION 2017-18"])
        # In this source, the aggregate row is labelled TOTAL in SR NO and has no ward name.
        if serial in {"total", "grand total"} and not ward: total_rows.append(r); continue
        open_plots=money(r["Open Plot Count"]); arv=money(r["Total ARV"])
        if ward and demand is not None and count is not None and open_plots is not None and arv is not None:
            out.append({"ward_id":ward,"ward_name":ward,"total_assessments_count":round(count),"open_plot_count":round(open_plots),"built_properties":round(count-open_plots),"properties_on_roll":round(count-open_plots),"total_arv":arv,"property_tax_demand_inr":demand,"property_tax_collected_inr":collected or ""})
    if len(total_rows) != 1: raise SystemExit(f"Expected exactly one TOTAL row; found {len(total_rows)}. Inspect the source before proceeding.")
    total=total_rows[0]
    for raw, output in [("Total Count","total_assessments_count"),("Open Plot Count","open_plot_count"),("Total ARV","total_arv"),("ORIGINAL DEMAND 2017-18","property_tax_demand_inr")]:
        published=money(total[raw]); computed=sum(x[output] for x in out)
        if published is None or abs(computed-published) > max(1,abs(published)*0.001): raise SystemExit(f"TOTAL CHECK FAILED for {raw}: rows={computed:,.2f}, published={published}")
        print(f"TOTAL CHECK OK — {raw}: {computed:,.2f}")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("w",newline="") as h: w=csv.DictWriter(h,fieldnames=out[0].keys());w.writeheader();w.writerows(out)
    print(f"Wrote {len(out)} Pune Sampark rows to {a.output}; built-properties denominator = Total Count − Open Plot Count")
if __name__=="__main__":main()
