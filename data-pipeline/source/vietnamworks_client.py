import asyncio
import json
import httpx
import boto3
from datetime import date
from botocore.config import Config
from tenacity import retry, stop_after_attempt, wait_exponential
from source.storage import StorageConfig

# Filter "Ngành nghề = Công nghệ thông tin/Viễn thông" (parentId=5, childrenIds=[-1] = tất cả sub).
# Captured từ browser DevTools khi filter trên vietnamworks.com.
IT_CATEGORY_FILTER = [
    {
        "field": "jobFunction",
        "value": json.dumps([{"parentId": 5, "childrenIds": [-1]}]),
    }
]

# jobDescription + jobRequirement là 2 field quan trọng cho LLM/RAG — không có trong list cũ.
RETRIEVE_FIELDS = [
    "jobId", "jobTitle", "companyName", "companyId",
    "salaryMin", "salaryMax", "isSalaryVisible",
    "prettySalary", "salaryCurrency",
    "companyLogo", "jobUrl",
    "jobLevel", "jobLevelVI", "jobLevelId", "typeWorkingId",
    "createdOn", "expiredOn", "approvedOn",
    "skills", "workingLocations", "benefits",
    "jobDescription", "jobRequirement",       # plain-text / HTML — LLM RAG input
    "industries", "industriesV3",             # category metadata
]


class VietnamWorksClient:
    BASE_URL = "https://ms.vietnamworks.com"

    def __init__(self, semaphore_limit: int = 10):
        self.sem = asyncio.Semaphore(semaphore_limit)
        self._s3 = boto3.client(
            "s3",
            endpoint_url=StorageConfig.minio_endpoint,
            aws_access_key_id=StorageConfig.minio_access_key,
            aws_secret_access_key=StorageConfig.minio_secret_key,
            config=Config(signature_version="s3v4"),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    async def fetch_page(self, client: httpx.AsyncClient, page: int):
        payload = {
            "userId": 0,
            "query": "",                    # empty = không lọc theo keyword
            "filter": IT_CATEGORY_FILTER,   # chỉ lấy job thuộc ngành IT/Viễn thông
            "ranges": [],
            "order": [],
            "hitsPerPage": 50,
            "page": page,
            "retrieveFields": RETRIEVE_FIELDS,
            "summaryVersion": "",
        }

        async with self.sem:
            response = await client.post(
                f"{self.BASE_URL}/job-search/v1.0/search",
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def fetch_and_save(self, date_str: str | None = None, max_pages: int | None = None):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(headers=headers) as client:
            first = await self.fetch_page(client, page=0)
            total_pages = first["meta"]["nbPages"]

            if max_pages is not None:
                total_pages = min(total_pages, max_pages)

            print(f"IT category | total={first['meta']['nbHits']} jobs | pages={total_pages}")

            tasks = [self.fetch_page(client, page=p) for p in range(1, total_pages)]
            rest = await asyncio.gather(*tasks)

        all_pages = [first] + list(rest)

        dt = date_str if date_str else date.today().isoformat()
        bucket = "bronze"

        for i, page_data in enumerate(all_pages):
            key = f"jobs/dt={dt}/page_{i+1:03d}.json"
            body = json.dumps(page_data, ensure_ascii=False, indent=2).encode("utf-8")
            self._s3.put_object(Bucket=bucket, Key=key, Body=body)
            print(f"  Uploaded s3a://{bucket}/{key}  ({len(page_data['data'])} jobs)")

        return len(all_pages)
