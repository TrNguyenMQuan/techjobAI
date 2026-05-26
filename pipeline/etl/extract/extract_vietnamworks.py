"""
Extract IT jobs from VietnamWorks API.
Strategy: Filter by jobFunction (IT industry) instead of keywords.
Endpoint: POST https://ms.vietnamworks.com/job-search/v1.0/search

Usage:
    python pipeline/etl/extract/extract_vietnamworks.py
"""

import json
import time
from datetime import date, datetime
from pathlib import Path

import requests
import pandas as pd

# ============================================================
# CONFIG
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

API_URL = "https://ms.vietnamworks.com/job-search/v1.0/search"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "vi",
    "Origin": "https://www.vietnamworks.com",
    "Referer": "https://www.vietnamworks.com/",
    "x-source": "search-result",
}

RETRIEVE_FIELDS = [
    "address", "benefits", "jobTitle", "salaryMax", "isSalaryVisible",
    "jobLevelVI", "isShowLogo", "salaryMin", "companyLogo", "userId",
    "jobLevel", "jobLevelId", "jobId", "jobUrl", "companyId",
    "approvedOn", "isAnonymous", "alias", "expiredOn", "industries",
    "industriesV3", "workingLocations", "services", "companyName",
    "salary", "onlineOn", "simpleServices", "visibilityDisplay",
    "isShowLogoInSearch", "priorityOrder", "skills",
    "profilePublishedSiteMask", "jobDescription", "jobRequirement",
    "prettySalary", "requiredCoverLetter", "languageSelectedVI",
    "languageSelected", "languageSelectedId", "typeWorkingId",
    "createdOn", "isAdrLiteJob",
]

# Filter: jobFunction parentId=5 (IT), childrenIds=[-1] (all sub-categories)
JOB_FUNCTION_FILTER = {
    "field": "jobFunction",
    "value": json.dumps([{"parentId": 5, "childrenIds": [-1]}])
}

# Pagination config
MAX_PAGES = 20  # Safety limit (881 jobs / 50 per page = 18 pages)
HITS_PER_PAGE = 50
DELAY_BETWEEN_REQUESTS = 1.5  # seconds

# Output
today_str = date.today().isoformat()
OUTPUT_DIR = PROJECT_ROOT / f"data/raw/vietnamworks/{today_str}"


# ============================================================
# API CALL
# ============================================================
def search_jobs(page: int = 0) -> dict:
    """Call VietnamWorks search API with IT industry filter."""
    payload = {
        "userId": 0,
        "query": "",
        "filter": [JOB_FUNCTION_FILTER],
        "ranges": [],
        "order": [],
        "hitsPerPage": HITS_PER_PAGE,
        "page": page,
        "retrieveFields": RETRIEVE_FIELDS,
        "summaryVersion": "",
    }

    try:
        resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  [ERROR] page={page} → {e}")
        return {}


