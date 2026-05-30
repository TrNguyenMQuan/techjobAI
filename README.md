# TechJob AI — Unified Data Engineering Pipeline

Dự án TechJob AI là hệ thống thu thập, làm sạch, mô hình hóa dữ liệu tuyển dụng IT tại Việt Nam và cung cấp API tìm kiếm ngữ nghĩa (Semantic Search).

Dự án đã được hợp nhất thành một pipeline tự động hóa hoàn toàn, lưu trữ dưới thư mục [data-pipeline](file:///c:/VSC/Project/techjobAI/data-pipeline).

---

## 🏗️ Tổng quan Công nghệ & Kiến trúc

Chi tiết kiến trúc và thiết kế hệ thống được mô tả tại [data-pipeline/README.md](file:///c:/VSC/Project/techjobAI/data-pipeline/README.md).

```
┌──────────────────┐      ┌────────────────────────┐      ┌────────────────────┐
│  VietnamWorks    │ ───▶ │   Object Storage thô   │ ───▶ │   PySpark Silver   │
│  Public API      │      │     (MinIO Bronze S3)  │      │   (MinIO Parquet)  │
└──────────────────┘      └────────────────────────┘      └─────────┬──────────┘
                                                                    │
                                                                    ▼
┌──────────────────┐      ┌────────────────────────┐      ┌────────────────────┐
│ FastAPI Backend  │ ◀─── │  Bảng Gold/Aggregates  │ ◀─── │    dbt Transform   │
│ (Semantic Search)│      │  (PostgreSQL + Vector) │      │    (warehouse)     │
└──────────────────┘      └────────────────────────┘      └────────────────────┘
```

## ⚙️ Các thành phần cốt lõi

1.  **Thu thập dữ liệu (Bronze)**: Async client sử dụng thư viện `httpx` cào dữ liệu từ VietnamWorks API, lưu trữ JSON gốc vào MinIO S3.
2.  **Làm sạch dữ liệu (Silver)**: PySpark làm sạch, chuyển đổi Schema, loại trùng lặp và ghi dữ liệu dạng Parquet lên MinIO S3, sau đó nạp vào PostgreSQL table `silver.jobs`.
3.  **Mô hình hóa dữ liệu (Gold/Warehouse)**:
    *   **dbt (Data Build Tool)**: Chuyển đổi dữ liệu từ `silver.jobs` sang Star Schema (`fact_job`, `dim_company`, `dim_skill`, `dim_location`, `job_skill_bridge`).
    *   **Chuẩn hóa lương**: Tự động quy đổi mức lương USD/VND, theo năm/tháng về chuẩn duy nhất `VND/tháng`.
    *   **Pre-computed Aggregates**: Tính toán sẵn dữ liệu tổng hợp (`dashboard_cache`, `agg_top_skills`, `agg_salary_by_title`, `agg_trend_monthly`) để API phản hồi tức thì (<10ms).
4.  **Học máy & Tìm kiếm ngữ nghĩa (Semantic Search)**:
    *   **Sentence Transformers (`all-MiniLM-L6-v2`)**: Chuyển đổi thông tin tuyển dụng (Title + Description + Skills) thành vector 384 chiều.
    *   **pgvector (HNSW Index)**: Lưu trữ vector và tìm kiếm tương tự (cosine similarity) trực tiếp trong PostgreSQL với chỉ mục HNSW tốc độ cao (<50ms).
5.  **Điều phối (Orchestration)**: **Apache Airflow** điều khiển và giám sát toàn bộ luồng công việc hàng ngày (`Bronze -> Silver -> Postgres -> dbt -> Embedding`).
6.  **Cổng dịch vụ (FastAPI)**: Cung cấp API phục vụ Dashboard analytics và Semantic Search.

---

## 🚀 Hướng dẫn nhanh

Tru cập thư mục [data-pipeline/README.md](file:///c:/VSC/Project/techjobAI/data-pipeline/README.md) để xem chi tiết cách cấu hình biến môi trường và chạy dự án qua Docker Compose.