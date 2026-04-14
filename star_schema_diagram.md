# Olist Star Schema Diagram

## Overview
This star schema transforms the Olist OLTP database (3NF) into an optimized analytical model with one fact table and five dimension tables.

```mermaid
erDiagram
    fact_order_items {
        varchar order_id FK
        int order_item_id
        varchar product_id FK
        varchar seller_id FK
        varchar customer_id FK
        date order_date_key FK
        varchar order_status
        timestamp order_purchase_timestamp
        timestamp order_approved_at
        timestamp order_delivered_carrier_date
        timestamp order_delivered_customer_date
        timestamp order_estimated_delivery_date
        numeric price
        numeric freight_value
        numeric total_item_value
        numeric order_payment_value
        int payment_count
        varchar payment_types
        numeric avg_review_score
        int review_count
        boolean delivered_on_time
    }

    dim_customers {
        varchar customer_id PK
        varchar customer_unique_id
        varchar zip_code_prefix
        varchar customer_city
        varchar customer_state
    }

    dim_sellers {
        varchar seller_id PK
        varchar zip_code_prefix
        varchar seller_city
        varchar seller_state
    }

    dim_products {
        varchar product_id PK
        varchar product_category
        int product_name_length
        int product_description_length
        int product_photos_qty
        int product_weight_g
        int product_length_cm
        int product_height_cm
        int product_width_cm
    }

    dim_dates {
        date date_key PK
        int year
        int quarter
        int month
        int day
        int day_of_week
        varchar day_name
        varchar month_name
        boolean is_weekend
    }

    dim_locations {
        varchar zip_code_prefix PK
        varchar city
        varchar state
    }

    fact_order_items ||--o{ dim_customers : "customer_id"
    fact_order_items ||--o{ dim_sellers : "seller_id"
    fact_order_items ||--o{ dim_products : "product_id"
    fact_order_items ||--o{ dim_dates : "order_date_key"
    dim_customers ||--o{ dim_locations : "zip_code_prefix"
    dim_sellers ||--o{ dim_locations : "zip_code_prefix"
```

## Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Grain** | One row per order line item | Most granular level; supports any aggregation |
| **Fact Type** | Transaction fact table | Each row represents a business event (item sold) |
| **Date Dimension** | Generated from order timestamps | Covers only dates with actual orders |
| **Location** | Shared dimension for customers & sellers | Avoids duplication of geographic data |
| **Payments** | Aggregated to order level in fact | Payments are per-order, not per-item |
| **Reviews** | Averaged to order level in fact | Reviews are per-order, not per-item |
| **Materialization** | Dimensions & fact as tables; staging as views | Tables for query performance; views for freshness |