# ============================================================
# PARSE RESPONSE
# ============================================================
def parse_job(raw: dict) -> dict:
    """Parse one job from API response into a flat dict."""
    # Skills
    raw_skills = raw.get("skills") or []
    skills = [s.get("skillName", "") for s in raw_skills if isinstance(s, dict) and s.get("skillName")]

    # Working locations
    locations = raw.get("workingLocations") or []
    city_names = list(set(
        loc.get("cityNameVI", loc.get("cityName", ""))
        for loc in locations
        if isinstance(loc, dict) and (loc.get("cityNameVI") or loc.get("cityName"))
    ))
    address = (
        locations[0].get("address", "")
        if locations and isinstance(locations[0], dict)
        else raw.get("address", "")
    )

    # Industries
    industries_v3 = raw.get("industriesV3") or []
    industry = (
        industries_v3[0].get("industryV3NameVI", "")
        if industries_v3 and isinstance(industries_v3[0], dict)
        else ""
    )

    # Benefits
    raw_benefits = raw.get("benefits") or []
    benefits = [b.get("benefitValue", "") for b in raw_benefits if isinstance(b, dict) and b.get("benefitValue")]

    return {
        "source_id": f"vnw_{raw.get('jobId', '')}",
        "job_id": raw.get("jobId"),
        "title": raw.get("jobTitle", ""),
        "company_name": raw.get("companyName", ""),
        "company_id": raw.get("companyId"),
        "company_logo": raw.get("companyLogo", ""),
        "location_cities": json.dumps(city_names, ensure_ascii=False),
        "address": address,
        "salary_min": raw.get("salaryMin", 0),
        "salary_max": raw.get("salaryMax", 0),
        "salary_currency": raw.get("salaryCurrency", ""),
        "salary_display": raw.get("prettySalary", ""),
        "is_salary_visible": raw.get("isSalaryVisible", False),
        "job_level": raw.get("jobLevel", ""),
        "job_level_vi": raw.get("jobLevelVI", ""),
        "job_description": raw.get("jobDescription", ""),
        "job_requirement": raw.get("jobRequirement", ""),
        "skills": json.dumps(skills, ensure_ascii=False),
        "benefits": json.dumps(benefits, ensure_ascii=False),
        "industry": industry,
        "type_working_id": raw.get("typeWorkingId"),
        "language": raw.get("languageSelected", ""),
        "source_url": raw.get("jobUrl", ""),
        "created_on": raw.get("createdOn", ""),
        "approved_on": raw.get("approvedOn", ""),
        "expired_on": raw.get("expiredOn", ""),
        "online_on": raw.get("onlineOn", ""),
        "extracted_at": datetime.utcnow().isoformat(),
    }


# ============================================================
# MAIN
# ============================================================
def main():
    print(f"{'=' * 60}")
    print(f"  VietnamWorks IT Jobs Extractor — {today_str}")
    print(f"  Strategy: Filter by jobFunction (IT industry)")
    print(f"{'=' * 60}")

    # First request to get total
    result = search_jobs(page=0)
    meta = result.get("meta", {})
    total_hits = meta.get("nbHits", 0)
    total_pages = meta.get("nbPages", 0)

    print(f"\n  Total IT jobs available: {total_hits}")
    print(f"  Total pages: {total_pages}")
    print(f"  Pages to fetch: {min(total_pages, MAX_PAGES)}")

    all_jobs = []
    seen_ids = set()

    # Parse page 0
    data = result.get("data", [])
    for raw_job in data:
        job = parse_job(raw_job)
        if job["source_id"] not in seen_ids:
            seen_ids.add(job["source_id"])
            all_jobs.append(job)

    print(f"  Page 0: +{len(all_jobs)} jobs (total: {len(all_jobs)})")

    # Fetch remaining pages
    pages_to_fetch = min(total_pages, MAX_PAGES)
    for page in range(1, pages_to_fetch):
        time.sleep(DELAY_BETWEEN_REQUESTS)
        result = search_jobs(page=page)
        data = result.get("data", [])

        new_count = 0
        for raw_job in data:
            job = parse_job(raw_job)
            if job["source_id"] not in seen_ids:
                seen_ids.add(job["source_id"])
                all_jobs.append(job)
                new_count += 1

        print(f"  Page {page}: +{new_count} jobs (total: {len(all_jobs)})")

        # Stop early if no new jobs
        if new_count == 0 and len(data) == 0:
            print(f"  [INFO] No more data, stopping early.")
            break

    if not all_jobs:
        print("\n[WARNING] Không lấy được job nào!")
        return

    # Save to Parquet
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_parquet = OUTPUT_DIR / "jobs.parquet"
    output_json = OUTPUT_DIR / "jobs.json"

    df = pd.DataFrame(all_jobs)
    df.to_parquet(output_parquet, engine="pyarrow", index=False)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  DONE!")
    print(f"  Total unique IT jobs : {len(df)}")
    print(f"  Parquet file         : {output_parquet}")
    print(f"  JSON backup          : {output_json}")
    print(f"  Columns              : {list(df.columns)}")
    print(f"{'=' * 60}")

    # Preview
    print(f"\n--- Sample (first 5 rows) ---")
    print(df[["source_id", "title", "company_name", "salary_display", "location_cities"]].head().to_string())


if __name__ == "__main__":
    main()
