# Reproducing the Pune operational POC

The repository includes the processed Pune tax table, the Sampark-to-administrative-ward crosswalk, exported ward building measures, analysis code, and generated outputs.

To regenerate the map and results from the tracked tables:

```bash
python3 analyse_pune_poc.py --admin data/admin_wards.csv --buildings data/ward_buildings.csv --geojson data/raw/pune_wards/GeoData/pune-admin-wards.geojson --out outputs/pune
```

The ward GeoJSON is sourced from the public DataMeet Pune wards repository and is intentionally not vendored here because it is a separate Git checkout. Restore it first:

```bash
python3 clone_pune_wards.py
```

The satellite table in `data/ward_buildings.csv` was exported from Google Earth Engine using `earth_engine_pune_2018_2019.js`.

This is an operational POC, not evidence that the current Pune screening ranks tax-base gaps. See `outputs/pune/LIMITATIONS.md`.
