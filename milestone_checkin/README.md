# Milestone Check-in

Evidence that Phase 2 deliverables work — dbt tests, CI/CD linting, and analytical queries.

## Contents

| File | What it shows |
|---|---|
| `dbt_test_output.txt` | Full `dbt test` run — 26/26 tests pass |
| `dbt_build_output.txt` | Full `dbt build` run — 14 models + 26 tests, 40/40 pass |
| `analytical_queries_output.txt` | Sample output (15 rows each) from all 3 advanced queries |
| `ci_sqlfluff_pass.png` | GitHub Actions: SQL Lint (SQLFluff) job succeeded |
| `ci_dbt_build_pass.png` | GitHub Actions: dbt Build & Test job succeeded |
| `dbt_docs_catalog.png` | (optional) Browser view of the generated dbt data catalog |

## How to regenerate

```bash
cd olist_dbt
dbt test --profiles-dir .    > ../milestone_checkin/dbt_test_output.txt 2>&1
dbt build --profiles-dir .   > ../milestone_checkin/dbt_build_output.txt 2>&1
```

For queries, any output from running the `.sql` files in `queries/` against the Neon database is sufficient evidence.
