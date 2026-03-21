# ERD (Entity-Relationship Diagram) – Crow's Foot Notation

```mermaid
erDiagram
    locations ||--o{ customers : "has"
    locations ||--o{ sellers : "has"
    customers ||--o{ orders : "places"
    product_categories |o--o{ products : "contains"
    orders ||--o{ order_items : "contains"
    products ||--o{ order_items : "appears in"
    sellers ||--o{ order_items : "fulfills"
    orders ||--o{ order_payments : "paid via"
    orders ||--o{ order_reviews : "receives"

    locations {
        VARCHAR zip_code_prefix PK
        VARCHAR city
        VARCHAR state
    }
    product_categories {
        VARCHAR category_name PK
        VARCHAR category_name_english
    }
    customers {
        VARCHAR customer_id PK
        VARCHAR customer_unique_id
        VARCHAR zip_code_prefix FK
    }
    sellers {
        VARCHAR seller_id PK
        VARCHAR zip_code_prefix FK
    }
    products {
        VARCHAR product_id PK
        VARCHAR category_name FK
        INTEGER weight_g
        INTEGER length_cm
        INTEGER height_cm
        INTEGER width_cm
    }
    orders {
        VARCHAR order_id PK
        VARCHAR customer_id FK
        VARCHAR order_status
        TIMESTAMPTZ purchase_timestamp
        TIMESTAMPTZ approved_at
        TIMESTAMPTZ delivered_carrier_date
        TIMESTAMPTZ delivered_customer_date
        TIMESTAMPTZ estimated_delivery_date
    }
    order_items {
        VARCHAR order_id PK,FK
        INTEGER order_item_id PK
        VARCHAR product_id FK
        VARCHAR seller_id FK
        TIMESTAMPTZ shipping_limit_date
        NUMERIC price
        NUMERIC freight_value
    }
    order_payments {
        VARCHAR order_id PK,FK
        INTEGER payment_sequential PK
        VARCHAR payment_type
        INTEGER payment_installments
        NUMERIC payment_value
    }
    order_reviews {
        VARCHAR review_id PK
        VARCHAR order_id PK,FK
        INTEGER review_score
        TEXT comment_title
        TEXT comment_message
        TIMESTAMPTZ creation_date
        TIMESTAMPTZ answer_timestamp
    }
```

## Entity Definitions & Attributes

### 1. **locations**
- **Primary Key:** **`zip_code_prefix`** (VARCHAR(10))
- **Attributes:** **`city`** (VARCHAR(100)), **`state`** (VARCHAR(2))

### 2. **product_categories**
- **Primary Key:** **`category_name`** (VARCHAR(100))
- **Attributes:** **`category_name_english`** (VARCHAR(100))

### 3. **customers**
- **Primary Key:** **`customer_id`** (VARCHAR(50))
- **Attributes:** **`customer_unique_id`** (VARCHAR(50)), **`zip_code_prefix`** (FK → locations)

### 4. **sellers**
- **Primary Key:** **`seller_id`** (VARCHAR(50))
- **Attributes:** **`zip_code_prefix`** (FK → locations)

### 5. **products**
- **Primary Key:** **`product_id`** (VARCHAR(50))
- **Attributes:** **`category_name`** (FK → product_categories), **`weight_g`**, **`length_cm`**, **`height_cm`**, **`width_cm`**

### 6. **orders**
- **Primary Key:** **`order_id`** (VARCHAR(50))
- **Attributes:** **`customer_id`** (FK), **`order_status`**, **`purchase_timestamp`**, **`approved_at`**, **`delivered_carrier_date`**, **`delivered_customer_date`**, **`estimated_delivery_date`**

### 7. **order_items** (Bridge/Fact Table)
- **Primary Key:** Composite (**`order_id`**, **`order_item_id`**)
- **Attributes:** **`product_id`** (FK), **`seller_id`** (FK), **`shipping_limit_date`**, **`price`**, **`freight_value`**

### 8. **order_payments**
- **Primary Key:** Composite (**`order_id`**, **`payment_sequential`**)
- **Attributes:** **`payment_type`**, **`payment_installments`**, **`payment_value`**

### 9. **order_reviews**
- **Primary Key:** Composite (**`review_id`**, **`order_id`**)
- **Attributes:** **`review_score`**, **`comment_title`**, **`comment_message`**, **`creation_date`**, **`answer_timestamp`**

---


## Relationship Descriptions

| From | To | Relationship | Cardinality | Description |
|------|---|---|---|---|
| locations | customers | FK (zip_code_prefix) | 1-to-Many | Each location can have multiple customers; each customer belongs to one location. |
| locations | sellers | FK (zip_code_prefix) | 1-to-Many | Each location can have multiple sellers; each seller belongs to one location. |
| product_categories | products | FK (category_name) | 1-to-Many | Each category contains multiple products; each product belongs to one category. |
| customers | orders | FK (customer_id) | 1-to-Many | Each customer can place multiple orders; each order belongs to one customer. |
| orders | order_items | FK (order_id) | 1-to-Many | Each order contains multiple items; each item belongs to one order. |
| products | order_items | FK (product_id) | 1-to-Many | Each product can appear in many order items; each item references one product. |
| sellers | order_items | FK (seller_id) | 1-to-Many | Each seller can fulfill many order items; each item is fulfilled by one seller. |
| orders | order_payments | FK (order_id) | 1-to-Many | Each order can have multiple payment records; each payment belongs to one order. |
| orders | order_reviews | FK (order_id) | 1-to-Many | Each order can have multiple reviews; each review belongs to one order. |


