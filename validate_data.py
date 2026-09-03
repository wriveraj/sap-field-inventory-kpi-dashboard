r"""
validate_data.py - independently re-derive the 5 headline findings from the
synthetic CSVs. Run this from the project root (same folder as data\).
"""
import pandas as pd

sites = pd.read_csv("data/sites.csv")
territories = pd.read_csv("data/territories.csv")
inv = pd.read_csv("data/inventory_snapshots.csv", parse_dates=["snapshot_date"])
par = pd.read_csv("data/par_levels.csv")
alloc = pd.read_csv("data/allocations.csv", parse_dates=["request_date", "fulfilled_date"])
demand = pd.read_csv("data/demand_history.csv")
products = pd.read_csv("data/products.csv")
cases = pd.read_csv("data/cases.csv")

inv = inv.merge(sites[["site_id", "territory_id"]], on="site_id").merge(territories, on="territory_id")
par_map = par.set_index(["site_id", "product_id"])["par_qty"]
inv["par_qty"] = inv.set_index(["site_id", "product_id"]).index.map(par_map)
inv["pct_of_par"] = inv["on_hand_qty"] / inv["par_qty"]

print("=== Finding 2: PAR compliance by territory, first vs last month ===")
print(inv.groupby(["territory_name", "snapshot_date"])["pct_of_par"].mean().unstack(level=0).iloc[[0, -1]].round(2))

alloc2 = alloc.merge(sites[["site_id", "territory_id"]], left_on="destination_site_id", right_on="site_id").merge(territories, on="territory_id")
alloc2["turnaround"] = (alloc2["fulfilled_date"] - alloc2["request_date"]).dt.days
print("\n=== Finding 3: allocation turnaround (days) by territory ===")
print(alloc2.groupby("territory_name")["turnaround"].mean().round(1))

dv = demand.groupby("product_id")["qty_used"].agg(["mean", "std"])
dv["cv"] = dv["std"] / dv["mean"].replace(0, 1)
dv = dv.merge(products[["product_id", "product_name"]], on="product_id")
print("\n=== Finding 4: demand variance (CV), top 5 ===")
print(dv.sort_values("cv", ascending=False)[["product_name", "mean", "std", "cv"]].head(5).round(2))

print("\n=== Finding 5: case fulfillment rate ===")
print(cases["case_status"].value_counts(normalize=True).round(3))

inv2 = inv.merge(products[["product_id", "unit_cost"]], on="product_id")
latest = inv2[inv2.snapshot_date == inv2.snapshot_date.max()].copy()
latest["gap"] = (latest["par_qty"] - latest["on_hand_qty"]).clip(lower=0)
latest["exposure"] = latest["gap"] * latest["unit_cost"]
print("\n=== Finding 1: reorder cost exposure, latest month ===")
print("Total:", round(latest["exposure"].sum(), 2))
print(latest.groupby("territory_name")["exposure"].sum().round(2).sort_values(ascending=False))