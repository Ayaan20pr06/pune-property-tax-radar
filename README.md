# Property-tax gap radar

A small, auditable proof-of-concept for ranking wards where satellite-derived built form suggests that the recorded property-tax demand is low. It is a field-inspection prioritiser, not an automated assessment system.

## Fast demo

```bash
cd property-tax-radar
python3 run_radar.py --demo
```

The demo uses synthetic data, so its metrics demonstrate the pipeline works—not the business claim. Share the complete terminal output and the generated `outputs/summary.txt` here after running it.

## Real-data run

1. Prepare `data/buildings.csv` and `data/wards.csv` following [`data/README.md`](data/README.md).
2. Run:

```bash
cd property-tax-radar
python3 run_radar.py --data-dir data --output-dir outputs --as-of-year 2025
```

For Pune FY2017-18, first use `prepare_pune_2017_18.py` on the OpenCity CSV. It carries `Total Count` into `properties_on_roll` and uses `ORIGINAL DEMAND 2017-18`, not arrears.

For satellite work, prefer `data/ward_features.csv` exported by [`earth_engine_pune_features.js`](earth_engine_pune_features.js). This is more honest than inventing per-building records from a raster. It can be used in place of `buildings.csv`.

## Pitch-deck test that matters

The credible claim is retrospective: train only on tax-roll data available *before* a city-wide survey, rank wards, then show that high-ranked wards later had unusually large verified omissions. Include the AUC only if `survey_gap_fraction` comes from an independent survey. A demo or a model fit on post-survey values cannot establish that claim.

## Outputs

- `outputs/summary.txt` — copyable metrics and top inspection targets.
- `outputs/ward_inspection_ranking.csv` — field-team queue.
- `outputs/demand_vs_expected.svg` — recorded versus predicted demand.
- `outputs/top_wards.svg` — pitch-ready inspection chart.

The model uses cross-validated out-of-fold predictions so a ward is scored by a model that did not train on its own tax-demand value.

## Pune evidence workflow

Do not use `--demo` results in a pitch. Download the FY2017-18 source CSV, prepare `wards.csv`, then validate every join before modelling. The final retrospective check is implemented in `validate_regions.py`; its input mapping must document how every old tax ward maps to the later survey's regional-office geography.

If the OpenCity host blocks direct `curl` downloads, run `python3 fetch_pune_source.py`. It tries the download and CKAN datastore APIs without requiring a URL to be pasted from chat.
