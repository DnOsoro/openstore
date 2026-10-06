import os
import glob
import boto3
from botocore.client import Config
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

S3_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://localhost:8333")
AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "openstore_key")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "openstore_secret")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "olist-raw")
SOURCE_DIR = "data/source"

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )

def upload_files():
    s3 = get_s3_client()
    
    # Ensure bucket exists
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"Bucket '{BUCKET_NAME}' created or already exists.")
    except Exception as e:
        print(f"Note on bucket creation: {e}")

    # Find all CSV files in source folder
    csv_files = glob.glob(os.path.join(SOURCE_DIR, "*.csv"))
    if not csv_files:
        print(f"No CSV files found in {SOURCE_DIR}")
        return

    print(f"Found {len(csv_files)} CSV files. Starting upload to SeaweedFS...")

    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        print(f"Uploading {file_name} -> s3://{BUCKET_NAME}/{file_name}...")
        s3.upload_file(file_path, BUCKET_NAME, file_name)
        print(f"Successfully uploaded {file_name}")

if __name__ == "__main__":
    upload_files()
