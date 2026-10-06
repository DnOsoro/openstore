import os
import io
import boto3
import pandas as pd
from sqlalchemy import create_engine, text
from botocore.client import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

S3_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://localhost:8333")
AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "openstore_key")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "openstore_secret")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "olist-raw")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

engine = create_engine(DATABASE_URL)

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )

def load_raw_data():
    s3 = get_s3_client()
    
    # Ensure 'raw' schema exists in PostgreSQL
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.commit()
        print("Schema 'raw' verified/created in PostgreSQL.")

    # List objects in SeaweedFS bucket
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    if "Contents" not in response:
        print("No files found in SeaweedFS bucket.")
        return

    for obj in response["Contents"]:
        file_key = obj["Key"]
        if not file_key.endswith(".csv"):
            continue

        table_name = file_key.replace(".csv", "")
        print(f"\nFetching s3://{BUCKET_NAME}/{file_key}...")
        
        # Read file directly from SeaweedFS stream
        csv_obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
        df = pd.read_csv(io.BytesIO(csv_obj["Body"].read()))
        
        print(f"Loaded {len(df):,} rows into memory. Inserting into raw.{table_name}...")
        
        # Write to raw schema in PostgreSQL
        df.to_sql(
            name=table_name,
            con=engine,
            schema="raw",
            if_exists="replace",
            index=False,
            chunksize=10000
        )
        print(f"Successfully loaded raw.{table_name}")

if __name__ == "__main__":
    load_raw_data()
