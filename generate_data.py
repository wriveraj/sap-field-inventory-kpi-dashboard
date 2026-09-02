"""
generate_data.py — synthetic data generator for the SAP Field Inventory KPI Dashboard.

Produces 9 CSVs (one per table in schema.sql) modeling a 4-territory, 18-site
surgical device field inventory operation over a trailing 12-month window.

All data is synthetic. No employer data, real site names, or real account
numbers are used anywhere in this generator or its output.

Three intentional patterns are baked in so the resulting dashboard has real
findings to report (mirrors Project 01/02's "specific numbered findings"
case-study style):

  1. The "Gulf Coast" territory runs chronically below PAR from month 7 onward
     (a staffing/ordering gap that widens over time).
  2. Product "Cannulated Screw Set 6.5mm" (an Implant) has unusually high
     demand variance — spiky, unpredictable usage rather than a steady rate.
  3. The "Gulf Coast" territory also has the longest allocation turnaround
     (7-10 days vs. 2-4 days elsewhere) — a fulfillment-speed problem, not
     just a stocking problem.

Usage:
    pip install pandas numpy
    python generate_data.py
    # writes CSVs to ./data/
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

RNG = np.random.default_rng(42)
OUT_DIR = "data"

# 12 full months trailing the current date used for this project.
START_MONTH = date(2025, 8, 1)
N_MONTHS = 12
MONTHS = [START_MONTH + relativedelta(months=i) for i in range(N_MONTHS)]

# ---------------------------------------------------------------------------
# 1. Territories
# ---------------------------------------------------------------------------
territories = pd.DataFrame([
    {"territory_id": 1, "territory_name": "Coastal Northeast", "region": "Northeast"},
    {"territory_id": 2, "territory_name": "Great Lakes",       "region": "Midwest"},
    {"territory_id": 3, "territory_name": "Piedmont",          "region": "Southeast"},
    {"territory_id": 4, "territory_name": "Gulf Coast",        "region": "South"},
])
LAGGING_TERRITORY_ID = 4  # Gulf Coast — intentionally under-PAR + slow allocations

# ---------------------------------------------------------------------------
# 2. Sites (4-5 per territory, 18 total)
# ---------------------------------------------------------------------------
site_rows = []
site_id = 1
states_by_territory = {1: ["CT", "MA", "NY"], 2: ["OH", "MI", "IL"], 3: ["NC", "SC", "GA"], 4: ["TX", "LA", "FL"]}
site_types = ["Hospital", "Hospital", "ASC", "Clinic"]
sites_per_territory = {1: 5, 2: 4, 3: 4, 4: 5}

for t_id, n_sites in sites_per_territory.items():
    for i in range(n_sites):
        site_rows.append({
            "site_id": site_id,
            "site_name": f"{territories.loc[territories.territory_id == t_id, 'territory_name'].values[0]} Site {i+1}",
            "territory_id": t_id,
            "site_type": RNG.choice(site_types),
            "state": RNG.choice(states_by_territory[t_id]),
        })
        site_id += 1

sites = pd.DataFrame(site_rows)

# ---------------------------------------------------------------------------
# 3. Products
# ---------------------------------------------------------------------------
products = pd.DataFrame([
    # Implants
    {"product_name": "Cannulated Screw Set 6.5mm", "category": "Implant", "unit_cost": 1850.00},
    {"product_name": "Total Knee System",           "category": "Implant", "unit_cost": 3400.00},
    {"product_name": "Hip Stem - Cementless",       "category": "Implant", "unit_cost": 2950.00},
    {"product_name": "Locking Plate 3.5mm",         "category": "Implant", "unit_cost": 975.00},
    {"product_name": "Intramedullary Nail",         "category": "Implant", "unit_cost": 2100.00},
    {"product_name": "Suture Anchor Kit",           "category": "Implant", "unit_cost": 640.00},
    {"product_name": "Spinal Fusion Cage",          "category": "Implant", "unit_cost": 3800.00},
    {"product_name": "External Fixator Set",        "category": "Implant", "unit_cost": 1420.00},
    # Instruments
    {"product_name": "Power Drill System",          "category": "Instrument", "unit_cost": 1200.00},
    {"product_name": "Reamer Set",                  "category": "Instrument", "unit_cost": 890.00},
    {"product_name": "Retractor Tray",               "category": "Instrument", "unit_cost": 410.00},
    {"product_name": "C-Arm Drape Kit",              "category": "Instrument", "unit_cost": 320.00},
    {"product_name": "Torque Wrench Set",            "category": "Instrument", "unit_cost": 275.00},
    {"product_name": "Bone Saw Blade Set",           "category": "Instrument", "unit_cost": 240.00},
    # Disposables
    {"product_name": "Sterile Gown - Surgical",      "category": "Disposable", "unit_cost": 8.50},
    {"product_name": "Surgical Drape Pack",          "category": "Disposable", "unit_cost": 22.00},
    {"product_name": "Bone Cement Kit",              "category": "Disposable", "unit_cost": 145.00},
    {"product_name": "Irrigation Solution 3L",       "category": "Disposable", "unit_cost": 14.00},
    {"product_name": "Suture Pack - Assorted",       "category": "Disposable", "unit_cost": 38.00},
    {"product_name": "Skin Marker Kit",              "category": "Disposable", "unit_cost": 6.00},
    {"product_name": "Sterilization Wrap",           "category": "Disposable", "unit_cost": 11.00},
    # PPE
    {"product_name": "N95 Respirator",               "category": "PPE", "unit_cost": 1.80},
    {"product_name": "Surgical Face Shield",         "category": "PPE", "unit_cost": 3.20},
    {"product_name": "Sterile Surgical Gloves (pr)", "category": "PPE", "unit_cost": 0.90},
    {"product_name": "Bouffant Cap",                 "category": "PPE", "unit_cost": 0.35},
])
products.insert(0, "product_id", range(1, len(products) + 1))

HIGH_VARIANCE_PRODUCT_ID = int(products.loc[products.product_name == "Cannulated Screw Set 6.5mm", "product_id"].iloc[0])
IMPLANT_IDS = products.loc[products.category == "Implant", "product_id"].tolist()

# ---------------------------------------------------------------------------
# 4. PAR levels — each site carries 60-80% of the catalog
# ---------------------------------------------------------------------------
par_rows = []
par_id = 1
site_product_par = {}  # (site_id, product_id) -> par_qty, for downstream lookups

for _, s in sites.iterrows():
    n_products = RNG.integers(int(len(products) * 0.6), int(len(products) * 0.8))
    chosen = RNG.choice(products["product_id"].values, size=n_products, replace=False)
    for p_id in chosen:
        p_row = products.loc[products.product_id == p_id].iloc[0]
        base_par = {"Implant": 4, "Instrument": 3, "Disposable": 25, "PPE": 150}[p_row["category"]]
        par_qty = int(max(1, RNG.normal(base_par, base_par * 0.25)))
        par_rows.append({
            "par_id": par_id,
            "site_id": s["site_id"],
            "product_id": int(p_id),
            "par_qty": par_qty,
            "effective_start_date": START_MONTH,
            "effective_end_date": None,
        })
        site_product_par[(s["site_id"], int(p_id))] = par_qty
        par_id += 1

par_levels = pd.DataFrame(par_rows)

# ---------------------------------------------------------------------------
# 5. Inventory snapshots — monthly, on-hand qty around PAR with noise.
#    Gulf Coast drifts below PAR starting month 7 (index 6).
# ---------------------------------------------------------------------------
snapshot_rows = []
snapshot_id = 1

for (s_id, p_id), par_qty in site_product_par.items():
    territory_id = int(sites.loc[sites.site_id == s_id, "territory_id"].iloc[0])
    for i, month in enumerate(MONTHS):
        noise = RNG.normal(0, par_qty * 0.15)
        on_hand = par_qty + noise
        if territory_id == LAGGING_TERRITORY_ID and i >= 6:
            # widening shortfall for the lagging territory in the back half of the year
            shortfall_severity = (i - 5) * 0.08
            on_hand -= par_qty * shortfall_severity
        on_hand = int(max(0, round(on_hand)))
        snapshot_rows.append({
            "snapshot_id": snapshot_id,
            "site_id": s_id,
            "product_id": p_id,
            "snapshot_date": month,
            "on_hand_qty": on_hand,
        })
        snapshot_id += 1

inventory_snapshots = pd.DataFrame(snapshot_rows)

# ---------------------------------------------------------------------------
# 6. Cases — scheduled surgical cases per site per month, mostly implant-driven
# ---------------------------------------------------------------------------
case_rows = []
case_id = 1

for _, s in sites.iterrows():
    site_products = par_levels.loc[par_levels.site_id == s["site_id"], "product_id"].tolist()
    site_implants = [p for p in site_products if p in IMPLANT_IDS]
    if not site_implants:
        continue
    territory_id = int(s["territory_id"])
    for month in MONTHS:
        n_cases = RNG.integers(4, 13)
        for _ in range(n_cases):
            p_id = int(RNG.choice(site_implants))
            qty_required = int(RNG.integers(1, 4))
            case_day = month + timedelta(days=int(RNG.integers(0, 27)))

            snap = inventory_snapshots[
                (inventory_snapshots.site_id == s["site_id"]) &
                (inventory_snapshots.product_id == p_id) &
                (inventory_snapshots.snapshot_date == month)
            ]
            on_hand = int(snap["on_hand_qty"].iloc[0]) if len(snap) else 0

            if on_hand < qty_required:
                status = "Delayed" if RNG.random() < 0.85 else "Cancelled"
            else:
                status = "Fulfilled" if RNG.random() < 0.97 else "Delayed"

            case_rows.append({
                "case_id": case_id,
                "site_id": s["site_id"],
                "product_id": p_id,
                "case_date": case_day,
                "qty_required": qty_required,
                "case_status": status,
            })
            case_id += 1

cases = pd.DataFrame(case_rows)

# ---------------------------------------------------------------------------
# 7. Allocations — replenishment requests, longer turnaround for Gulf Coast
# ---------------------------------------------------------------------------
allocation_rows = []
allocation_id = 1

for (s_id, p_id), par_qty in site_product_par.items():
    territory_id = int(sites.loc[sites.site_id == s_id, "territory_id"].iloc[0])
    n_allocations = RNG.integers(3, 9)
    for _ in range(n_allocations):
        month = MONTHS[int(RNG.integers(0, N_MONTHS))]
        request_day = month + timedelta(days=int(RNG.integers(0, 27)))
        qty = int(max(1, RNG.normal(par_qty * 0.4, par_qty * 0.15)))

        if territory_id == LAGGING_TERRITORY_ID:
            turnaround = int(RNG.integers(7, 11))
        else:
            turnaround = int(RNG.integers(2, 5))

        # ~6% of requests are still open (no fulfilled_date)
        fulfilled_date = None if RNG.random() < 0.06 else request_day + timedelta(days=turnaround)

        allocation_rows.append({
            "allocation_id": allocation_id,
            "destination_site_id": s_id,
            "product_id": p_id,
            "qty": qty,
            "request_date": request_day,
            "fulfilled_date": fulfilled_date,
        })
        allocation_id += 1

allocations = pd.DataFrame(allocation_rows)

# ---------------------------------------------------------------------------
# 8. Cycle counts — quarterly per site/product subset, one product noisier
# ---------------------------------------------------------------------------
cycle_count_rows = []
count_id = 1
count_months = [MONTHS[2], MONTHS[5], MONTHS[8], MONTHS[11]]  # quarterly

for (s_id, p_id), par_qty in site_product_par.items():
    if RNG.random() < 0.5:  # not every site/product gets counted every quarter
        continue
    for month in count_months:
        snap = inventory_snapshots[
            (inventory_snapshots.site_id == s_id) &
            (inventory_snapshots.product_id == p_id) &
            (inventory_snapshots.snapshot_date == month)
        ]
        expected = int(snap["on_hand_qty"].iloc[0]) if len(snap) else par_qty

        variance_pct = 0.18 if p_id == HIGH_VARIANCE_PRODUCT_ID else 0.05
        actual = int(max(0, round(expected + RNG.normal(0, max(1, expected * variance_pct)))))

        cycle_count_rows.append({
            "count_id": count_id,
            "site_id": s_id,
            "product_id": p_id,
            "count_date": month,
            "expected_qty": expected,
            "actual_qty": actual,
        })
        count_id += 1

cycle_counts = pd.DataFrame(cycle_count_rows)

# ---------------------------------------------------------------------------
# 9. Demand history — monthly usage; high-variance product gets spiky usage
# ---------------------------------------------------------------------------
demand_rows = []
demand_id = 1

for (s_id, p_id), par_qty in site_product_par.items():
    p_row = products.loc[products.product_id == p_id].iloc[0]
    base_usage = {"Implant": 1.5, "Instrument": 1.0, "Disposable": 8.0, "PPE": 40.0}[p_row["category"]]
    for month in MONTHS:
        if p_id == HIGH_VARIANCE_PRODUCT_ID:
            # spiky, unpredictable usage — occasional zero months, occasional large spikes
            qty = int(max(0, RNG.choice([0, 0, base_usage, base_usage * 4, base_usage * 6])))
        else:
            qty = int(max(0, round(RNG.normal(base_usage, base_usage * 0.3))))
        demand_rows.append({
            "demand_id": demand_id,
            "site_id": s_id,
            "product_id": p_id,
            "usage_month": month,
            "qty_used": qty,
        })
        demand_id += 1

demand_history = pd.DataFrame(demand_rows)

# ---------------------------------------------------------------------------
# Write CSVs
# ---------------------------------------------------------------------------
import os
os.makedirs(OUT_DIR, exist_ok=True)

tables = {
    "territories": territories,
    "sites": sites,
    "products": products,
    "par_levels": par_levels,
    "inventory_snapshots": inventory_snapshots,
    "cases": cases,
    "allocations": allocations,
    "cycle_counts": cycle_counts,
    "demand_history": demand_history,
}

for name, df in tables.items():
    path = os.path.join(OUT_DIR, f"{name}.csv")
    df.to_csv(path, index=False)
    print(f"{name:22s} {len(df):6,d} rows -> {path}")

print("\nDone. Load these CSVs directly into Power BI (Get Data > Text/CSV),")
print("or run schema.sql against Postgres and \\copy each table in.")
