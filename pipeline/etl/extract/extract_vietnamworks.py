"""
Extract IT jobs from VietnamWorks API.
Endpoint: POST https://ms.vietnamworks.com/job-search/v1.0/search

Usage:
    python pipeline/etl/extract/extract_vietnamworks.py
"""

import json
import time
import os
from datetime import date, datetime
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
import requests
import pandas as pd

# ============================================================
# CONFIG
# ============================================================
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

# Từ khóa IT để crawl
KEYWORDS = [
    "data engineer",
    "backend developer",
    "frontend developer",
    "fullstack developer",
    "devops engineer",
    "data analyst",
    "data scientist",
    "machine learning engineer",
    "python developer",
    "java developer",
    "react developer",
    "nodejs developer",
    "software engineer",
    "QA engineer",
    "mobile developer",
    "cloud engineer",
    "AI engineer",
    "business analyst",
    "product manager",
    "UI UX designer",
]

# Output
today_str = date.today().isoformat()
OUTPUT_DIR = PROJECT_ROOT / f"data/raw/vietnamworks/{today_str}"



# ============================================================
# API CALL
# ============================================================
def search_jobs(query: str, page: int = 0, hits_per_page: int = 50) -> dict:
    """Call VietnamWorks search API."""
    payload = {
        "userId": 0,
        "query": query,
        "filter": [],
        "ranges": [],
        "order": [],
        "hitsPerPage": hits_per_page,
        "page": page,
        "retrieveFields": RETRIEVE_FIELDS,
        "summaryVersion": "",
    }

    try:
        resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  [ERROR] query='{query}' page={page} → {e}")
        return {}


# ============================================================
# PARSE RESPONSE
# ============================================================
def parse_job(raw: dict) -> dict:
    """Parse one job from API response into a flat dict."""
    # Skills → list of names
    raw_skills = raw.get("skills") or []
    skills = [s.get("skillName", "") for s in raw_skills if isinstance(s, dict) and s.get("skillName")]
    # Working locations → combined city names
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
    # Benefits → list of values
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
    print(f"  VietnamWorks API Extractor — {today_str}")
    print(f"{'=' * 60}")

    all_jobs = []
    seen_ids = set()

    for keyword in KEYWORDS:
        print(f"\n[KEYWORD] '{keyword}'")

        # Page 0
        result = search_jobs(keyword, page=0)
        meta = result.get("meta", {})
        nb_hits = meta.get("nbHits", 0)
        nb_pages = meta.get("nbPages", 0)

        print(f"  → {nb_hits} hits, {nb_pages} pages")

        data = result.get("data", [])
        new_count = 0
        for raw_job in data:
            job = parse_job(raw_job)
            if job["source_id"] not in seen_ids:
                seen_ids.add(job["source_id"])
                all_jobs.append(job)
                new_count += 1

        print(f"  → Page 0: +{new_count} new jobs (total: {len(all_jobs)})")

        # Fetch remaining pages (max 3 thêm = tổng 4 pages)
        for page in range(1, min(nb_pages, 10)):
            time.sleep(1)  # Rate limit
            result = search_jobs(keyword, page=page)
            data = result.get("data", [])
            new_count = 0
            for raw_job in data:
                job = parse_job(raw_job)
                if job["source_id"] not in seen_ids:
                    seen_ids.add(job["source_id"])
                    all_jobs.append(job)
                    new_count += 1
            print(f"  → Page {page}: +{new_count} new jobs (total: {len(all_jobs)})")

        # Rate limit giữa các keyword
        time.sleep(1.5)

    if not all_jobs:
        print("\n[WARNING] Không lấy được job nào!")
        return

    # Save to Parquet
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "jobs.parquet"

    df = pd.DataFrame(all_jobs)
    df.to_parquet(output_path, engine="pyarrow", index=False)

    # Also save raw JSON for backup
    json_path = OUTPUT_DIR / "jobs.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  DONE!")
    print(f"  Total unique jobs : {len(df)}")
    print(f"  Parquet file      : {output_path}")
    print(f"  JSON backup       : {json_path}")
    print(f"  Columns           : {list(df.columns)}")
    print(f"{'=' * 60}")

    # Preview
    print(f"\n--- Sample (first 5 rows) ---")
    print(df[["source_id", "title", "company_name", "salary_display", "location_cities"]].head().to_string())


if __name__ == "__main__":
    main()
