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

def run_core_transformations():
    print("Starting Core Transformations (staging -> core)...")
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS core;"))
        
        # 1. Dimension: Customers
        print("Building core.dim_customers...")
        conn.execute(text("DROP TABLE IF EXISTS core.dim_customers CASCADE;"))
        conn.execute(text("""
            CREATE TABLE core.dim_customers AS
            SELECT 
                customer_id,
                customer_unique_id,
                zip_code_prefix,
                customer_city,
                customer_state
            FROM staging.stg_customers;
        """))

        # 2. Fact: Orders
        print("Building core.fct_orders...")
        conn.execute(text("DROP TABLE IF EXISTS core.fct_orders CASCADE;"))
        conn.execute(text("""
            CREATE TABLE core.fct_orders AS
            SELECT 
                o.order_id,
                o.customer_id,
                o.order_status,
                o.order_purchase_at,
                o.order_approved_at,
                o.order_shipped_at,
                o.order_delivered_at,
                o.order_estimated_delivery_at,
                COALESCE(i.item_count, 0) AS total_items,
                COALESCE(i.total_price, 0) AS total_order_value,
                COALESCE(i.total_freight, 0) AS total_freight_value,
                COALESCE(i.total_price, 0) + COALESCE(i.total_freight, 0) AS grand_total
            FROM staging.stg_orders o
            LEFT JOIN (
                SELECT 
                    order_id,
                    COUNT(item_number) AS item_count,
                    SUM(price) AS total_price,
                    SUM(freight_value) AS total_freight
                FROM staging.stg_order_items
                GROUP BY order_id
            ) i ON o.order_id = i.order_id;
        """))

    print("\n✓ Core dimensional models built successfully!")

if __name__ == "__main__":
    run_core_transformations()
