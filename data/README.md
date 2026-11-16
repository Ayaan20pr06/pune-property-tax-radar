# Data contract

Put two CSVs here, with one row per building and ward respectively.

`buildings.csv` required columns: `ward_id`, `building_id`, `footprint_m2`, `height_m`.
Optional: `construction_year` (used to calculate five-year new-build share). Height may be estimated from floors × 3 m, but label that assumption in the pitch.

`wards.csv` required columns: `ward_id`, `ward_name`, `properties_on_roll`, `property_tax_demand_inr`.
Optional: `property_tax_collected_inr`; `survey_gap_fraction` only where a later field survey supplies a ground-truth gap, for retrospective validation.

Tax demand must be the billed assessment / demand for a single financial year, not multi-year arrears or collection. Map every building to the same ward version as the tax roll before modelling.

For Pune FY2017-18, `properties_on_roll` is deliberately the built-properties count (`Total Count − Open Plot Count`), not all assessments. The preparation script also retains `total_assessments_count`, `open_plot_count`, `built_properties`, and `total_arv`.
