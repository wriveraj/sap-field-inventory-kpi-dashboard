# DAX Measures — SAP Field Inventory KPI Dashboard


Paste these into Power BI Desktop after loading the 9 CSVs from `data/`.
Written against the exact column names in `schema.sql` — no renaming needed.

## 1. Setup — do this before writing any measures

**A. Create a Calendar table.** None of the fact tables share a single date
column, so build one shared date dimension. New Table:

```
Calendar =
CALENDAR(DATE(2025,8,1), DATE(2026,7,31))
```

Mark it as a Date Table: select the table → Table tools → "Mark as Date Table"
→ pick the `Date` column. Then add a couple of helper columns for readability:

```
Calendar[Month] = FORMAT('Calendar'[Date], "MMM YYYY")
Calendar[MonthStart] = DATE(YEAR('Calendar'[Date]), MONTH('Calendar'[Date]), 1)
```

**B. Build relationships to Calendar** (Model view, drag `Date` to each):
- `Calendar[Date]` → `inventory_snapshots[snapshot_date]`
- `Calendar[Date]` → `cases[case_date]`
- `Calendar[Date]` → `allocations[request_date]`
- `Calendar[Date]` → `cycle_counts[count_date]`
- `Calendar[Date]` → `demand_history[usage_month]`

All one-to-many, Calendar on the "one" side, single direction.

**C. Standard dimension relationships** (should auto-detect, verify these exist):
- `sites[territory_id]` → `territories[territory_id]`
- `par_levels[site_id]` → `sites[site_id]`, `par_levels[product_id]` → `products[product_id]`
- Same site_id/product_id pattern for `inventory_snapshots`, `cases`,
  `allocations` (site_id via `destination_site_id`), `cycle_counts`, `demand_history`

**D. Two calculated columns needed** — `par_levels` doesn't have a direct key
into `inventory_snapshots`, so pull PAR qty across with a lookup rather than
a relationship (avoids a composite-key modeling headache):

In `inventory_snapshots`, new column:
```
PAR Qty =
LOOKUPVALUE(
    par_levels[par_qty],
    par_levels[site_id], inventory_snapshots[site_id],
    par_levels[product_id], inventory_snapshots[product_id]
)
```

In `inventory_snapshots`, new column:
```
Unit Cost = RELATED(products[unit_cost])
```
(This one *does* work as RELATED if the product_id relationship from step C
is in place.)

---

## 2. Core KPI measures

### Fulfillment Rate
```
Fulfilled Cases = CALCULATE(COUNTROWS(cases), cases[case_status] = "Fulfilled")

Total Cases = COUNTROWS(cases)

Fulfillment Rate = DIVIDE([Fulfilled Cases], [Total Cases])
```
Format as percentage. Slice by `territories[territory_name]` or `sites[site_name]`.

### PAR Compliance %
```
Sites At Or Above PAR =
CALCULATE(
    COUNTROWS(inventory_snapshots),
    inventory_snapshots[on_hand_qty] >= inventory_snapshots[PAR Qty]
)

Total Site-Product Snapshots = COUNTROWS(inventory_snapshots)

PAR Compliance % = DIVIDE([Sites At Or Above PAR], [Total Site-Product Snapshots])
```
This is the measure that shows Gulf Coast dropping from ~101% to 50% when
you plot it by month — put it on a line chart with `Calendar[MonthStart]`
on the x-axis and `territories[territory_name]` as legend.

### Demand Variance (coefficient of variation)
```
Demand Avg = AVERAGE(demand_history[qty_used])

Demand StDev = STDEV.P(demand_history[qty_used])

Demand Variance (CV) = DIVIDE([Demand StDev], [Demand Avg])
```
Higher = less predictable. Sort a product-level table visual by this
descending — Cannulated Screw Set 6.5mm should land at the top.

### Reorder Cost Exposure
```
PAR Gap =
SUMX(
    inventory_snapshots,
    MAX(0, inventory_snapshots[PAR Qty] - inventory_snapshots[on_hand_qty])
)

Reorder Cost Exposure =
SUMX(
    inventory_snapshots,
    MAX(0, inventory_snapshots[PAR Qty] - inventory_snapshots[on_hand_qty])
        * inventory_snapshots[Unit Cost]
)

Reorder Cost Exposure (Latest Month) =
CALCULATE(
    [Reorder Cost Exposure],
    FILTER(ALL('Calendar'), 'Calendar'[Date] = MAX('Calendar'[Date]))
)
```
Use the "(Latest Month)" version for a headline KPI card — it forces the
calc to the most recent snapshot regardless of what else is on the report
page, same framing as Project 01's "$59,752 in reorder cost exposure" tile.

### Cycle Count Accuracy
```
Cycle Count Accuracy % =
AVERAGEX(
    cycle_counts,
    1 - DIVIDE(ABS(cycle_counts[actual_qty] - cycle_counts[expected_qty]), cycle_counts[expected_qty])
)
```

### Allocation Turnaround
```
Allocation Turnaround (Days) =
AVERAGEX(
    allocations,
    DATEDIFF(allocations[request_date], allocations[fulfilled_date], DAY)
)
```
`DATEDIFF` returns blank for still-open allocations (no `fulfilled_date`),
and `AVERAGEX` ignores blanks automatically — no extra filtering needed.
This is the measure that shows Gulf Coast at ~8.5 days vs. ~3.0 elsewhere.

---

## 3. Time intelligence (this is the DAX depth that differentiates this
project from 01/02 — don't skip it)

### Month-over-month change
```
Fulfillment Rate MoM Δ =
VAR CurrentRate = [Fulfillment Rate]
VAR PriorRate =
    CALCULATE([Fulfillment Rate], DATEADD('Calendar'[Date], -1, MONTH))
RETURN
    CurrentRate - PriorRate
```

### Rolling 3-month average (smooths noise, good for the exposure trend line)
```
Reorder Cost Exposure - Rolling 3mo Avg =
AVERAGEX(
    DATESINPERIOD('Calendar'[Date], LASTDATE('Calendar'[Date]), -3, MONTH),
    [Reorder Cost Exposure]
)
```

### PAR Compliance trend vs. 12-month start (the "collapsed from 101% to 50%" stat)
```
PAR Compliance % - Change vs Start =
VAR StartValue =
    CALCULATE([PAR Compliance %], FIRSTDATE('Calendar'[Date]))
VAR CurrentValue = [PAR Compliance %]
RETURN
    CurrentValue - StartValue
```

---

## 4. Suggested visuals (page 1 — territory overview)

- KPI cards across the top: `Fulfillment Rate`, `PAR Compliance %`,
  `Reorder Cost Exposure (Latest Month)`, `Allocation Turnaround (Days)`
- Line chart: `PAR Compliance %` by `Calendar[MonthStart]`, legend =
  `territories[territory_name]` — this is the chart that sells the whole
  project, since Gulf Coast visibly diverges from the other three lines
- Bar chart: `Reorder Cost Exposure` by `territories[territory_name]`,
  sorted descending
- Table: products sorted by `Demand Variance (CV)` descending, with
  `Demand Avg` and `Demand StDev` as supporting columns

Page 2 (drill-down) can filter to a single territory/site and show the
same measures at that grain — standard Power BI drill pattern, no new DAX
needed beyond what's above.
