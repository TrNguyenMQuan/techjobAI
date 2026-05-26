"""
Upload raw Parquet/JSON to Azure Data Lake Gen2.
Medallion: raw/vietnamworks/<date>/jobs.parquet
"""

import os
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient

# Config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = PROJECT_ROOT / "infra" / ".env"
load_dotenv(ENV_PATH)

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "techjob-datalake")

today_str = date.today().isoformat()
RAW_DIR = PROJECT_ROOT / f"data/raw/vietnamworks/{today_str}"


def main():
    print(f"{'=' * 60}")
    print(f"  Azure Data Lake Upload — {today_str}")
    print(f"{'=' * 60}")

    if not CONNECTION_STRING:
        print("[ERROR] AZURE_STORAGE_CONNECTION_STRING not set in .env")
        return

    # Connect to Azure Data Lake
    service_client = DataLakeServiceClient.from_connection_string(CONNECTION_STRING)
    filesystem_client = service_client.get_file_system_client(CONTAINER_NAME)

    # Create filesystem (container) if not exists
    try:
        filesystem_client.get_file_system_properties()
        print(f"[INFO] Container '{CONTAINER_NAME}' exists")
    except Exception:
        filesystem_client.create_file_system()
        print(f"[INFO] Created container: {CONTAINER_NAME}")

    # Check local files
    if not RAW_DIR.exists():
        print(f"[ERROR] Directory not found: {RAW_DIR}")
        print(f"  → Run extract script first!")
        return

    # Upload files
    uploaded = 0
    for file_path in RAW_DIR.iterdir():
        if file_path.is_file() and file_path.suffix == ".parquet":
            # Medallion path: raw/vietnamworks/2026-05-17/jobs.parquet
            remote_path = f"raw/vietnamworks/{today_str}/{file_path.name}"

            directory_client = filesystem_client.get_directory_client(f"raw/vietnamworks/{today_str}")
            directory_client.create_directory()

            file_client = directory_client.get_file_client(file_path.name)

            with open(file_path, "rb") as f:
                file_data = f.read()
                file_client.upload_data(file_data, overwrite=True)

            size_kb = file_path.stat().st_size / 1024
            print(f"Uploaded: {remote_path} ({size_kb:.1f} KB)")
            uploaded += 1

    print(f"\n{'=' * 60}")
    print(f"  DONE! Uploaded {uploaded} files to Azure Data Lake")
    print(f"  Account   : techjobdatalake001")
    print(f"  Container : {CONTAINER_NAME}")
    print(f"  Path      : raw/vietnamworks/{today_str}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
