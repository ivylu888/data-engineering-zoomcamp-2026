import os
import sys
import pandas as pd
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from google.api_core.exceptions import NotFound, Forbidden
import time


# --- Configuration ---
BUCKET_NAME = "de-zoomcamp--2026" 
CREDENTIALS_FILE = "de-zoomcamp-487123-1fd52da55e16.json"

# Tasks to complete: 2019-2020 for both Yellow and Green taxis
YEARS = ["2019"]
COLORS = ["fhv"]
MONTHS = [f"{i:02d}" for i in range(1, 13)]
DOWNLOAD_DIR = "."

client = storage.Client.from_service_account_json(CREDENTIALS_FILE)
bucket = client.bucket(BUCKET_NAME)

def download_file(color, year, month):
    file_name = f"{color}_tripdata_{year}-{month}.csv.gz"
    url = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/fhv/{file_name}"
    
    parquet_file = file_name.replace(".csv.gz", ".parquet")
    file_path = os.path.join(DOWNLOAD_DIR, file_name)
    parquet_path = os.path.join(DOWNLOAD_DIR, parquet_file)

    try:
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, file_path)
        
        # --- Data Cleaning with Pandas ---
        # Load the raw CSV file into a DataFrame
        df = pd.read_csv(file_path)
        
        # # Standardize data types:
        # Convert base number to string and location IDs to nullable integers (Int64)
        # This prevents schema issues in BigQuery caused by mixed types or NaN values
        if 'PUlocationID' in df.columns:
            df['PUlocationID'] = df['PUlocationID'].astype('Int64')
        if 'DOlocationID' in df.columns:
            df['DOlocationID'] = df['DOlocationID'].astype('Int64')
        
        # Export the cleaned data to Parquet format for better performance and smaller storage size
        df.to_parquet(parquet_path, engine='pyarrow')
        print(f"Cleaned and converted to: {parquet_path}")
        
       # Cleanup: Remove the raw CSV to save local disk space
        os.remove(file_path)
        return parquet_path
    except Exception as e:
        print(f"Failed to process {url}: {e}")
        return None

def verify_gcs_upload(blob_name):
    return storage.Blob(bucket=bucket, name=blob_name).exists(client)

def upload_to_gcs(file_path, max_retries=3):
    if not file_path: return
    
    blob_name = os.path.basename(file_path)
    blob = bucket.blob(blob_name)
    
    for attempt in range(max_retries):
        try:
            print(f"Uploading {file_path} to GCS (Attempt {attempt + 1})...")
            blob.upload_from_filename(file_path, timeout=600)
            
            if verify_gcs_upload(blob_name):
                print(f"Successfully uploaded and verified: gs://{BUCKET_NAME}/{blob_name}")
                # Clean up: Delete local file after successful upload to save space
                os.remove(file_path)
                return
        except Exception as e:
            print(f"Upload failed for {file_path}: {e}")
        
        time.sleep(5)
    print(f"Giving up on {file_path} after {max_retries} attempts.")

if __name__ == "__main__":
    for year in YEARS:
        for color in COLORS:
            print(f"\n--- Starting Migration for {color.upper()} {year} ---")
            
            # Step 1: Download all 12 months for this category in parallel
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Use lambda to pass multiple arguments to download_file
                file_paths = list(executor.map(lambda m: download_file(color, year, m), MONTHS))

            # Step 2: Upload those files to GCS and delete locally
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.map(upload_to_gcs, filter(None, file_paths))

    print("\n All 2019-2020 data is in the GCS bucket.")