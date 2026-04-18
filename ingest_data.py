import os
import sys
import logging
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
import streamlit as st
from dotenv import load_dotenv


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL")
if not DATABASE_URL:
    logging.error("DATABASE_URL is not set.")
    sys.exit(1)

engine = create_engine(
    DATABASE_URL,
    pool_size=2,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=300,
    pool_pre_ping=True
)

metadata = MetaData()
DATA_DIR = "./data/raw"


def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        logging.warning(f"Missing file: {path}")
        return None
    try:
        logging.info(f"Loading {filename}")
        return pd.read_csv(path)
    except Exception as e:
        logging.error(f"Could not read {filename}: {e}")
        return None


def clean_dataframe(df):
    if df is None or df.empty:
        return None
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.astype(object)
    df = df.where(pd.notnull(df), None)
    return df


def idempotent_insert(table_name, df, conflict_cols=None):
    if df is None or df.empty:
        logging.info(f"[{table_name}] No rows to insert.")
        return

    table = Table(table_name, metadata, autoload_with=engine)
    records = df.to_dict(orient="records")
    
    # Batch insert in chunks to avoid timeout
    batch_size = 5000
    total_rows = len(records)
    
    for i in range(0, total_rows, batch_size):
        batch = records[i:i+batch_size]
        
        with engine.begin() as conn:
            stmt = insert(table).values(batch)

            if conflict_cols is None:
                conflict_cols = [col.name for col in table.primary_key]

            if not conflict_cols:
                conn.execute(stmt)
                logging.warning(f"[{table_name}] Batch {i//batch_size + 1} inserted without conflict handling.")
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)
                conn.execute(stmt)
                logging.info(f"[{table_name}] Batch {i//batch_size + 1}: Processed {len(batch)} rows (total: {min(i+batch_size, total_rows)}/{total_rows}).")


def process_locations(df_customers, df_sellers):
    parts = []

    if df_customers is not None and not df_customers.empty:
        x = df_customers[["customer_zip_code_prefix", "customer_city", "customer_state"]].copy()
        x.rename(
            columns={
                "customer_zip_code_prefix": "zip_code_prefix",
                "customer_city": "city",
                "customer_state": "state"
            },
            inplace=True
        )
        parts.append(x)

    if df_sellers is not None and not df_sellers.empty:
        x = df_sellers[["seller_zip_code_prefix", "seller_city", "seller_state"]].copy()
        x.rename(
            columns={
                "seller_zip_code_prefix": "zip_code_prefix",
                "seller_city": "city",
                "seller_state": "state"
            },
            inplace=True
        )
        parts.append(x)

    if not parts:
        logging.info("[locations] No data to process.")
        return

    df = pd.concat(parts, ignore_index=True)
    df.drop_duplicates(subset=["zip_code_prefix"], keep="first", inplace=True)
    idempotent_insert("locations", clean_dataframe(df))


def process_product_categories(df_translation, df_products):
    parts = []

    if df_products is not None and not df_products.empty:
        x = df_products[["product_category_name"]].copy()
        x.rename(columns={"product_category_name": "category_name"}, inplace=True)
        x["category_name_english"] = None
        parts.append(x)

    if df_translation is not None and not df_translation.empty:
        y = df_translation.copy()
        y.rename(
            columns={
                "product_category_name": "category_name",
                "product_category_name_english": "category_name_english"
            },
            inplace=True
        )
        parts.append(y)

    if not parts:
        logging.info("[product_categories] No data to process.")
        return

    df = pd.concat(parts, ignore_index=True)

    df["category_name"] = df["category_name"].astype("string").str.strip()
    df.loc[df["category_name"] == "", "category_name"] = pd.NA

    df["category_name_english"] = df["category_name_english"].astype("string").str.strip()
    df.loc[df["category_name_english"] == "", "category_name_english"] = pd.NA

    df = df[df["category_name"].notna()].copy()

    df.sort_values(by=["category_name_english"], inplace=True, na_position="last")
    df.drop_duplicates(subset=["category_name"], keep="first", inplace=True)

    idempotent_insert("product_categories", clean_dataframe(df))


def process_customers(df):
    if df is None or df.empty:
        logging.info("[customers] No data to process.")
        return

    df = df[["customer_id", "customer_unique_id", "customer_zip_code_prefix"]].copy()
    df.rename(columns={"customer_zip_code_prefix": "zip_code_prefix"}, inplace=True)
    df.drop_duplicates(subset=["customer_id"], keep="first", inplace=True)
    idempotent_insert("customers", clean_dataframe(df))


