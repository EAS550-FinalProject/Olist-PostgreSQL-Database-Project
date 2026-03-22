# Olist PostgreSQL Database Project (Phase 1)
**Entity-Relationship Modeling & Cloud Data Ingestion**

Hey! Here is our implementation for Phase 1 of the E-Commerce Database Project. We took the raw Kaggle Olist dataset and turned it into a fully fleshed-out, strictly **Third Normal Form (3NF)** PostgreSQL database hosted on Neon.

## Project Demo
*Link to Unlisted YouTube Demo:* (https://youtu.be/almtUcIKs9A)

## Project Overview & Deliverables
This phase covers everything from raw relational modeling to writing constraints and building out a Python ingestion pipeline that doesn't duplicate data. 

**What's inside:**
1.  **`ERD.md`**: Our Crow's Foot diagram showing how everything maps together logically.
2.  **`schema.sql`**: The DDL script we wrote to provision the actual tables in Postgres.
3.  **`3nf_report.md`**: Our write-up explaining why we made certain normalization choices and how they prevent common database anomalies.
4.  **`ingest_data.py`**: A Pandas/SQLAlchemy ETL script. We made sure it's fully idempotent, meaning you can run it as many times as you want without messing up the database.
5.  **`security.sql`** *(Bonus)*: A quick Role-Based Access Control setup we added to separate read-only analysts from an app user that can actually insert data.

## Folder Structure
```text
.
├── data/
│   └── raw/               <-- Drop your Kaggle CSVs in here             
├── ingest_data.py         
├── README.md              
├── requirements.txt       
├── schema.sql             
├── security.sql           
└── .gitignore             
```
## Dataset Source
We used the Brazilian E-Commerce Public Dataset by Olist. It contains around 100k anonymized orders from 2016 to 2018.
*   **You can grab it here:** [Olist E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
*   **Local Setup:** Just unzip the CSVs right into `./data/raw/` at the root of the project.

---

## How to Run It

### 1. Setting up Neon Postgres
1.  Make a free serverless project over at [Neon.tech](https://neon.tech/).
2.  Go to your Neon Dashboard and find your **Connection Details**.
3.  Grab both your **Direct Connection** (for the SQL scripts) and your **Pooled Connection** (the one with `-pooler` in the host, for the Python script).

### 2. Deploying the Schema
Pop open DBeaver, pgAdmin, or just the Neon SQL Editor, and run these against your *Direct Connection*:
1.  **`schema.sql`:** This builds all 9 tables, sets up my foreign keys, and adds some indexes. If you need to wipe and restart, it safely drops everything first.
2.  **`security.sql`:** This gives you an `analyst_role` (read-only) and an `app_user_role` (can insert/update, but intentionally can't `DELETE` stuff). 

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
*   **Pandas Cleanup:** We explicitly run drop_duplicates on the primary keys in memory first.
*   **Postgres `ON CONFLICT`:** SQLAlchemy maps the tables and writes INSERT INTO ... ON CONFLICT (pk) DO NOTHING. So if a row is already in the database, Postgres simply ignores it.

### 5. Secure Credential Handling (GitHub Secrets)
To ensure that no database credentials are hardcoded in the repository, we store the database connection string securely using environment variables for local development and GitHub Secrets for repository automation.

For GitHub:
1. Go to your repo **Settings** > **Secrets and variables** > **Actions**.
2. Add a **New repository secret** called `DATABASE_URL`.
3. Paste your pooled Neon connection string as the value.

For local development:
- Store the same connection string in a local `.env` file.
- Make sure `.env` is included in `.gitignore` so it is not committed.

This keeps credentials out of the codebase and aligns with the Phase 1 security requirement.

---

## Neon Free-Tier Warning 
Since Neon suspends databases to save compute hours, leaving a pool of connections open will keep the database awake and literally eat your entire free-tier quota in days.

To avoid this, I specifically tuned SQLAlchemy in `ingest_data.py`:
*   **`pool_size=2` & `max_overflow=5`**: Keeps the connection count super low.
*   **`pool_recycle=300`**: Kills any dormant connection older than 5 minutes so Neon can go to sleep when we're not actively ingesting.
*   **`pool_pre_ping=True`**: Double-checks if the connection is alive before firing a query, which stops cold-start crashes.