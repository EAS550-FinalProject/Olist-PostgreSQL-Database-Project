# Third Normal Form (3NF) Justification Report

## Executive Summary

This report documents the normalization of the Olist e-commerce dataset into Third Normal Form (3NF). The schema eliminates redundancy, prevents insert/update/delete anomalies, and ensures data integrity. All entities are in 3NF, with carefully resolved many-to-many relationships through associative tables.

---

## Part 1: Normalization Theory Review

### First Normal Form (1NF)
**Definition:** All attributes contain atomic (indivisible) values. No repeating groups or nested structures.

**Application to this schema:**
- CSV data is flattened into single-relation tables.
- Fields like timestamps are converted to atomic `TIMESTAMPTZ` type (not JSON/arrays).
- Address components (city, state, zip_code_prefix) are stored as separate atomic fields (not combined strings).
- Financial values are stored as `NUMERIC(10,2)` (atomic decimal, not strings).

**Evidence of 1NF compliance:**
```sql
-- Example: All attributes are atomic
CREATE TABLE orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    order_status VARCHAR(20) NOT NULL,
    purchase_timestamp TIMESTAMPTZ NOT NULL,
    approved_at TIMESTAMPTZ,
    -- ... no nested objects or repeating groups
);
```

---

### Second Normal Form (2NF)
**Definition:** Must be in 1NF AND all non-key attributes must depend on the *entire* primary key (not just part of it).

**Application to this schema:**

#### Single-key tables (inherently 2NF):
- `locations(zip_code_prefix)` – city and state depend on the entire PK.
- `product_categories(category_name)` – category_name_english depends on the entire PK.
- `customers(customer_id)` – customer_unique_id and zip_code_prefix depend on the entire PK.
- `sellers(seller_id)` – zip_code_prefix depends on the entire PK.
- `products(product_id)` – all physical attributes depend on the entire PK.
- `orders(order_id)` – all timestamps and status depend on the entire PK.

#### Composite-key tables (carefully verified):
- **order_items(order_id, order_item_id):**
  - `product_id` depends on BOTH order_id AND order_item_id (the specific item in a specific order).
  - `seller_id` depends on BOTH (each order item is fulfilled by a specific seller).
  - `price` depends on BOTH (price can vary per item even within an order).
  - `freight_value` depends on BOTH (freight is item-specific).
  - ✓ No partial dependencies.

- **order_payments(order_id, payment_sequential):**
  - `payment_type`, `payment_installments`, `payment_value` all depend on BOTH the order and payment sequence.
  - ✓ No partial dependencies.

- **order_reviews(review_id, order_id):**
  - `review_score`, `comment_title`, `comment_message`, `creation_date`, `answer_timestamp` all depend on BOTH the review and order context.
  - ✓ No partial dependencies.

**Evidence of 2NF compliance:** No non-key attribute depends on only part of a composite key.

---

### Third Normal Form (3NF)
**Definition:** Must be in 2NF AND no non-key attribute can depend on another non-key attribute (no transitive dependencies).

**Application to this schema:**

#### Identifying potential transitive dependencies:

**Scenario 1: Location hierarchy**
- *Raw data:* Customer has zip → city → state (transitive chain)
- *Problem:* If city and state were stored directly in customers table, updating a city name could require updating many customer records.
- *Solution:* Extract to `locations(zip_code_prefix, city, state)` table. Customers now reference only zip_code_prefix.
- *Result:* ✓ No transitive dependency; city/state are facts about location, not customer.

**Scenario 2: Product dimensions**
- *Considered:* Should product weight/dimensions be in a separate table?
- *Decision:* No. Weight and length are intrinsic properties of a product, not derived values. Keeping them in `products` avoids unnecessary joins.
- *Result:* ✓ All attributes directly describe the product entity.

**Scenario 3: Price data**
- *Raw data:* Order has items with per-item prices; order has total value (potentially derived).
- *Problem:* If we stored order_total in orders table, it would depend on order_items records (transitive dependency).
- *Solution:* Only store item-level prices in `order_items`. Order-level totals are computed/derived on demand.
- *Result:* ✓ No stored transitive dependency; actual totals are computed via SUM() in queries.

