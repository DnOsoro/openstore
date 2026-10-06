import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("POSTGRES_USER", "openstore_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "openstore_pass")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "openstore_db")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

def run_staging_transformations():
    print("Starting Staging Transformations (raw -> staging)...")
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging;"))
        
        # 1. Staging Orders
        print("Transforming staging.stg_orders...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS staging.stg_orders AS
            SELECT 
                order_id,
                customer_id,
                order_status,
                order_purchase_timestamp::TIMESTAMP AS order_purchase_at,
                order_approved_at::TIMESTAMP AS order_approved_at,
                order_delivered_carrier_date::TIMESTAMP AS order_shipped_at,
                order_delivered_customer_date::TIMESTAMP AS order_delivered_at,
                order_estimated_delivery_date::TIMESTAMP AS order_estimated_delivery_at
            FROM raw.olist_orders_dataset;
        """))

        # 2. Staging Customers
        print("Transforming staging.stg_customers...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS staging.stg_customers AS
            SELECT 
                customer_id,
                customer_unique_id,
                customer_zip_code_prefix::INT AS zip_code_prefix,
                customer_city,
                customer_state
            FROM raw.olist_customers_dataset;
        """))

        # 3. Staging Order Items
        print("Transforming staging.stg_order_items...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS staging.stg_order_items AS
            SELECT 
                order_id,
                order_item_id::INT AS item_number,
                product_id,
                seller_id,
                shipping_limit_date::TIMESTAMP AS shipping_limit_at,
                price::NUMERIC(10, 2) AS price,
                freight_value::NUMERIC(10, 2) AS freight_value
            FROM raw.olist_order_items_dataset;
        """))

    print("\n✓ Staging transformations completed successfully!")

if __name__ == "__main__":
    run_staging_transformations()
