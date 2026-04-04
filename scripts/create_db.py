# create_db.py
# This script creates the SQLite database and all tables for the OTB Tracker.
# Run this ONCE to set up the database. If you run it again, it won't overwrite existing data.

import sqlalchemy as sa  # SQLAlchemy is our toolkit for talking to databases from Python
import os                # Used to build file paths that work on any operating system

# ─── 1. Connect to the database ───────────────────────────────────────────────
# SQLite stores everything in a single file. We tell SQLAlchemy where that file lives.
# If the file doesn't exist yet, SQLite will create it automatically.

DB_PATH = os.path.join("db", "otb.db")          # Path: db/otb.db
engine = sa.create_engine(f"sqlite:///{DB_PATH}") # "engine" = our connection to the DB
metadata = sa.MetaData()                           # "metadata" = a registry of all our tables

# ─── 2. Define tables ─────────────────────────────────────────────────────────
# Each table below is like a CREATE TABLE statement in SQL.
# sa.Column() = one column, with a name and data type.

# DEPARTMENTS — top-level trading divisions e.g. Womenswear, Menswear, Footwear
departments = sa.Table("departments", metadata,
    sa.Column("dept_id",   sa.Integer, primary_key=True),  # Unique ID, like an identity column in SQL
    sa.Column("dept_name", sa.String,  nullable=False),    # e.g. "Womenswear"
)

# CATEGORIES — sub-divisions within a department e.g. Tops, Bottoms, Outerwear
categories = sa.Table("categories", metadata,
    sa.Column("cat_id",   sa.Integer, primary_key=True),
    sa.Column("cat_name", sa.String,  nullable=False),     # e.g. "Outerwear"
    sa.Column("dept_id",  sa.Integer, sa.ForeignKey("departments.dept_id")),  # Links to departments
)

# OTB_PLAN — the planner's season budget, broken down by category and month
# This is the "planned" side of the OTB formula
otb_plan = sa.Table("otb_plan", metadata,
    sa.Column("plan_id",             sa.Integer, primary_key=True),
    sa.Column("cat_id",              sa.Integer, sa.ForeignKey("categories.cat_id")),
    sa.Column("season",              sa.String,  nullable=False),   # e.g. "SS25"
    sa.Column("month",               sa.String,  nullable=False),   # e.g. "2025-03"
    sa.Column("planned_sales_gbp",   sa.Float,   nullable=False),   # Planned sales in £ (cost value)
    sa.Column("planned_end_stock_gbp", sa.Float, nullable=False),   # Target closing stock in £
)

# OPENING_STOCK — stock on hand at the start of the season, in £ cost value
otb_opening_stock = sa.Table("otb_opening_stock", metadata,
    sa.Column("stock_id",        sa.Integer, primary_key=True),
    sa.Column("cat_id",          sa.Integer, sa.ForeignKey("categories.cat_id")),
    sa.Column("season",          sa.String,  nullable=False),
    sa.Column("opening_stock_gbp", sa.Float, nullable=False),  # £ value of stock at season start
)

# PURCHASE_ORDERS — every order the buyer has placed, with delivery dates and cost value
# This is the "on order" part of the OTB formula
purchase_orders = sa.Table("purchase_orders", metadata,
    sa.Column("po_id",           sa.Integer, primary_key=True),
    sa.Column("cat_id",          sa.Integer, sa.ForeignKey("categories.cat_id")),
    sa.Column("season",          sa.String,  nullable=False),
    sa.Column("supplier",        sa.String,  nullable=False),   # e.g. "Supplier A"
    sa.Column("order_date",      sa.String,  nullable=False),   # Date PO was raised
    sa.Column("delivery_date",   sa.String,  nullable=False),   # Expected delivery date
    sa.Column("order_value_gbp", sa.Float,   nullable=False),   # £ cost value of the order
    sa.Column("status",          sa.String,  nullable=False),   # "confirmed", "in transit", "delivered"
)

# ACTUAL_SALES — weekly sales as the season progresses (in £ cost value)
# We'll use this in Phase 2 to track how actuals compare to the plan
actual_sales = sa.Table("actual_sales", metadata,
    sa.Column("sale_id",       sa.Integer, primary_key=True),
    sa.Column("cat_id",        sa.Integer, sa.ForeignKey("categories.cat_id")),
    sa.Column("season",        sa.String,  nullable=False),
    sa.Column("week",          sa.String,  nullable=False),    # e.g. "2025-W10"
    sa.Column("sales_gbp",     sa.Float,   nullable=False),    # Actual sales that week in £
)

# ─── 3. Create all tables in the database ─────────────────────────────────────
# checkfirst=True means: only create a table if it doesn't already exist.
# This makes the script safe to re-run without wiping your data.
metadata.create_all(engine, checkfirst=True)

print("✅ Database created at db/otb.db")
print("✅ Tables created: departments, categories, otb_plan, otb_opening_stock, purchase_orders, actual_sales")