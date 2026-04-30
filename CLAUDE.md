# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

Course project (EAS 550 / DMQL) built on the Brazilian E-Commerce Public Dataset by Olist (~100k orders). Two phases live in the same repo:

- **Phase 1** — 3NF OLTP schema in PostgreSQL (Neon), Python ingestion, RBAC.
- **Phase 2** — dbt star schema on top of the OLTP tables, dbt tests, analytical SQL, SQLFluff + GitHub Actions CI.

Database is hosted on Neon (free tier). Treat the connection as scarce — Neon suspends idle compute and the SQLAlchemy pool in `ingest_data.py` is intentionally tuned tiny (`pool_size=2`, `pool_recycle=300`) so the DB can sleep. Don't widen those without reason.

## Architecture

The pipeline has three stacked layers — changing one without thinking about the others usually breaks something.

**1. OLTP schema (`schema.sql`)** — 9 tables in 3NF. Two lookup tables (`locations` keyed by `zip_code_prefix`, `product_categories` keyed by Portuguese `category_name`) are referenced by `customers`, `sellers`, and `products`. Composite PKs on `order_items (order_id, order_item_id)`, `order_payments (order_id, payment_sequential)`, and `order_reviews (review_id, order_id)`. The script drops everything in dependency order before recreating — running it wipes the database.

**2. Ingestion (`ingest_data.py`)** — Pandas reads CSVs from `./data/raw/`, renames columns to match the schema (e.g. `customer_zip_code_prefix` → `zip_code_prefix`, `order_purchase_timestamp` → `purchase_timestamp`, review fields drop the `review_` prefix), then writes via SQLAlchemy `INSERT … ON CONFLICT DO NOTHING` in 5000-row batches. Idempotent by design — safe to re-run. `locations` is built by unioning customer + seller zip data and deduping; `product_categories` is built by unioning the translation CSV with category names found in the products CSV. Reads `DATABASE_URL` from `.env` first, then falls back to `st.secrets` (Streamlit). The `-pooler` Neon connection string is required.

**3. dbt analytics (`olist_dbt/`)** — Two model layers:
- `models/staging/` → views over `source('olist', <table>)` from `_sources.yml`. Renames OLTP columns into a stable naming convention used by marts (e.g. staging re-prefixes timestamps back to `order_purchase_timestamp`).
- `models/marts/` → tables. Star schema centered on `fact_order_items` (grain: one row per order line item). Dimensions: `dim_customers`, `dim_sellers`, `dim_products`, `dim_dates`, `dim_locations`. The fact joins payments and reviews pre-aggregated to order grain (sum/count/string_agg for payments, avg/count for reviews) so a single line item carries order-level rollups. Materialization is set in `dbt_project.yml`: staging = `view`, marts = `table`. Tests live in `models/marts/schema.yml` (not_null, unique, relationships, accepted_values).

**Column-name boundary:** OLTP uses bare names (`purchase_timestamp`, `creation_date`); staging/marts use prefixed names (`order_purchase_timestamp`, `review_creation_date`). Renames happen in two places — `ingest_data.py` strips prefixes going *into* Postgres, staging models add them back going *out*. If you rename a column, fix both sides.

## Commands

All commands assume the working directory is the repo root unless noted.

### Environment

```bash
pip install -r requirements.txt
# DATABASE_URL must be set (use Neon -pooler connection for ingest_data.py)
# DBT_PASSWORD must be set for any dbt command (read by olist_dbt/profiles.yml)
```

### Ingestion

```bash
python ingest_data.py
```

### dbt (run from `olist_dbt/`)

```bash
cd olist_dbt
dbt debug   --profiles-dir .
dbt build   --profiles-dir .   # runs models + tests
dbt run     --profiles-dir .   # models only
dbt test    --profiles-dir .   # tests only
dbt docs generate --profiles-dir . && dbt docs serve

# Single model / test
dbt run  --profiles-dir . --select fact_order_items
dbt test --profiles-dir . --select fact_order_items
dbt run  --profiles-dir . --select +fact_order_items   # model + upstream
```

`--profiles-dir .` is required because `profiles.yml` lives inside the project directory, not the default `~/.dbt/`.

### Linting

```bash
sqlfluff lint olist_dbt/models/
sqlfluff fix  olist_dbt/models/
```

`.sqlfluff` uses `templater = dbt`, so linting will compile dbt models — `DBT_PASSWORD` must be set in the environment or the templater will fail.

### CI

`.github/workflows/ci.yml` runs SQLFluff lint and `dbt debug` → `dbt build` → `dbt test` on every PR to `main`. Both jobs need the `DBT_PASSWORD` repo secret. CI hits the real Neon database — there is no local Postgres in CI.

## Conventions

- SQL keywords and functions lowercase (`.sqlfluff` `capitalisation_policy = lower`). Excluded rules: `LT05`, `RF04`, `ST06`. Max line length 120.
- Don't capitalize SQL in new dbt models — it will fail lint.
- Phase 1 deliverable PDFs (`3nf_report.pdf`, `Olist Database ERD.pdf`, `star_schema_diagram.pdf`, `performance_tuning_report.pdf`) are checked-in artifacts — don't regenerate or rename without checking with the user.
- `milestone_checkin/` holds graded evidence (CI screenshots, dbt output captures). Treat as read-only unless explicitly updating it.
- `AI_DISCLOSURE.md` is a course-required artifact disclosing AI tool usage — keep it current if AI assistance is used on new work.
