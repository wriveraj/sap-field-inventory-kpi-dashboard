# SAP Field Inventory KPI Dashboard — Data Layer

Synthetic dataset modeling a 4-territory, 18-site surgical device field
inventory operation over a trailing 12-month window (Aug 2025–Jul 2026).
Built to demonstrate Power BI + DAX modeling on the kind of field inventory
data managed daily in an SAP-based territory: PAR levels, case demand,
advanced allocations, and cycle counts.

**All data is synthetic.** No employer data, real site names, account
numbers, or actual production figures appear anywhere in this project —
see `generate_data.py` for the full generation logic.

## Files

- `schema.sql` — relational schema (9 tables), Postgres-compatible
- `generate_data.py` — generator script (pandas/numpy, seeded for reproducibility)
- `data/*.csv` — generated output, ready to load directly into Power BI

## Loading into Power BI

Power BI → Get Data → Text/CSV → import each file in `data/`. Set relationships
using the `*_id` columns per `schema.sql` (star-schema-ish: `sites`,
`products`, and `territories` are dimension tables; the rest are fact tables
keyed to them).

## Loading into Postgres (optional)

```bash
psql -d your_db -f schema.sql
psql -d your_db -c "\copy territories FROM 'data/territories.csv' CSV HEADER"
psql -d your_db -c "\copy sites FROM 'data/sites.csv' CSV HEADER"
psql -d your_db -c "\copy products FROM 'data/products.csv' CSV HEADER"
psql -d your_db -c "\copy par_levels FROM 'data/par_levels.csv' CSV HEADER"
psql -d your_db -c "\copy inventory_snapshots FROM 'data/inventory_snapshots.csv' CSV HEADER"
psql -d your_db -c "\copy cases FROM 'data/cases.csv' CSV HEADER"
psql -d your_db -c "\copy allocations FROM 'data/allocations.csv' CSV HEADER"
psql -d your_db -c "\copy cycle_counts FROM 'data/cycle_counts.csv' CSV HEADER"
psql -d your_db -c "\copy demand_history FROM 'data/demand_history.csv' CSV HEADER"
```

## Findings baked into this dataset (validated against generated output)

These are the "so what" numbers for the case study — confirmed by directly
querying the generated CSVs, not just designed-in assumptions:

1. **$136,594 in total reorder cost exposure** across the territory in the
   most recent month (below-PAR gap × unit cost) — **75% of it ($102,085)
   concentrated in the Gulf Coast territory alone.**
2. **Gulf Coast PAR compliance collapsed from 101% to 50%** over the
   12-month window, while every other territory held 96–103%. This is a
   widening gap, not a one-time miss — worth a trend chart, not just a
   snapshot stat.
3. **Gulf Coast allocation turnaround averages 8.5 days**, nearly 3x the
   3.0-day average everywhere else — the stocking gap above is partly a
   *speed* problem, not just a *demand* problem.
4. **Cannulated Screw Set 6.5mm has 3.5x the demand variability of any
   other implant** (coefficient of variation 1.29 vs. ~0.37 for comparable
   SKUs) — a candidate for safety-stock or PAR-formula review rather than
   standard reorder logic.
5. **Overall case fulfillment rate: 87.4%** (Fulfilled), with 10.4% Delayed
   and 2.2% Cancelled — a clean headline KPI for the dashboard's top tile.

## Next steps to finish Project 03

1. Build the Power BI model: import CSVs, set relationships, write DAX
   measures for the 6 KPIs listed in the project scope doc.
2. Build 1-2 dashboard pages (territory overview + drill-down).
3. Decide: embed Power BI (Publish to Web) or rebuild key visuals in
   HTML/JS to match the site's existing dark/yellow theme, same as
   Projects 01/02.
4. Write the case study using the 5 findings above as the numbered list.
5. Push this repo to GitHub, update the site card from "In Development"
   to a live link.
