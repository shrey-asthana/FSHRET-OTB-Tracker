"""
load_data.py
============
Phase 1 | Milestone 2 — Populate the OTB database with realistic sample data.

Run this AFTER create_db.py has already created the tables.
Command: python scripts/load_data.py
"""

import sqlite3
import random
from datetime import date, timedelta

# ─── CONFIG ──────────────────────────────────────────────────────────────────
DB_PATH = "db/otb.db"
random.seed(42)  # Fixed seed = same data every run (good for debugging)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("Connected to:", DB_PATH)
print()

# ─────────────────────────────────────────────────────────────────────────────
# TABLE 1: departments
# Columns: dept_id, dept_name
# ─────────────────────────────────────────────────────────────────────────────

departments = [
    (1, "Womenswear"),
    (2, "Menswear"),
    (3, "Accessories"),
]

cur.executemany(
    "INSERT OR IGNORE INTO departments (dept_id, dept_name) VALUES (?, ?)",
    departments
)
print(f"  ✓ Loaded {len(departments)} departments")

# ─────────────────────────────────────────────────────────────────────────────
# TABLE 2: categories
# Columns: cat_id, cat_name, dept_id
# ─────────────────────────────────────────────────────────────────────────────

categories = [
    # (cat_id, cat_name, dept_id)
    (1,  "Tops",      1),   # Womenswear
    (2,  "Dresses",   1),
    (3,  "Denim",     1),
    (4,  "Trousers",  1),
    (5,  "Outerwear", 1),
    (6,  "Tops",      2),   # Menswear
    (7,  "Denim",     2),
    (8,  "Trousers",  2),
    (9,  "Outerwear", 2),
    (10, "Bags",      3),   # Accessories
    (11, "Scarves",   3),
    (12, "Belts",     3),
]

cur.executemany(
    "INSERT OR IGNORE INTO categories (cat_id, cat_name, dept_id) VALUES (?, ?, ?)",
    categories
)
print(f"  ✓ Loaded {len(categories)} categories")

# ─────────────────────────────────────────────────────────────────────────────
# TABLE 3: otb_plan
# Columns: plan_id, cat_id, season, month, planned_sales_gbp, planned_end_stock_gbp
#
# One row per category per month — monthly budget breakdown.
# SS25 runs March to August 2025 = 6 months.
#
# The OTB formula:
#   OTB = Planned Sales + Planned End Stock − Opening Stock − On Order
# ─────────────────────────────────────────────────────────────────────────────

season = "SS25"

season_months = ["2025-03", "2025-04", "2025-05", "2025-06", "2025-07", "2025-08"]

# Total season planned sales per category (£ cost value)
category_season_budgets = {
    # cat_id: total planned sales £
    1:  42000,   # WW Tops
    2:  55000,   # WW Dresses
    3:  38000,   # WW Denim
    4:  30000,   # WW Trousers
    5:  65000,   # WW Outerwear
    6:  35000,   # MW Tops
    7:  40000,   # MW Denim
    8:  28000,   # MW Trousers
    9:  60000,   # MW Outerwear
    10: 18000,   # Bags
    11: 8000,    # Scarves
    12: 6000,    # Belts
}

# Monthly trading curve — how sales weight across the 6 months
# March is slow (just launching), May/June is peak, August tails off
monthly_weights = [0.10, 0.15, 0.22, 0.25, 0.18, 0.10]

otb_plans = []
plan_id = 1

for cat_id, total_sales in category_season_budgets.items():
    for i, month in enumerate(season_months):
        planned_sales_gbp      = round(total_sales * monthly_weights[i], 2)
        planned_end_stock_gbp  = round(planned_sales_gbp * 0.10, 2)  # 10% end stock target

        otb_plans.append((plan_id, cat_id, season, month, planned_sales_gbp, planned_end_stock_gbp))
        plan_id += 1

cur.executemany(
    """INSERT OR IGNORE INTO otb_plan
       (plan_id, cat_id, season, month, planned_sales_gbp, planned_end_stock_gbp)
       VALUES (?, ?, ?, ?, ?, ?)""",
    otb_plans
)
print(f"  ✓ Loaded {len(otb_plans)} OTB plan rows  ({len(category_season_budgets)} categories × {len(season_months)} months)")

# ─────────────────────────────────────────────────────────────────────────────
# TABLE 4: otb_opening_stock
# Columns: stock_id, cat_id, season, opening_stock_gbp
#
# Stock carried in from AW24 at the start of SS25.
# Typically 6–14% of the new season's planned sales.
# ─────────────────────────────────────────────────────────────────────────────

opening_stocks = []
stock_id = 1

for cat_id, total_sales in category_season_budgets.items():
    carry_in_pct       = random.uniform(0.06, 0.14)
    opening_stock_gbp  = round(total_sales * carry_in_pct, 2)

    opening_stocks.append((stock_id, cat_id, season, opening_stock_gbp))
    stock_id += 1

cur.executemany(
    """INSERT OR IGNORE INTO otb_opening_stock
       (stock_id, cat_id, season, opening_stock_gbp)
       VALUES (?, ?, ?, ?)""",
    opening_stocks
)
print(f"  ✓ Loaded {len(opening_stocks)} opening stock rows")

