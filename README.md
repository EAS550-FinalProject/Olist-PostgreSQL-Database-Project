# Olist PostgreSQL Database Project (Phase 1 and Phase 2)

# Olist PostgreSQL Database Project (Phase 1)

**Entity-Relationship Modeling & Cloud Data Ingestion**

Hey! Here is our implementation for Phase 1 of the E-Commerce Database Project. We took the raw Kaggle Olist dataset and turned it into a fully fleshed-out, strictly **Third Normal Form (3NF)** PostgreSQL database hosted on Neon.

## Project Demo

*Link to Unlisted YouTube Demo:* ([https://youtu.be/NfuyvZ5eZF8](https://youtu.be/NfuyvZ5eZF8))

## Project Overview & Deliverables

This phase covers everything from raw relational modeling to writing constraints and building out a Python ingestion pipeline that doesn't duplicate data.

**What's inside:**

1. **`ERD.md`** and **`Olist Database ERD.pdf`**: Our Crow's Foot diagram showing how everything maps together logically.
2. **`schema.sql`**: The DDL script we wrote to provision the actual tables in Postgres.
3. **`3nf_report.pdf`**: Our write-up explaining why we made certain normalization choices and how they prevent common database anomalies.
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

2. **`star_schema_diagram.md`**
   Documentation of the star schema design, including the fact table, dimension tables, grain, and design rationale.

3. **`queries/`**
   Advanced analytical SQL queries:

   * `rfm_analysis.sql`
   * `seller_performance.sql`
   * `cohort_retention.sql`

4. **`performance_tuning_report.md`**
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
├── performance_tuning_report.md
├── star_schema_diagram.md
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

* `performance_tuning_report.md`

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
