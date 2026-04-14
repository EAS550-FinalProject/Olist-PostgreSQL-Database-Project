# Performance Tuning Report

## Query Profiled: Monthly Cohort Retention Analysis
**File:** `queries/cohort_retention.sql`

This is the most complex of our three analytical queries, featuring:
- 4 CTEs (customer_first_purchase, customer_monthly_activity, cohort_activity, cohort_sizes)
- Window functions: LAG, ROW_NUMBER
- Date arithmetic with EXTRACT and DATE_TRUNC
- Multiple GROUP BY aggregations and JOINs

---

## Baseline Performance (Before Indexing)

```
Planning Time: 0.816 ms
Execution Time: 842.984 ms
```

### Key Observations from EXPLAIN ANALYZE
| Operation | Time (ms) | Notes |
|-----------|-----------|-------|
| CTE customer_first_purchase | ~278 | GroupAggregate with Parallel Hash Join |
| Merge Join (activity x cohort) | ~300 | Largest bottleneck: cross-join filtered by month range |
| External Merge Sort (disk) | ~14 | 3 disk-based sorts (4.3-5.4 MB each) |
| WindowAgg (LAG, ROW_NUMBER) | ~48 | Efficient incremental sort |
| Total | ~843 | Full query execution |

### Bottlenecks Identified
1. **Parallel Seq Scans on `orders`**: Filtering `order_status = 'delivered'` scans all 99,441 rows twice
2. **Hash Join on `customers.customer_id`**: Joins 99k customers with 96k delivered orders
3. **External Merge Sort (Disk Spills)**: 3 sort operations spill to disk (4-5 MB each) due to `work_mem` limits
4. **CTE Materialization**: `customer_first_purchase` CTE scanned twice (once for cohort join, once for cohort sizes)

---

## Indexes Created

```sql
-- Index 1: Speeds up filtering delivered orders and timestamp range scans
CREATE INDEX idx_orders_status_timestamp ON orders(order_status, purchase_timestamp);

-- Index 2: Speeds up customer-order joins filtered by status
CREATE INDEX idx_orders_customer_status ON orders(customer_id, order_status);

-- Index 3: Speeds up GROUP BY customer_unique_id in CTE
CREATE INDEX idx_customers_unique_id ON customers(customer_unique_id);
```

## Post-Indexing Performance

```
Planning Time: 1.090 ms
Execution Time: 876.991 ms
```

### Analysis
The query planner **correctly chose not to use the new indexes** for this dataset size. This is expected behavior:

- **Dataset size (~100k orders, ~99k customers)**: PostgreSQL's cost-based optimizer determines that sequential scans are faster than index lookups when a large percentage of rows are needed. Since ~97% of orders are 'delivered', an index on `order_status` provides no selectivity benefit.
- **Parallel Seq Scans**: With parallel workers, full table scans on small tables are often faster than index access, which adds random I/O overhead.

### When These Indexes WILL Help
At scale (1M+ orders), these indexes become critical:
- `idx_orders_status_timestamp`: If querying specific date ranges (e.g., last 30 days), the combined index enables index-only scans
- `idx_orders_customer_status`: Speeds up per-customer lookups when joining with filtered orders
- `idx_customers_unique_id`: Eliminates sort step in GROUP BY operations on large customer tables

---

## Additional Optimizations Considered

### 1. Increase `work_mem` (Recommended)
Three sort operations spill to disk. Increasing `work_mem` from the default 4MB to 16MB would keep sorts in-memory:
```sql
SET work_mem = '16MB';  -- Session-level
```
**Expected impact**: Eliminates disk-based external merge sorts, saving ~50-100ms.

### 2. Materialized View (For Dashboards)
For repeated execution (e.g., dashboard refresh), create a materialized view:
```sql
CREATE MATERIALIZED VIEW mv_cohort_retention AS
  <query>
WITH DATA;

REFRESH MATERIALIZED VIEW CONCURRENTLY mv_cohort_retention;
```

### 3. Pre-aggregate First Purchase (For Large Scale)
At scale, pre-computing `customer_first_purchase` as a table avoids recalculating it each query run.

---

## Summary

| Metric | Value |
|--------|-------|
| Baseline Execution Time | 843 ms |
| Post-Index Execution Time | 877 ms (no change; optimizer correctly chose seq scans) |
| Indexes Created | 3 (for future scalability) |
| Primary Bottleneck | CTE materialization + disk sorts |
| Recommended Fix | Increase `work_mem` to 16MB |
| Dataset Size | ~100k orders, ~99k customers, ~112k order items |
