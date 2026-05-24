# data-pipeline — VietnamWorks ETL

End-to-end pipeline thu thập + chuẩn hoá dữ liệu tuyển dụng IT Việt Nam từ **VietnamWorks public API**, theo kiến trúc **Medallion** (Raw → Staging → Warehouse).

> Phần Data Engineering của dự án [techjobAI](../README.md). Application (FastAPI + LLM + MCP) ở folder khác sau khi pipeline xong.

---

## Quick start (chỉ áp dụng sau khi xong các milestones)

```bash
cd data-pipeline
cp .env.example .env       # điền credentials
docker compose up -d       # khởi động Postgres + MinIO + Airflow + Redis
open http://localhost:8080 # Airflow UI (admin/admin)
open http://localhost:9001 # MinIO console
source venv/bin/activate
```

---

## Cấu trúc thư mục (target — sẽ hình thành dần qua các milestones)

```
data-pipeline/
├── .env.example                # template biến môi trường
├── .gitignore                  # loại trừ .env, __pycache__, data/, logs/
├── requirements.txt            # python deps (pyspark, requests, dotenv, ...)
├── docker-compose.yml          # Postgres + MinIO + Airflow + Redis
├── Dockerfile.airflow          # custom Airflow image (cài pyspark + dbt)
│
├── dags/                       # Airflow DAGs
│   └── vietnamworks_etl_dag.py
│
├── pipeline/                   # PySpark jobs (1 file = 1 transformation)
│   ├── extract_to_raw.py       # API → MinIO (Bronze, Parquet, partition dt=)
│   └── raw_to_staging.py       # MinIO Raw → Postgres staging (Silver)
│
├── source/                     # shared utilities (DRY)
│   ├── api_client.py           # VietnamWorks API client (pagination + retry)
│   ├── spark_session.py        # factory build SparkSession
│   ├── storage.py              # abstraction MinIO ↔ ADLS Gen2
│   ├── setup_db.py             # DDL idempotent
│   └── logger.py               # structured logging (structlog)
│
├── dbt_vietnamworks/           # dbt project (Silver → Gold)
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/            # 1-1 mirror với staging.jobs
│       │   ├── stg_jobs.sql
│       │   ├── _sources.yml
│       │   └── _schema.yml
│       └── warehouse/          # fact + dim tables (star schema)
│           ├── dim_company.sql
│           ├── dim_skill.sql
│           └── fact_job_postings.sql
│
├── tests/                      # pytest unit + integration tests
│   ├── conftest.py
│   ├── test_api_client.py
│   └── test_transforms.py
│
├── docs/
│   ├── ROADMAP.md              # checklist 8 milestones (track tiến độ)
│   ├── STACK.md                # tech stack rationale
│   └── GLOSSARY.md             # từ điển DE concepts (VN)
│
└── .github/workflows/
    └── ci.yml                  # lint + test + dbt parse
```

---

## Kiến trúc Medallion

| Layer | Storage | Format | Mục đích |
|---|---|---|---|
| **Raw (Bronze)** | MinIO → ADLS | Parquet, partition `dt=YYYY-MM-DD/` | Lưu y nguyên, replay được khi logic sai |
| **Staging (Silver)** | Postgres schema `staging` | Tables | Đã dedupe + cast types, chưa modeling |
| **Warehouse (Gold)** | Postgres schema `warehouse` | Fact + Dim tables (star schema) | Sẵn sàng cho BI / LLM RAG |

**Phân công lao động**:
- **PySpark** làm `Raw → Staging` (cần Python flexibility cho parse phức tạp)
- **dbt** làm `Staging → Warehouse` (cần SQL modeling + tests + lineage)

---

## Tiến độ

Tick checkbox khi xong từng milestone tại [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Tài liệu tham khảo nội bộ

- [docs/ROADMAP.md](docs/ROADMAP.md) — 8 milestones checklist
- [docs/STACK.md](docs/STACK.md) — tech stack tradeoffs
- [docs/GLOSSARY.md](docs/GLOSSARY.md) — từ điển DE (Medallion, Idempotency, CDC, ...)
- Plan đầy đủ (Why + Hands-on chi tiết): `~/.claude/plans/vai-tr-c-a-soft-salamander.md`
- Repo tham khảo: https://github.com/TrNhDuong/VietnamWorks_DE_Pipeline
