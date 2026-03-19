-- Drop existing tables if they exist to allow clean recreation
DROP TABLE IF EXISTS order_reviews CASCADE;
DROP TABLE IF EXISTS order_payments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS sellers CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS product_categories CASCADE;
DROP TABLE IF EXISTS locations CASCADE;

-- Master table for geographic data (ZIP codes, cities, states)
CREATE TABLE IF NOT EXISTS locations (
    zip_code_prefix VARCHAR(10) PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL
);

-- Master table for product categories and their English translations
CREATE TABLE IF NOT EXISTS product_categories (
    category_name VARCHAR(100) PRIMARY KEY,
    category_name_english VARCHAR(100)
);

-- Master table for customers; references locations by zip code
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50) NOT NULL,
    zip_code_prefix VARCHAR(10) NOT NULL,
    FOREIGN KEY (zip_code_prefix) REFERENCES locations(zip_code_prefix)
);

-- Registry of sellers; references locations by zip code
CREATE TABLE IF NOT EXISTS sellers (
    seller_id VARCHAR(50) PRIMARY KEY,
    zip_code_prefix VARCHAR(10) NOT NULL,
    FOREIGN KEY (zip_code_prefix) REFERENCES locations(zip_code_prefix)
);

-- Product catalog including physical dimensions for shipping
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    category_name VARCHAR(100),
    weight_g INTEGER CHECK (weight_g >= 0),
    length_cm INTEGER CHECK (length_cm >= 0),
    height_cm INTEGER CHECK (height_cm >= 0),
    width_cm INTEGER CHECK (width_cm >= 0),
    FOREIGN KEY (category_name) REFERENCES product_categories(category_name)
);

-- Core transaction table tracking order lifecycle; references customer
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    order_status VARCHAR(20) NOT NULL,
    purchase_timestamp TIMESTAMPTZ NOT NULL,
    approved_at TIMESTAMPTZ,
    delivered_carrier_date TIMESTAMPTZ,
    delivered_customer_date TIMESTAMPTZ,
    estimated_delivery_date TIMESTAMPTZ,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Bridge table resolving many-to-many relationship between orders and products
-- Each record is a specific item in an order, fulfilled by a specific seller
CREATE TABLE IF NOT EXISTS order_items (
    order_id VARCHAR(50),
    order_item_id INTEGER,
    product_id VARCHAR(50) NOT NULL,
    seller_id VARCHAR(50) NOT NULL,
    shipping_limit_date TIMESTAMPTZ NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    freight_value NUMERIC(10, 2) NOT NULL CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);

-- Records payment details for an order (an order can have multiple payments)
CREATE TABLE IF NOT EXISTS order_payments (
    order_id VARCHAR(50),
    payment_sequential INTEGER,
    payment_type VARCHAR(20) NOT NULL,
    payment_installments INTEGER NOT NULL CHECK (payment_installments >= 0),
    payment_value NUMERIC(10, 2) NOT NULL CHECK (payment_value >= 0),
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Customer feedback/reviews for orders
CREATE TABLE IF NOT EXISTS order_reviews (
    review_id VARCHAR(50),
    order_id VARCHAR(50),
    review_score INTEGER NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    comment_title TEXT,
    comment_message TEXT,
    creation_date TIMESTAMPTZ NOT NULL,
    answer_timestamp TIMESTAMPTZ,
    PRIMARY KEY (review_id, order_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Create indexes for performance optimization on frequently filtered columns and foreign keys
CREATE INDEX idx_customers_zip ON customers(zip_code_prefix);
CREATE INDEX idx_sellers_zip ON sellers(zip_code_prefix);
CREATE INDEX idx_products_category ON products(category_name);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_purchase_date ON orders(purchase_timestamp);

CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_order_items_seller ON order_items(seller_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);

CREATE INDEX idx_order_payments_order ON order_payments(order_id);
CREATE INDEX idx_order_reviews_order ON order_reviews(order_id);
