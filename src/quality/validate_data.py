import os
import pandas as pd
import pandera.pandas as pa
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("POSTGRES_USER", "openstore_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "openstore_pass")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "openstore_db")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

# Define schemas for critical tables
schemas = {
    "olist_orders_dataset": pa.DataFrameSchema({
        "order_id": pa.Column(str, nullable=False),
        "customer_id": pa.Column(str, nullable=False),
        "order_status": pa.Column(str, pa.Check.isin(["delivered", "shipped", "canceled", "unavailable", "invoiced", "processing", "created", "approved"])),
    }),
    "olist_order_items_dataset": pa.DataFrameSchema({
        "order_id": pa.Column(str, nullable=False),
        "order_item_id": pa.Column(int, pa.Check.greater_than_or_equal_to(1)),
        "price": pa.Column(float, pa.Check.greater_than(0)),
        "freight_value": pa.Column(float, pa.Check.greater_than_or_equal_to(0)),
    }),
    "olist_customers_dataset": pa.DataFrameSchema({
        "customer_id": pa.Column(str, nullable=False),
        "customer_unique_id": pa.Column(str, nullable=False),
        "customer_zip_code_prefix": pa.Column(int, nullable=False),
    })
}

def validate_raw_tables():
    print("Starting Data Quality checks with Pandera...\n")
    all_passed = True

    for table_name, schema in schemas.items():
        print(f"Validating 'raw.{table_name}'...")
        query = f"SELECT * FROM raw.{table_name};"
        df = pd.read_sql(query, engine)
        
        try:
            schema.validate(df, lazy=True)
            print(f"  ✓ 'raw.{table_name}' PASSED quality checks ({len(df):,} rows validated).")
        except pa.errors.SchemaErrors as err:
            all_passed = False
            print(f"  ✗ 'raw.{table_name}' FAILED quality checks:")
            print(err.failure_cases[["schema_context", "column", "check", "failure_case"]].head())

    if all_passed:
        print("\nAll raw data quality checks passed successfully!")
    else:
        print("\nSome tables failed validation checks. Please review log outputs.")

if __name__ == "__main__":
    validate_raw_tables()
