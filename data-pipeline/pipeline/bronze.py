import asyncio
from source.vietnamworks_client import VietnamWorksClient

def run(date_str: str):
    client = VietnamWorksClient(semaphore_limit=5)

    # Filter IT/Viễn thông (parentId=5) → ~880 jobs, ~18 pages, không overlap, không cần dedup.
    pages = asyncio.run(client.fetch_and_save(date_str=date_str))

    print(f"Bronze ingestion done: {pages} pages written for dt={date_str}")
