# Phase 2 Milestone Check-in

Evidence that Phase 2 is working: dbt models build, data quality tests pass, CI/CD runs on PRs, and the three analytical queries return results against the live Neon database.

## Summary

- 14 dbt models (8 staging, 5 dimensions, 1 fact table)
- 26 dbt tests, all passing
- `dbt build` completes with 40/40 successful (models + tests)
- SQLFluff linting passes
- GitHub Actions: both SQL Lint and dbt Build & Test jobs succeed on PRs
- All 3 analytical queries run successfully

## CI/CD Pipeline

The workflow in `.github/workflows/ci.yml` runs two jobs on every pull request to `main`.

SQL Lint (SQLFluff):

![SQL Lint Passing](./ci_sqlfluff_pass.png)

dbt Build & Test:

![dbt Build & Test Passing](./ci_dbt_build_pass.png)

## dbt Tests

Tests include `not_null`, `unique`, `relationships` (referential integrity), and `accepted_values` on `order_status`.

Final output from `dbt test`:

```
Finished running 26 data tests in 0 hours 0 minutes and 12.13 seconds (12.13s).
Completed successfully
Done. PASS=26 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=26
```

Full log: [`dbt_test_output.txt`](./dbt_test_output.txt)

## dbt Build

`dbt build` runs all models and tests together.

```
Finished running 6 table models, 26 data tests, 8 view models in 0 hours 0 minutes and 17.19 seconds (17.19s).
Completed successfully
Done. PASS=40 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=40
```

Full log: [`dbt_build_output.txt`](./dbt_build_output.txt)

## dbt Data Catalog

Generated with `dbt docs generate` and viewed via `dbt docs serve`.

![dbt Data Catalog](./dbt_docs_catalog.png)

To view locally:
```
cd olist_dbt
dbt docs serve --profiles-dir .
```

## Analytical Queries

Three queries in the `queries/` folder, each using CTEs and window functions. Full output in [`analytical_queries_output.txt`](./analytical_queries_output.txt).

### Query 1 — RFM Customer Segmentation
Uses NTILE(4) to score customers on Recency, Frequency, and Monetary dimensions.

| customer_segment | customer_count | avg_recency_days | avg_total_spent |
|---|---|---|---|
| Champions | 23531 | 159.7 | 267.67 |
| At Risk | 22848 | 412.1 | 266.96 |
| Potential Loyalists | 314 | 170.1 | 138.00 |
| Loyal Customers | 11559 | 159.3 | 82.93 |
| Others | 29111 | 296.4 | 60.02 |
| Lost | 5995 | 502.5 | 45.48 |

### Query 2 — Seller Performance Dashboard
Uses RANK(), PERCENT_RANK(), and a rolling 5-seller average. Top 5 by revenue:

| rank | seller_id (prefix) | city | state | total_revenue | avg_review_score |
|---|---|---|---|---|---|
| 1 | 4869f7a5 | guariba | SP | 226987.93 | 4.14 |
| 2 | 53243585 | lauro de freitas | BA | 217940.44 | 4.13 |
| 3 | 4a3ca931 | ibitinga | SP | 199408.32 | 3.83 |
| 4 | fa1c13f2 | sumare | SP | 190917.14 | 4.37 |
| 5 | 7c67e144 | itaquaquecetuba | SP | 188063.83 | 3.35 |

### Query 3 — Monthly Cohort Retention
Uses LAG() and ROW_NUMBER() to track retention by acquisition cohort. Returns 188 rows covering the first 13 months of each cohort.

## Files

| File | Description |
|---|---|
| `ci_sqlfluff_pass.png` | GitHub Actions: SQL Lint success |
| `ci_dbt_build_pass.png` | GitHub Actions: dbt Build & Test success |
| `dbt_docs_catalog.png` | dbt docs catalog view |
| `dbt_test_output.txt` | Full `dbt test` log |
| `dbt_build_output.txt` | Full `dbt build` log |
| `analytical_queries_output.txt` | Output from all 3 queries |

## How to Regenerate

```
cd olist_dbt
export DBT_PASSWORD="<password>"

dbt test --profiles-dir . > ../milestone_checkin/dbt_test_output.txt 2>&1
dbt build --profiles-dir . > ../milestone_checkin/dbt_build_output.txt 2>&1
dbt docs generate --profiles-dir .
```

Analytical queries live in `../queries/` and run against the Neon database.
