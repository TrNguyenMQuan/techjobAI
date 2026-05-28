import asyncio
from pathlib import Path
from source.vietnamworks_client import VietnamWorksClient

async def main():
    client = VietnamWorksClient(semaphore_limit=5)  # conservative khi test
    await client.fetch_and_save(
        query="data engineer",
        raw_dir=Path("data/raw/jobs"),
        max_pages=3,  # chỉ lấy 3 trang để test nhanh
    )

asyncio.run(main())

from pathlib import Path
from pipeline.silver import run
from datetime import date
run(
    date_str=date.today().isoformat(),   # tự lấy ngày hôm nay
    raw_dir=Path("data/raw/jobs"),
    staging_dir=Path("data/staging/jobs"),
)
