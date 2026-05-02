# Olist PostgreSQL Database Project (Phase 1 and Phase 2)

# Olist PostgreSQL Database Project (Phase 1)

**Entity-Relationship Modeling & Cloud Data Ingestion**

Hey! Here is our implementation for Phase 1 of the E-Commerce Database Project. We took the raw Kaggle Olist dataset and turned it into a fully fleshed-out, strictly **Third Normal Form (3NF)** PostgreSQL database hosted on Neon.

## Project Demo

*Link to Unlisted YouTube Demo:* ([https://youtu.be/NfuyvZ5eZF8](https://youtu.be/NfuyvZ5eZF8))

## Project Overview & Deliverables

This phase covers everything from raw relational modeling to writing constraints and building out a Python ingestion pipeline that doesn't duplicate data.

**What's inside:**

1. **`docs/ERD.md`** and **`docs/ERD.pdf`**: Our Crow's Foot diagram showing how everything maps together logically.
2. **`schema.sql`**: The DDL script we wrote to provision the actual tables in Postgres.
3. **`docs/3nf_report.pdf`**: Our write-up explaining why we made certain normalization choices and how they prevent common database anomalies.
4. **`ingest_data.py`**: A Pandas/SQLAlchemy ETL script. We made sure it's fully idempotent, meaning you can run it as many times as you want without messing up the database.
5. **`security.sql`** *(Bonus)*: A quick Role-Based Access Control setup we added to separate read-only analysts from an app user that can actually insert data.

## Folder Structure

```text
.
├── data/
│   └── raw          
├── ingest_data.py         
├── README.md              
├── requirements.txt       
├── schema.sql             
├── security.sql           
└── .gitignore             
```

## Dataset Source

We used the Brazilian E-Commerce Public Dataset by Olist. It contains around 100k anonymized orders from 2016 to 2018.

* **You can grab it here:** [Olist E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
* **Local Setup:** Just unzip the CSVs right into `./data/raw/` at the root of the project.

---

## How to Run It

### 1. Setting up Neon Postgres

1. Make a free serverless project over at [Neon.tech](https://neon.tech/).
2. Go to your Neon Dashboard and find your **Connection Details**.
3. Grab both your **Direct Connection** (for the SQL scripts) and your **Pooled Connection** (the one with `-pooler` in the host, for the Python script).

### 2. Deploying the Schema

Pop open DBeaver, pgAdmin, or just the Neon SQL Editor, and run these against your *Direct Connection*:

1. **`schema.sql`:** This builds all 9 tables, sets up my foreign keys, and adds some indexes. If you need to wipe and restart, it safely drops everything first.
2. **`security.sql`:** This gives you an `analyst_role` (read-only) and an `app_user_role` (can insert/update, but intentionally can't `DELETE` stuff).

### 3. Python Environment

Make sure you have your dependencies installed:

```bash
# Optional but recommended: set up a venv
python -m venv venv
# Windows: venv\Scripts\activate   ||   macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
```

### 4. Running the Ingestion Script

**Quick tip:** We rely on the `DATABASE_URL` environment variable. Make sure to use your `-pooler` connection string here so Neon doesn't get overwhelmed.

**Linux / macOS:**

```bash
export DATABASE_URL="postgresql://user:password@ep-pooler-hostname.neon.tech/dbname?sslmode=require"  #sample url
python ingest_data.py
```

**Windows (PowerShell):**

```powershell
$env:DATABASE_URL="postgresql://user:password@ep-pooler-hostname.neon.tech/dbname?sslmode=require"   #sample url
python ingest_data.py
```

#### A Note on Idempotency

We made ingest_data.py fully idempotent. You can run it multiple times, and it will not duplicate rows or break the database. Here is how we handled that:

* **Pandas Cleanup:** We explicitly run drop_duplicates on the primary keys in memory first.
* **Postgres `ON CONFLICT`:** SQLAlchemy maps the tables and writes INSERT INTO ... ON CONFLICT (pk) DO NOTHING. So if a row is already in the database, Postgres simply ignores it.

### 5. Secure Credential Handling (GitHub Secrets)

To ensure that no database credentials are hardcoded in the repository, we store the database connection string securely using environment variables for local development and GitHub Secrets for repository automation.

For GitHub:

1. Go to your repo **Settings** > **Secrets and variables** > **Actions**.
2. Add a **New repository secret** called `DATABASE_URL`.
3. Paste your pooled Neon connection string as the value.

For local development:

* Store the same connection string in a local `.env` file.
* Make sure `.env` is included in `.gitignore` so it is not committed.

This keeps credentials out of the codebase and aligns with the Phase 1 security requirement.

---

## Neon Free-Tier Warning

Since Neon suspends databases to save compute hours, leaving a pool of connections open will keep the database awake and literally eat your entire free-tier quota in days.

To avoid this, we specifically tuned SQLAlchemy in `ingest_data.py`:

* **`pool_size=2` & `max_overflow=5`**: Keeps the connection count very low.
* **`pool_recycle=300`**: Kills any dormant connection older than 5 minutes so Neon can go to sleep when we're not actively ingesting.
* **`pool_pre_ping=True`**: Double-checks if the connection is alive before firing a query, which stops cold-start crashes.

# Olist PostgreSQL Database Project (Phase 2)

**Transformation, Data Quality, and CI/CD for E-Commerce Analytics**

This repository contains our Phase 2 implementation of the Olist E-Commerce Database Project for EAS 550. In this phase, we extended our Phase 1 PostgreSQL OLTP database into an analytics-ready warehouse layer using dbt, added automated data quality testing, created advanced analytical SQL queries, and configured CI/CD with GitHub Actions.

## Project Overview

Our project is based on the Brazilian E-Commerce Public Dataset by Olist. After building a normalized PostgreSQL database in Phase 1, Phase 2 focuses on transforming the operational schema into a star schema for analytics and business reporting.

The main goals of this phase are:

* build a dbt project to transform the OLTP schema into a star schema
* implement dbt tests for null checks, uniqueness, accepted values, and referential integrity
* generate dbt documentation for the analytics models
* create advanced SQL queries using CTEs, window functions, and aggregations
* analyze query performance using `EXPLAIN ANALYZE`
* apply indexing and document performance tuning decisions
* automate SQL linting and dbt testing through GitHub Actions

## Phase 2 Deliverables

This repository includes the following Phase 2 deliverables:

1. **`olist_dbt/`**
   Complete dbt project for transforming the OLTP schema into an analytics-ready star schema.

2. **`docs/star_schema_diagram.pdf`**
   Documentation of the star schema design, including the fact table, dimension tables, grain, and design rationale.

3. **`queries/`**
   Advanced analytical SQL queries:

   * `rfm_analysis.sql`
   * `seller_performance.sql`
   * `cohort_retention.sql`

4. **`docs/performance_tuning_report.pdf`**
   Performance analysis of the most complex analytical query using `EXPLAIN ANALYZE`, indexing strategy, and tuning observations.

5. **`.github/workflows/ci.yml`**
   GitHub Actions workflow to run SQLFluff linting and dbt tests automatically on pull requests to `main`.

6. **`.sqlfluff`**
   SQLFluff configuration for PostgreSQL and dbt templating.

## Folder Structure

````text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── data/
│   └── raw/
├── olist_dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── analyses/
│   ├── macros/
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   ├── seeds/
│   ├── snapshots/
│   └── tests/
├── queries/
│   ├── cohort_retention.sql
│   ├── rfm_analysis.sql
│   └── seller_performance.sql
├── docs/
│   ├── ERD.md
│   ├── ERD.pdf
│   ├── 3nf_report.pdf
│   ├── star_schema_diagram.pdf
│   ├── performance_tuning_report.pdf
│   └── screenshots/
├── README.md
├── schema.sql
├── ingest_data.py
├── security.sql
└── .sqlfluff
````


## Dataset Source

We used the Brazilian E-Commerce Public Dataset by Olist, which contains approximately 100k orders and related customer, seller, product, payment, review, and geolocation information.

Dataset source:

* Brazilian E-Commerce Public Dataset by Olist (Kaggle)

## Star Schema Summary

Our analytics layer uses a star schema centered around:

* **Fact table:** `fact_order_items`
* **Dimension tables:**

  * `dim_customers`
  * `dim_sellers`
  * `dim_products`
  * `dim_dates`
  * `dim_locations`

### Fact Table Grain

One row per order line item.

This design supports flexible analysis of sales, seller performance, customer behavior, delivery metrics, and cohort retention.

## dbt Transformation Layer

The dbt project is organized into two model layers:

### Staging Models

The staging layer standardizes and prepares raw OLTP tables for downstream transformation.

### Mart Models

The mart layer builds:

* dimension tables for customers, sellers, products, dates, and locations
* a fact table for order-item-level analytics

## Data Quality Testing

We implemented dbt tests to validate data quality, including:

* `not_null`
* `unique`
* `relationships`
* `accepted_values`

These tests help enforce schema consistency and referential integrity across the star schema.

## Advanced Analytical Queries

We created three advanced SQL queries to support business analytics:

### 1. Customer RFM Analysis

Segments customers based on recency, frequency, and monetary value using CTEs and window functions.

### 2. Seller Performance Dashboard Query

Ranks sellers by revenue, review percentile, and state-level performance using window functions and aggregations.

### 3. Monthly Cohort Retention Analysis

Tracks customer retention by cohort month using multiple CTEs, date logic, and window functions.

## Performance Tuning

We profiled the most complex query, `cohort_retention.sql`, using `EXPLAIN ANALYZE`.

Our performance tuning work included:

* identifying query bottlenecks
* creating indexes on strategic columns
* comparing execution behavior before and after indexing
* documenting why PostgreSQL’s optimizer selected sequential scans for this dataset size
* proposing additional tuning opportunities such as increasing `work_mem`

See:

* `docs/performance_tuning_report.pdf`

## CI/CD Workflow

We configured GitHub Actions to run automatically on pull requests to the `main` branch.

The workflow includes:

* SQL linting with SQLFluff
* dbt project validation
* dbt build
* dbt test

This ensures that SQL quality and transformation logic are checked before merging changes.

## How to Run Phase 2 Locally

### 1. Install Python dependencies

```bash
pip install dbt-core dbt-postgres sqlfluff sqlfluff-templater-dbt
````

### 2. Configure dbt profile

Update `olist_dbt/profiles.yml` with your PostgreSQL / Neon connection details, or use environment variables if configured by your team.

### 3. Run dbt debug

```bash
cd olist_dbt
dbt debug --profiles-dir .
```

### 4. Run dbt models

```bash
dbt build --profiles-dir .
```

### 5. Run dbt tests

```bash
dbt test --profiles-dir .
```

### 6. Generate dbt docs

```bash
dbt docs generate --profiles-dir .
dbt docs serve
```

## How to Run the SQL Queries

The SQL files inside the `queries/` folder can be run directly in PostgreSQL using Neon SQL Editor, pgAdmin, DBeaver, or any PostgreSQL-compatible SQL client.

## Milestone Check-in

Proof that Phase 2 deliverables work. Evidence lives in the `milestone_checkin/` folder — raw command outputs (`.txt`) for reproducibility and screenshots (`.png`) for CI runs.

### CI/CD Pipeline — Both Jobs Passing
SQLFluff lint and dbt Build & Test run automatically on every PR to `main`.

![SQL Lint succeeded](milestone_checkin/ci_sqlfluff_pass.png)
![dbt Build & Test succeeded](milestone_checkin/ci_dbt_build_pass.png)

### dbt Tests — 26/26 Passing
Data quality enforced via `not_null`, `unique`, `relationships`, and `accepted_values` tests.
See `milestone_checkin/dbt_test_output.txt` for full output.

### dbt Build — 40/40 Passing
Full pipeline build (14 models + 26 tests).
See `milestone_checkin/dbt_build_output.txt` for full output.

### Advanced Analytical Queries
Output samples from the 3 queries in `queries/` (RFM, Seller Performance, Cohort Retention).
See `milestone_checkin/analytical_queries_output.txt`.

## Secure Credential Handling

Database credentials must not be hardcoded in the repository.

For GitHub Actions:

* store secrets in **Settings > Secrets and variables > Actions**
* use repository secrets such as `DBT_PASSWORD`

For local development:

* keep sensitive values out of tracked files when possible
* use environment variables or excluded local configuration files

## Team Note

This Phase 2 repository builds directly on our Phase 1 work. The OLTP schema, ingestion pipeline, and security setup remain part of the project and support the analytics layer developed in this phase.

# Olist PostgreSQL Database Project (Phase 3)

**Application Layer: Streamlit BI Dashboard on Neon, deployed to Render**

Phase 3 turns the analytics layer from Phase 2 into a user-facing BI dashboard. The app is a multi-page Streamlit application that connects directly to the Neon Postgres database, queries the dbt mart layer (`fact_order_items` + `dim_*`) and the OLTP tables, and renders interactive visualizations. It is wired for continuous deployment to Render through `render.yaml`.

## Live Application

* **Public URL:** _add the Render URL here once deployed (e.g. `https://olist-analytics.onrender.com`)_
* **Demo video:** _link to the unlisted YouTube end-to-end demo_

> Render's free tier spins the service down after ~15 minutes of inactivity, so the first request after a quiet period can take up to 60 seconds (cold start). Subsequent requests are fast.

## Architecture

```mermaid
flowchart LR
    A[Raw CSVs<br/>data/raw/] -->|ingest_data.py| B[(Neon Postgres<br/>OLTP, 9 tables)]
    B -->|dbt build| C[(Mart layer<br/>fact_order_items + dim_*)]
    B --> D[Streamlit App<br/>app/]
    C --> D
    D -->|Render auto-deploy| E[Public URL<br/>onrender.com]
    F[GitHub Actions CI<br/>SQLFluff + dbt + AppTest] --> B
```

* OLTP layer is created by `schema.sql` and loaded idempotently by `ingest_data.py`.
* The mart layer is built by the dbt project under `olist_dbt/` (Phase 2).
* The Streamlit app reads marts for overview KPIs and OLTP tables for the RFM, seller, and cohort analyses.
* CI runs SQLFluff lint, `dbt build`/`dbt test`, and a Streamlit smoke test that executes every page against the live database.

## Application Features

### Overview (`app/Overview.py`)

* Five KPI cards: orders, customers, gross revenue, avg review, on-time delivery rate
* Date range slider that filters every chart and KPI on the page
* Monthly revenue area chart (Altair)
* Top 10 product categories bar chart
* Order status breakdown table

![Overview page](docs/screenshots/overview.png)

### RFM Analysis (`app/pages/1_RFM_Analysis.py`)

* NTILE-based RFM scoring (recency, frequency, monetary) over delivered orders
* Two threshold sliders to tighten or loosen segment definitions live
* Customers-per-segment bar chart, revenue-share donut, segment detail table

![RFM segmentation](docs/screenshots/rfm.png)

### Seller Performance (`app/pages/2_Seller_Performance.py`)

* State multiselect filter and leaderboard size slider
* KPI cards: sellers shown, combined revenue, avg review score
* Top 20 sellers bar chart, revenue-by-state chart, full ranked leaderboard

![Seller performance](docs/screenshots/seller_performance.png)

### Cohort Retention (`app/pages/3_Cohort_Retention.py`)

* Horizon slider (3–18 months since first purchase)
* Retention heatmap (cohort month × months since first purchase) with labelled cells
* Cohort size bar chart and raw cohort table

![Cohort retention](docs/screenshots/cohort_retention.png)

> Screenshots live in [`docs/screenshots/`](docs/screenshots/).

## Code Layout

```text
app/
├── Overview.py               # Entry script — appears as "Overview" in the sidebar
├── db.py                     # Cached SQLAlchemy engine + run_query helper
├── test_app.py               # AppTest smoke test for all four pages
├── pages/
│   ├── 1_RFM_Analysis.py
│   ├── 2_Seller_Performance.py
│   └── 3_Cohort_Retention.py
└── screenshots/              # README image assets
.streamlit/config.toml        # production-friendly Streamlit defaults
render.yaml                   # Render Blueprint for continuous deploy
```

## Performance & Caching

All database access goes through `app/db.py`:

* `@st.cache_resource` on the SQLAlchemy engine. One shared connection pool per app process.
* `pool_size=2`, `max_overflow=3`, `pool_recycle=300`, `pool_pre_ping=True`. Same Neon-friendly tuning as the ingest script so idle connections drop and Neon compute can pause.
* `@st.cache_data(ttl=600)` on every query function. Re-using the dashboard for 10 minutes never re-hits Neon.

A typical demo session issues only a handful of unique queries even with heavy widget interaction.

## Running the App Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set the database URL

Use the same Neon `-pooler` connection string as the ingest script.

**Linux / macOS:**

```bash
export DATABASE_URL="postgresql://user:password@ep-pooler-hostname.neon.tech/dbname?sslmode=require"
```

**Windows (PowerShell):**

```powershell
$env:DATABASE_URL="postgresql://user:password@ep-pooler-hostname.neon.tech/dbname?sslmode=require"
```

Or place it in a local `.env` file (already gitignored):

```
DATABASE_URL=postgresql://...
```

### 3. Launch Streamlit

```bash
streamlit run app/Overview.py
```

The app opens at `http://localhost:8501`. Use the sidebar to navigate between Overview, RFM Analysis, Seller Performance, and Cohort Retention.

### 4. Run the smoke test (optional)

```bash
python app/test_app.py
```

Runs every page headlessly against the live database. Fails on any uncaught exception. Useful before opening a PR.

## Cloud Deployment to Render

The repo includes a `render.yaml` Blueprint, so Render can provision the service straight from the GitHub repo with no UI clicking.

### One-time setup

1. Push `main` to GitHub (Render watches the branch configured in `render.yaml`).
2. In Render, **New → Blueprint** and point it at this repository. Render reads `render.yaml` and creates the `olist-analytics` web service.
3. In the service's **Environment** tab, set `DATABASE_URL` to the Neon pooler connection string. (`render.yaml` declares the variable with `sync: false`, so Render prompts for it instead of reading it from source.)
4. First build runs `pip install -r requirements.txt`; first start runs `streamlit run app/Overview.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`.

### After setup

Every push to `main` redeploys automatically (`autoDeploy: true` in `render.yaml`). Health checks hit `/_stcore/health` (Streamlit's built-in healthcheck endpoint).

### Credential hygiene

* `DATABASE_URL` is read by `app/db.py` from the environment first, then falls back to `st.secrets`. Nothing is hardcoded.
* `.env` is gitignored. `render.yaml` uses `sync: false` so the secret is only ever entered in the Render dashboard.
* GitHub Actions uses a `DBT_PASSWORD` repo secret (Phase 2 CI) and a `DATABASE_URL` repo secret (Phase 3 smoke test).

## CI / CD Coverage

`.github/workflows/ci.yml` runs three jobs on every PR to `main`:

| Job | What it does | Required secret |
| --- | --- | --- |
| SQL Lint (SQLFluff) | Lints all dbt SQL files | `DBT_PASSWORD` |
| dbt Build & Test | `dbt debug` → `dbt build` → `dbt test` against Neon | `DBT_PASSWORD` |
| Streamlit App Smoke Test | Runs `app/test_app.py` (executes every page via `streamlit.testing.v1.AppTest`) against Neon | `DATABASE_URL` |

If `DATABASE_URL` is not set, the smoke-test step exits 0 with a skip message instead of failing.