**Scenario 4: Category translations**
- *Raw data:* Products have Portuguese category names; category translations provide English names.
- *Problem:* If we stored category_name_english directly in products, and that value changed, we'd have redundancy across many product rows.
- *Solution:* Store translations only in `product_categories`, and products reference by category_name.
- *Result:* ✓ No transitive dependency; translations are facts about categories, not products.

**Detailed 3NF verification by table:**

| Table | Non-key Attributes | Dependencies | Transitive? |
|-------|---|---|---|
| locations | city, state | Depend on zip_code_prefix (PK) | ✗ No |
| product_categories | category_name_english | Depends on category_name (PK) | ✗ No |
| customers | customer_unique_id, zip_code_prefix | Depend on customer_id (PK); zip_code_prefix is FK to independent locations table | ✗ No |
| sellers | zip_code_prefix | Depends on seller_id (PK); zip_code_prefix is FK to independent locations table | ✗ No |
| products | category_name, weight_g, length_cm, height_cm, width_cm | All depend on product_id (PK); category_name is FK to independent product_categories table | ✗ No |
| orders | customer_id, order_status, purchase_timestamp, approved_at, delivered_carrier_date, delivered_customer_date, estimated_delivery_date | All depend on order_id (PK); customer_id is FK to independent customers table | ✗ No |
| order_items | product_id, seller_id, shipping_limit_date, price, freight_value | All depend on (order_id, order_item_id) composite key | ✗ No |
| order_payments | payment_type, payment_installments, payment_value | All depend on (order_id, payment_sequential) composite key | ✗ No |
| order_reviews | review_score, comment_title, comment_message, creation_date, answer_timestamp | All depend on (review_id, order_id) composite key | ✗ No |

✓ **All tables are 3NF compliant.**

---

## Part 2: Data Anomalies Prevention

### Insert Anomalies
**Problem:** Cannot insert certain data without inserting unrelated data.

**Example (Bad Design):**
```
If orders table stored: order_id, customer_id, customer_name, customer_zip, city, state, ...
Then to add a new order, we'd be forced to store/duplicate customer info even if that customer exists.
```

**Solution in 3NF Schema:**
- Customer info is in `customers` table; orders reference it via FK.
- Insert a new order without duplicating customer data: `INSERT INTO orders (order_id, customer_id, ...) VALUES (...)`
- ✓ Customer can be inserted independently; order can reference existing customer.

### Update Anomalies
**Problem:** Updating one fact requires updating all redundant copies, risking inconsistency.

**Example (Bad Design):**
```
If product_categories were denormalized into products table:
UPDATE products SET category_name_english = 'New Name' WHERE category_name = 'old_name'
-- Would need to update 100+ product rows if that category appears many times.
-- Risk: Some updates succeed, some fail; inconsistent state.
```

**Solution in 3NF Schema:**
- Category translations live in `product_categories` table.
- Update once: `UPDATE product_categories SET category_name_english = 'New Name' WHERE category_name = 'old_name'`
- ✓ All products automatically see the updated translation via FK reference.

### Delete Anomalies
**Problem:** Deleting some data unintentionally loses other data.

**Example (Bad Design):**
```
If locations (city/state) were stored in customers:
DELETE FROM customers WHERE customer_id = 'C123'
-- Loses the only record that city = 'São Paulo' existed, even if other customers live there.
```

**Solution in 3NF Schema:**
- Delete customer: `DELETE FROM customers WHERE customer_id = 'C123'`
- Location remains in independent `locations` table.
- ✓ Geography data is preserved; only customer association is removed.

---

## Part 3: Many-to-Many Relationship Resolution

### The Problem: Orders ↔ Products

**Raw scenario:**
- One order contains multiple products.
- One product can appear across multiple orders.
- This is **many-to-many** and cannot be directly represented in a single table without redundancy.

**Bad approach (denormalized):**
```sql
-- DO NOT USE THIS
CREATE TABLE orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    product_ids TEXT, -- "prod_A|prod_B|prod_C" -- BAD: not atomic
    prices TEXT,      -- "100|200|150"
    sellers TEXT,     -- "seller1|seller2|seller3"
    ...
);
-- Problems: Parsing complexity, no FK constraint, data anomalies.
```