def process_sellers(df):
    if df is None or df.empty:
        logging.info("[sellers] No data to process.")
        return

    df = df[["seller_id", "seller_zip_code_prefix"]].copy()
    df.rename(columns={"seller_zip_code_prefix": "zip_code_prefix"}, inplace=True)
    df.drop_duplicates(subset=["seller_id"], keep="first", inplace=True)
    idempotent_insert("sellers", clean_dataframe(df))


def process_products(df):
    if df is None or df.empty:
        logging.info("[products] No data to process.")
        return

    df = df[
        [
            "product_id",
            "product_category_name",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm"
        ]
    ].copy()

    df.rename(
        columns={
            "product_category_name": "category_name",
            "product_weight_g": "weight_g",
            "product_length_cm": "length_cm",
            "product_height_cm": "height_cm",
            "product_width_cm": "width_cm"
        },
        inplace=True
    )

    for col in ["weight_g", "length_cm", "height_cm", "width_cm"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    df.drop_duplicates(subset=["product_id"], keep="first", inplace=True)
    idempotent_insert("products", clean_dataframe(df))


def process_orders(df):
    if df is None or df.empty:
        logging.info("[orders] No data to process.")
        return

    df = df.copy()

    for col in [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df[col] = df[col].where(df[col].notna(), None)

    df.rename(
        columns={
            "order_purchase_timestamp": "purchase_timestamp",
            "order_approved_at": "approved_at",
            "order_delivered_carrier_date": "delivered_carrier_date",
            "order_delivered_customer_date": "delivered_customer_date",
            "order_estimated_delivery_date": "estimated_delivery_date"
        },
        inplace=True
    )

    df.drop_duplicates(subset=["order_id"], keep="first", inplace=True)
    idempotent_insert("orders", clean_dataframe(df))


def process_order_items(df):
    if df is None or df.empty:
        logging.info("[order_items] No data to process.")
        return

    df = df.copy()

    if "shipping_limit_date" in df.columns:
        df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")
        df["shipping_limit_date"] = df["shipping_limit_date"].where(df["shipping_limit_date"].notna(), None)

    df.drop_duplicates(subset=["order_id", "order_item_id"], keep="first", inplace=True)
    idempotent_insert("order_items", clean_dataframe(df))


def process_order_payments(df):
    if df is None or df.empty:
        logging.info("[order_payments] No data to process.")
        return

    df = df.copy()
    df.drop_duplicates(subset=["order_id", "payment_sequential"], keep="first", inplace=True)
    idempotent_insert("order_payments", clean_dataframe(df))


def process_order_reviews(df):
    if df is None or df.empty:
        logging.info("[order_reviews] No data to process.")
        return

    df = df.copy()

    for col in ["review_creation_date", "review_answer_timestamp"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df[col] = df[col].where(df[col].notna(), None)

    df.rename(
        columns={
            "review_comment_title": "comment_title",
            "review_comment_message": "comment_message",
            "review_creation_date": "creation_date",
            "review_answer_timestamp": "answer_timestamp"
        },
        inplace=True
    )

    df.drop_duplicates(subset=["review_id", "order_id"], keep="first", inplace=True)
    idempotent_insert("order_reviews", clean_dataframe(df))


def main():
    try:
        logging.info("Starting ingestion")

        df_customers = load_csv("olist_customers_dataset.csv")
        df_sellers = load_csv("olist_sellers_dataset.csv")
        df_products = load_csv("olist_products_dataset.csv")
        df_product_cat = load_csv("product_category_name_translation.csv")
        df_orders = load_csv("olist_orders_dataset.csv")
        df_order_items = load_csv("olist_order_items_dataset.csv")
        df_order_payments = load_csv("olist_order_payments_dataset.csv")
        df_order_reviews = load_csv("olist_order_reviews_dataset.csv")

        process_locations(df_customers, df_sellers)
        process_product_categories(df_product_cat, df_products)

        process_customers(df_customers)
        process_sellers(df_sellers)
        process_products(df_products)   

        process_orders(df_orders)  

        process_order_items(df_order_items)
        process_order_payments(df_order_payments)
        process_order_reviews(df_order_reviews)

    except Exception as e:
        logging.error(f"Error during ingestion: {e}")
    finally:
        engine.dispose()
        logging.info("Ingestion finished")


if __name__ == "__main__":
    main()