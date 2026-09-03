# Case Study: SAP Field Inventory KPI Dashboard

**Tools:** Power BI · DAX · Python (pandas/numpy) · PostgreSQL (optional)
**GitHub:** [github.com/wriveraj/sap-field-inventory-kpi-dashboard](https://github.com/wriveraj/sap-field-inventory-kpi-dashboard)

---

## The Problem

Part of my job is designing SAP-integrated KPI dashboards that track inventory accuracy, order fulfillment, and demand variance across a multi-territory field operation. The raw material for that is always the same handful of questions: Which territory is bleeding money on reorders right now? Is a PAR compliance problem a blip or a trend? Is a stocking gap a demand problem or a speed problem? Which SKUs are too unpredictable to trust to a standard reorder formula?

Those questions don't have obvious answers sitting in SAP itself — you have to pull the data out and model it. I wanted a portfolio project that showed that modeling work end to end, on data nobody could mistake for my employer's.

---

## What I Built

A synthetic dataset simulating a 4-territory, 18-site surgical device field inventory operation over a trailing 12-month window (Aug 2025–Jul 2026), generated with a seeded Python script so the numbers are reproducible. Nine tables, star-schema-ish — three dimension tables and six fact tables:

| Table | Purpose |
|---|---|
| territories | 4 territories |
| sites | 18 sites (Hospital / ASC / Clinic), tied to a territory |
| products | Implant / Instrument / Disposable / PPE catalog with unit cost |
| par_levels | Target stocking levels per site/product, with an effective date range |
| inventory_snapshots | Point-in-time on-hand quantity per site/product |
| cases | Surgical case demand, with Fulfilled / Delayed / Cancelled status |
| allocations | Advanced allocation requests, from request to fulfillment |
| cycle_counts | Physical count vs. system-expected quantity |
| demand_history | Monthly usage by site/product, for variance analysis |

**All data is synthetic.** No employer data, real site names, account numbers, or actual production figures appear anywhere in this project — the generation logic is in `generate_data.py`, and every number below was confirmed by directly querying the generated CSVs, not just designed in as an assumption.

---

## The DAX Measures

Six core KPI measures, plus three time-intelligence measures layered on top — the time intelligence is the piece that separates this project from Projects 01 and 02, since it's what actually shows a problem *emerging* instead of just reporting a snapshot.

**Core measures:**

- **Fulfillment Rate** — fulfilled cases ÷ total cases
- **PAR Compliance %** — share of site/product snapshots at or above PAR
- **Demand Variance (CV)** — coefficient of variation per product, to flag SKUs that don't behave predictably enough for a standard reorder formula
- **Reorder Cost Exposure** — sum of (PAR gap × unit cost), with a "latest month" variant for a headline KPI card
- **Cycle Count Accuracy %** — how close physical counts land to system-expected quantity
- **Allocation Turnaround (Days)** — average days from allocation request to fulfillment

**Time intelligence:**

- **Fulfillment Rate MoM Δ** — month-over-month change
- **Reorder Cost Exposure – Rolling 3mo Avg** — smooths noise for a trend line
- **PAR Compliance % – Change vs. Start** — current value against the 12-month starting value, which is the measure that catches a slow collapse a snapshot would miss entirely

Full DAX in `dax-measures.md`, written against the exact column names in `schema.sql` — no renaming needed to paste it in.

---

## What the Data Surfaced

1. **$136,594 in total reorder cost exposure** across the territory in the most recent month — **75% of it ($102,085) concentrated in the Gulf Coast territory alone.**
2. **Gulf Coast PAR compliance collapsed from 101% to 50%** over the 12-month window, while every other territory held 96–103%. A widening gap, not a one-time miss.
3. **Gulf Coast allocation turnaround averages 8.5 days**, nearly 3x the 3.0-day average everywhere else — the stocking gap above is partly a *speed* problem, not just a *demand* problem.
4. **Cannulated Screw Set 6.5mm has 3.5x the demand variability of any other implant** (coefficient of variation 1.29 vs. ~0.37 for comparable SKUs) — a candidate for safety-stock or PAR-formula review rather than standard reorder logic.
5. **Overall case fulfillment rate: 87.4%**, with 10.4% Delayed and 2.2% Cancelled — the headline KPI for the dashboard's top tile.

Findings 2 and 3 are the ones that matter most, together. A territory can be short on stock for two very different reasons — it isn't ordering enough, or its orders aren't moving fast enough — and those get fixed by completely different people. The data says Gulf Coast is a turnaround problem wearing a PAR-compliance costume.

---

## The Dashboard

Built as an interactive HTML dashboard rather than an embedded Power BI report, to match the site's existing dark/yellow theme and stay consistent with Projects 01 and 02 — no Power BI required to view it. It replicates the DAX logic above directly in JS: KPI cards across the top (Fulfillment Rate, PAR Compliance %, Reorder Cost Exposure, Allocation Turnaround), a line chart of PAR Compliance % by month with territory as the series (the chart where Gulf Coast visibly splits off from the other three lines), a bar chart of reorder cost exposure by territory, and a product table sorted by demand variance. A second view drills into a single territory or site at the same grain.

---

## Why I Built This

This is the version of my day job I don't get to show anyone outside of it. Designing the actual SAP-integrated dashboards is part of what I do — but that work is proprietary, so a portfolio can only ever gesture at it. This project is me rebuilding the analytical spine of that work — the same questions, the same kind of measures, the same "how would I actually explain this to a territory manager" pressure — on data that's mine to share.

The dashboard doesn't replace judgment. It's the same thing I'd want on my own screen before a call with a territory manager: not a guess about where the problem is, a number.
