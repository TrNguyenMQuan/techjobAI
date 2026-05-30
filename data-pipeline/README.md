# data-pipeline — VietnamWorks ETL & API Search Backend

Hệ thống end-to-end thu thập, xử lý, lưu trữ, phân tích và tìm kiếm ngữ nghĩa dữ liệu tuyển dụng IT tại Việt Nam từ **VietnamWorks public API**.

Hệ thống sử dụng kiến trúc **Medallion** phối hợp giữa **PySpark** (cho extraction/loading thô) và **dbt** (cho modeling/data warehouse).

---

## 🏗️ Kiến trúc Hệ thống

### 1. Luồng dữ liệu (Data Pipeline Flow)

```
[VietnamWorks API]
      │ (API Request - Async HTTPX client)
      ▼
[Bronze Storage (MinIO S3)]  <-- Lưu file JSON gốc phân trang
      │
      │ (PySpark Silver - Đọc JSON, làm sạch, loại trùng)
      ▼
[Silver Storage (MinIO S3)]  <-- Lưu Parquet format
      │
      │ (PySpark Postgres Writer)
      ▼
[PostgreSQL - silver.jobs]   <-- Bảng trung chuyển trung gian
      │
      │ (dbt Run)
      ├───────────────────────┬────────────────────────┐
      ▼                       ▼                        ▼
[dim_company, dim_skill,  [fact_job]            [job_skill_bridge]
  dim_location]               │ (Salary Normalize,     (N-N bridge)
                              │  HTML Strip)
                              ▼
                        [fact_job (Postgres)]
                              │
                              │ (Airflow Task: ML Embedding Service)
                              ▼
                        [fact_job.embedding]  <-- pgvector (384-dim, HNSW index)
                              │
                              │ (dbt aggregates)
                              ▼
                        [Dashboard Cache & Aggregates]
```

### 2. Các lớp lưu trữ (Medallion Architecture)

| Layer | Công nghệ | Dữ liệu & Định dạng | Mục đích |
|---|---|---|---|
| **Bronze** | MinIO (S3) | JSON, partition `jobs/dt=YYYY-MM-DD/` | Lưu trữ dữ liệu gốc thô từ API để lưu vết và có thể chạy lại khi cần. |
| **Silver (MinIO)** | MinIO (S3) | Parquet, partition `jobs/dt=YYYY-MM-DD/` | Dữ liệu dạng bảng sạch sẽ, loại bỏ trùng lặp `jobId`. |
| **Silver (Postgres)** | PostgreSQL | Bảng `silver.jobs` | Bảng lưu trữ trung gian để dbt đọc dữ liệu thô sạch. |
| **Gold (Warehouse)** | PostgreSQL | Bảng `warehouse_warehouse.fact_job` và các `dim_*` | Dữ liệu đã chuẩn hóa, làm sạch nội dung text (bỏ HTML tags), phân tách đa chiều. |
| **Gold (Aggregates)** | PostgreSQL | Các bảng `agg_*` và `dashboard_cache` | Tổng hợp dữ liệu pre-computed cho API Dashboard. |

---

## 📁 Cấu trúc Thư mục

```
data-pipeline/
├── .env.example                # File mẫu cấu hình biến môi trường
├── requirements.txt            # Quản lý python dependencies (PySpark, FastAPI, etc.)
├── docker-compose.yml          # Containerize: Airflow, Redis, MinIO, Postgres (pgvector)
├── Dockerfile.airflow          # Custom Airflow Image (cài đặt Java, PySpark, dbt)
│
├── dags/                       # Airflow DAG định nghĩa lịch trình chạy hàng ngày
│   └── vietnamworks_etl_dag.py
│
├── pipeline/                   # Scripts thực thi các bước ETL
│   ├── bronze.py               # Thu thập dữ liệu API -> Bronze JSON (MinIO)
│   ├── silver.py               # Bronze JSON -> Silver Parquet (MinIO)
│   ├── silver_to_postgres.py   # Silver Parquet -> Postgres (silver.jobs)
│   └── embedding.py            # Tạo vector embedding bằng SentenceTransformer
│
├── source/                     # Module Python tái sử dụng cho các scripts
│   ├── vietnamworks_client.py  # HTTP client kết nối API
│   ├── spark_session.py        # Cấu hình Spark Session
│   ├── storage.py              # Kết nối S3 / ADLS Gen2
│   └── setup_db.py             # Setup DDL database (pgvector, silver.jobs)
│
├── dbt_vietnamworks/           # Project dbt (Transform & Data Quality Tests)
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/            # Ánh xạ 1-1 từ silver.jobs
│       └── warehouse/          # Fact & Dimensions (Fact Job, Dim Skill, Dim Company, Dim Location)
│       └── aggregates/         # Tổng hợp dữ liệu pre-computed phục vụ Dashboard
│
├── app/                        # FastAPI App Backend
│   └── main.py                 # API Endpoints (phân trang job, stats, semantic search)
│
└── tests/                      # Pytest Suite
    ├── conftest.py
    └── test_api_client.py
```

---

## 🚀 Hướng dẫn khởi chạy

### 1. Chuẩn bị môi trường
```bash
cd data-pipeline
cp .env.example .env
# Điền đầy đủ thông tin credentials
```

### 2. Khởi chạy Docker Compose (Airflow + MinIO + Postgres + Redis + FastAPI Backend)
```bash
docker compose up -d --build
```

### 3. Setup Database (Tạo extension pgvector và bảng silver.jobs)
```bash
docker exec -it techjob-backend python source/setup_db.py
```

### 4. Sử dụng API Endpoints
FastAPI Backend chạy tại: `http://localhost:8000/docs` (Swagger UI)

*   **Stats API**: `GET /api/stats`
*   **List Jobs**: `GET /api/jobs?keyword=python&page=1&size=20`
*   **Semantic Search (pgvector)**: `GET /api/search?q=machine+learning+python+developer`
*   **Monthly Hiring Trends**: `GET /api/trends`
*   **Top Skills**: `GET /api/top-skills`

---

## 📈 Tích hợp CI/CD

Quy trình tự động hóa kiểm thử được thiết lập tại `.github/workflows/ci.yml`. Nó sẽ:
1.  Checkout code & Setup Python 3.11
2.  Cài đặt dependencies từ `requirements.txt`
3.  Chạy pytest để kiểm tra logic kết nối API và mapping của Spark.