# ─────────────────────────────────────────────────────────────────────────────
# TABLE 5: purchase_orders
# Columns: po_id, cat_id, season, supplier, order_date, delivery_date,
#          order_value_gbp, status
#
# Every order placed with suppliers = the "On Order" in the OTB formula.
# ─────────────────────────────────────────────────────────────────────────────

suppliers = [
    "Zhuhai Garment Co.",
    "Istanbul Textile Ltd.",
    "Dhaka Fashions PVT",
    "Porto Atelier S.A.",
    "Bangalore Weaves Ltd.",
    "Guangzhou Apparel Co.",
    "Lisbon Knitwear S.A.",
]

# Status values match what create_db.py documents: confirmed, in transit, delivered
po_statuses = ["confirmed", "in transit", "delivered", "confirmed", "delivered"]

season_start = date(2025, 3, 1)
season_end   = date(2025, 8, 31)

def random_delivery_date():
    offset = random.randint(0, (season_end - season_start).days)
    return str(season_start + timedelta(days=offset))

def order_date_from_delivery(delivery_str):
    delivery  = date.fromisoformat(delivery_str)
    lead_time = random.randint(60, 120)   # 60–120 day supplier lead time
    return str(delivery - timedelta(days=lead_time))

purchase_orders = []
po_id = 1

for cat_id, total_sales in category_season_budgets.items():
    num_pos          = random.randint(4, 7)
    committed_pct    = random.uniform(0.75, 0.95)
    total_committed  = total_sales * committed_pct

    # Normalisation: split committed spend randomly across POs
    splits       = [random.random() for _ in range(num_pos)]
    total_split  = sum(splits)
    split_values = [s / total_split * total_committed for s in splits]

    for po_value in split_values:
        delivery_date = random_delivery_date()
        order_date    = order_date_from_delivery(delivery_date)

        purchase_orders.append((
            po_id,
            cat_id,
            season,
            random.choice(suppliers),
            order_date,
            delivery_date,
            round(po_value, 2),
            random.choice(po_statuses)
        ))
        po_id += 1

cur.executemany(
    """INSERT OR IGNORE INTO purchase_orders
       (po_id, cat_id, season, supplier, order_date, delivery_date, order_value_gbp, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
    purchase_orders
)
print(f"  ✓ Loaded {len(purchase_orders)} purchase orders")

# ─────────────────────────────────────────────────────────────────────────────
# TABLE 6: actual_sales
# Columns: sale_id, cat_id, season, week, sales_gbp
#
# Weekly actuals so far this season. Week format: "2025-W09" (ISO week).
# 12 weeks of history = early March through late May.
# ─────────────────────────────────────────────────────────────────────────────

performance_curves = {
    "normal":      [0.6, 0.9, 1.1, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.4, 0.3],
    "hero":        [1.2, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 1.0, 0.9, 0.8, 0.6, 0.4],
    "slow_burner": [0.3, 0.4, 0.5, 0.7, 0.9, 1.1, 1.2, 1.1, 1.0, 0.8, 0.6, 0.4],
    "problem":     [0.3, 0.3, 0.2, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
}

category_performance = {
    1: "normal",       # WW Tops
    2: "hero",         # WW Dresses — summer hero
    3: "slow_burner",  # WW Denim
    4: "normal",       # WW Trousers
    5: "problem",      # WW Outerwear — wrong for SS25
    6: "normal",       # MW Tops
    7: "hero",         # MW Denim
    8: "slow_burner",  # MW Trousers
    9: "problem",      # MW Outerwear
    10: "hero",        # Bags
    11: "normal",      # Scarves
    12: "slow_burner", # Belts
}

WEEKS_TO_GENERATE = 12

actual_sales = []
sale_id = 1

for cat_id, total_sales in category_season_budgets.items():
    perf_type   = category_performance.get(cat_id, "normal")
    curve       = performance_curves[perf_type]
    base_weekly = total_sales / 26  # Spread season budget over 26 trading weeks

    for week_num in range(1, WEEKS_TO_GENERATE + 1):
        week_start = season_start + timedelta(weeks=week_num - 1)
        iso_week   = week_start.strftime("%Y-W%V")   # e.g. "2025-W09"

        multiplier = curve[week_num - 1] if week_num <= len(curve) else 0.3
        noise      = random.uniform(0.85, 1.15)      # ±15% random variation
        sales_gbp  = round(base_weekly * multiplier * noise, 2)

        actual_sales.append((sale_id, cat_id, season, iso_week, sales_gbp))
        sale_id += 1

cur.executemany(
    """INSERT OR IGNORE INTO actual_sales
       (sale_id, cat_id, season, week, sales_gbp)
       VALUES (?, ?, ?, ?, ?)""",
    actual_sales
)
print(f"  ✓ Loaded {len(actual_sales)} actual sales rows  ({WEEKS_TO_GENERATE} weeks × {len(category_season_budgets)} categories)")

# ─────────────────────────────────────────────────────────────────────────────
# COMMIT & CLOSE
# ─────────────────────────────────────────────────────────────────────────────

conn.commit()
conn.close()

print()
print("=" * 55)
print("✅ All data loaded successfully!")
print("=" * 55)