**3NF solution (associative table):**
```sql
CREATE TABLE order_items (
    order_id VARCHAR(50),
    order_item_id INTEGER,
    product_id VARCHAR(50) NOT NULL,
    seller_id VARCHAR(50) NOT NULL,
    shipping_limit_date TIMESTAMPTZ NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    freight_value NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);
```

**Benefits:**
- ✓ Each order-product pair is represented exactly once.
- ✓ Item-specific price and freight (they vary per item, not per product globally).
- ✓ Seller is recorded per item (same order may have items from different sellers).
- ✓ Full referential integrity via FKs.
- ✓ Easy to query: `SELECT p.*, oi.price FROM products p JOIN order_items oi ON p.product_id = oi.product_id WHERE oi.order_id = 'O123'`

---

## Part 4: Constraint Enforcement for Data Quality

### Primary Keys
Ensure unique identification and immutability of entities.
```sql
PRIMARY KEY (order_id) -- Single key on orders
PRIMARY KEY (order_id, order_item_id) -- Composite key on order_items; each item unique per order
```

### Foreign Keys
Enforce referential integrity; prevent orphans and enable dependency tracking.
```sql
FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
-- Guarantees every order references a valid customer
FOREIGN KEY (product_id) REFERENCES products(product_id)
-- Guarantees every order item references a real product
```

### NOT NULL Constraints
Identify and enforce required fields.
```sql
order_status VARCHAR(20) NOT NULL -- Every order must have a status
purchase_timestamp TIMESTAMPTZ NOT NULL -- Every order must have a purchase time
price NUMERIC(10,2) NOT NULL CHECK (price >= 0) -- Item price is mandatory and non-negative
```

### CHECK Constraints
Enforce domain-specific business rules.
```sql
CHECK (price >= 0) -- Price cannot be negative
CHECK (freight_value >= 0) -- Freight cost cannot be negative
CHECK (weight_g >= 0) -- Weight cannot be negative
CHECK (review_score BETWEEN 1 AND 5) -- Review scores range 1–5
CHECK (payment_installments >= 0) -- Installments count cannot be negative
```

### UNIQUE Constraints
Ensure non-key uniqueness where needed.
```sql
-- Implicit in PRIMARY KEY definitions; no additional UNIQUE constraints needed for this design.
```

---

## Part 5: ETL Idempotency & Data Loading

To ensure the schema remains in 3NF during data ingestion, the Python script enforces:

1. **Deduplication before insert:**
   ```python
   df.drop_duplicates(subset=["product_id"], keep="first", inplace=True)
   ```
   Removes duplicates in memory before any database operation.

2. **ON CONFLICT DO NOTHING:**
   ```python
   stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)
   ```
   If a record already exists (by PK), silently skip it. Idempotent: running the script multiple times produces the same result.

3. **Type coercion to schema:**
   ```python
   df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
   df[col] = pd.to_datetime(df[col], errors="coerce")
   ```
   Ensures all data matches table column types (no type mismatches that could corrupt integrity).

4. **Load order respects FKs:**
   - Insert `locations` first (referenced by customers, sellers).
   - Insert `product_categories` next (referenced by products).
   - Insert `customers`, `sellers`, `products` (depend on locations/categories).
   - Insert `orders` (depends on customers).
   - Insert `order_items`, `order_payments`, `order_reviews` (depend on orders and referenced tables).

---

## Part 6: Conclusion

The Olist database schema is **fully normalized to Third Normal Form (3NF)**:

✓ **1NF:** All attributes are atomic; no repeating groups.
✓ **2NF:** All non-key attributes depend on entire primary keys; no partial dependencies.
✓ **3NF:** No transitive dependencies between non-key attributes; master-detail pattern cleanly separates concerns.

✓ **Anomalies prevented:**
- Insert anomalies avoided via independent master tables.
- Update anomalies avoided via single-authority principle (each fact in one place).
- Delete anomalies avoided via proper FK relationships without cascading deletes.

✓ **Many-to-many relationships resolved:**
- Orders ↔ Products decomposed via `order_items` bridge table.
- Orders ↔ Sellers linked through `order_items`.

✓ **Data integrity enforced:**
- PKs/FKs guarantee referential integrity.
- NOT NULL, CHECK constraints enforce business rules.
- ETL script ensures idempotent loading with type validation.

This design is production-ready, scalable, and resistant to the common database anomalies that plague poorly normalized schemas.

