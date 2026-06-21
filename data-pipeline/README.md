# TechJob AI — Data Pipeline (Part 1)

> Pipeline thu thập & xử lý dữ liệu tuyển dụng IT từ **VietnamWorks public API**, theo kiến trúc **Medallion** (Raw → Staging → Warehouse → Marts), phục vụ **Market Trend Dashboard**, **Salary Prediction** và (sau này) **AI Recommendation** của nền tảng TechJob AI.
>
> README này là tài liệu của **module data-pipeline**. Tài liệu sản phẩm tổng thể xem ở README gốc của repo.

---

## Mục lục

- [1. Kiến trúc tổng quan](#1-kiến-trúc-tổng-quan)
- [2. Tech stack](#2-tech-stack)
- [3. Dành cho người DÙNG data (ML / BI teammate)](#3--dành-cho-người-dùng-data-ml--bi-teammate)
- [4. Dành cho người CHẠY pipeline (developer)](#4-️-dành-cho-người-chạy-pipeline-developer)
- [5. Cấu trúc thư mục](#5-cấu-trúc-thư-mục)
- [6. Đội ngũ](#6-đội-ngũ)

---

## 1. Kiến trúc tổng quan

Dữ liệu chảy qua 4 tầng (Medallion). Mỗi tầng làm sạch dần, tầng sau **không bao giờ** đọc thẳng tầng thô:

```
VietnamWorks API
      │  vietnamworks_client.py (async HTTP, pagination, retry)
      ▼
BRONZE   data/raw/jobs/dt=YYYY-MM-DD/*.json        ← JSON thô, nguyên bản
      │  silver.py (PySpark: parse + dedupe + cast)
      ▼
ILVER   s3a://silver/jobs/dt=.../*.parquet         ← parquet sạch (MinIO local / ADLS cloud)
      │  silver_to_postgres.py (Spark JDBC)
      ▼
STAGING  silver.jobs (Postgres, 19 cột)             ← bảng quan hệ, 1 row/job
      │  dbt run  (SQL modeling + tests + lineage)
      ▼
WAREHOUSE  warehouse_warehouse.*                    ← fact + dimensions (dimensional model)
      │  dbt run
      ▼
MARTS    warehouse_marts.*                          ← bảng pre-aggregated / feature table cho app + ML
```

**Hai môi trường (dev / prod):**

| | dev | prod |
|---|---|---|
| Warehouse | Postgres **localhost** | **NeonDB** (Postgres cloud — data chung của team) |
| Mục đích | Code và test | Nơi teamate đọc data |
| Chọn bằng | Default | `dbt ... --target prod` / override `.env` Neon |

> Code **không hardcode** connection — mọi host/credential nằm ở `.env` vars (`.env`) + `profiles.yml`. Đổi môi trường = đổi config, không sửa code.

---

## 2. Tech stack

| Layer | Tool | Vai trò |
|---|---|---|
| Ingestion | **PySpark 3.5** | Đọc API → parse JSON → parquet |
| Object storage | **MinIO** (local) | Lưu Bronze/Silver, S3-compatible |
| Warehouse | **Postgres** (localhost dev) → **NeonDB** (cloud prod) | Bảng quan hệ + marts |
| Orchestration | **Airflow** (Celery + Redis) | schedule `@daily`, retry, dependency |
| Transform | **dbt-postgres** | SQL modeling, tests, lineage |
| Container | **Docker Compose** | MinIO + Airflow + Redis |

---

## 3. Dành cho người DÙNG data (ML / BI teammate)

**Bạn KHÔNG cần chạy pipeline.** Data đã được publish sẵn lên **NeonDB**. Bạn chỉ cần kết nối và `SELECT`.

### 3.1. Kết nối NeonDB (read-only)

| Tham số | Giá trị |
|---|---|
| Host | `ep-odd-feather-aok9wn0q.c-2.ap-southeast-1.aws.neon.tech` |
| Port | `5432` |
| Database | `neondb` |
| User | `machine_learning_readonly` |
| Password | _xin team lead qua kênh bảo mật (KHÔNG commit lên git)_ |
| SSL | **bắt buộc** `sslmode=require` |

Connection string:
```
postgresql://machine_learning_readonly:<password>@ep-odd-feather-aok9wn0q.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

Đọc bằng Python (pandas):
```python
import pandas as pd, sqlalchemy
engine = sqlalchemy.create_engine(
    "postgresql+psycopg://machine_learning_readonly:<password>@ep-odd-feather-aok9wn0q"
    ".c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
)
df = pd.read_sql("SELECT * FROM warehouse_marts.mart_salary_features", engine)
```

> User `machine_learning_readonly` **chỉ đọc** schema `warehouse_marts`. Không sửa/xoá được — an toàn cho cả hai bên.

### 3.2. Catalog — các bảng dùng được (schema `warehouse_marts`)

| Bảng | Grain (1 row = ?) | Dùng cho |
|---|---|---|
| **`mart_salary_features`** | 1 job hiện lương | **Salary Prediction model** (feature table) |
| `mart_salary_benchmark` | (skill × cấp bậc) | lương median tham chiếu |
| `mart_skill_demand` | (skill × tuần) | skill hot theo thời gian |
| `mart_location_demand` | thành phố | phân bố job theo địa lý |
| `fact_job_skills` | (job × skill) | bridge table cho Skill Gap Analysis |

> **Bảng tra cứu (dimensions)** ở schema `warehouse_warehouse` (`dim_job_level`, `dim_location`, `dim_company`, `dim_skill`) — dùng để JOIN giải mã các cột `*_id`. `machine_learning_readonly` cần được grant đọc schema này (xem [§3.3.1](#331-mapping-mã-categorical--nhãn)).

> **Embeddings (semantic search)** ở schema `warehouse_warehouse`: bảng `job_embeddings` — `vector(1024)` sinh bằng `BAAI/bge-m3`. Data contract đầy đủ ở [§3.5](#35-data-contract--job_embeddings-m10).

### 3.3. Data contract — `mart_salary_features` (M9)

Bảng feature chính cho model dự đoán lương. **Schema ổn định** — DE cam kết tên cột/kiểu không đổi giữa các lần refresh (version `v1`).

- **Filter:** chỉ job có `is_salary_visible = true` và `salary_min/max` NOT NULL.
- **Label:** `salary_midpoint = (salary_min + salary_max) / 2`.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `job_id` | int | khoá, 1 row/job |
| `job_level_id` | int | **categorical** — id KHÔNG tuần tự, decode ở §3.3.1 → cần one-hot |
| `type_working_id` | int | **categorical** (hình thức làm việc), decode ở §3.3.1 → cần one-hot |
| `city_id` | int | địa điểm chính (phần tử đầu của working_locations), decode qua `dim_location` |
| `skill_count` | int | số skill job yêu cầu |
| `salary_min` / `salary_max` | int | khoảng lương (VND) |
| `salary_midpoint` | int | **label** của model |
| `week_start` | date | tuần đăng tin (bucket thời gian) |
| `has_*` (20 cột) | bool | có/không từng skill trong Top 20 (`has_python`, `has_sql`, `has_java`, …) |

> `job_level_id`, `type_working_id`, `city_id` là **mã categorical, KHÔNG phải số có thứ tự** — nhớ one-hot encode, đừng đưa thẳng số vào model.

#### 3.3.1. Mapping mã categorical → nhãn

**`job_level_id`** (lookup nhỏ & cố định — ghi sẵn đây, khỏi cần JOIN). ⚠️ id **không tuần tự**:

| id | Nghĩa | seniority_order |
|---|---|---|
| 8 | Thực tập sinh / Sinh viên | 1 |
| 1 | Mới tốt nghiệp (Fresher) | 2 |
| 5 | Nhân viên | 3 |
| 7 | Trưởng phòng (Manager) | 4 |
| 3 | Giám đốc & cấp cao hơn | 5 |

> Cần biến **có thứ tự**? Dùng `seniority_order` (1→5, có trong `dim_job_level`). Coi là **phân loại**? One-hot `job_level_id`.

**`city_id`** → JOIN `warehouse_warehouse.dim_location` (nhiều giá trị, không tiện liệt kê):
```sql
SELECT f.*, l.city_name_vi
FROM warehouse_marts.mart_salary_features f
LEFT JOIN warehouse_warehouse.dim_location l USING (city_id);
```

**`type_working_id`** → hình thức làm việc. **Chưa có dim** (≈95% là `1` = toàn thời gian; `2/3/4/6` hiếm, nhãn đang xác minh). Tạm coi là categorical thô.

### 3.4. Ví dụ query

```sql
-- Lấy toàn bộ feature table để train
SELECT * FROM warehouse_marts.mart_salary_features;

-- Kiểm tra số lượng & độ phủ label
SELECT count(*) AS total,
       count(*) FILTER (WHERE salary_midpoint IS NOT NULL) AS with_label
FROM warehouse_marts.mart_salary_features;

-- Lương median theo skill (sample ≥ 3, đã lọc job hiện lương)
SELECT skill_name, level_name_vi, median_salary_min, median_salary_max, sample_size
FROM warehouse_marts.mart_salary_benchmark
ORDER BY median_salary_max DESC;

-- Top skill hot nhất (tổng theo tất cả các tuần)
SELECT skill_name, SUM(job_count) AS total
FROM warehouse_marts.mart_skill_demand
GROUP BY skill_name ORDER BY total DESC LIMIT 15;
```

### 3.5. Data contract — `job_embeddings` (M10)

Bảng vector cho **AI Job Recommendation** & **Automated Resume Screening** (semantic search).
Khác các bảng trên: nằm ở schema **`warehouse_warehouse`** (không phải `warehouse_marts`).

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `job_id` | int | khoá, 1 row/job; JOIN `fact_job_postings` để lấy chi tiết job |
| `embedding` | `vector(1024)` | vector đã **normalize** (unit length) |
| `model_name` | text | model sinh vector — hiện: `BAAI/bge-m3` |
| `embedded_at` | timestamp | thời điểm tính vector |

**Luật bắt buộc:**
- **Cùng 1 model**: query của bạn PHẢI embed bằng đúng `BAAI/bge-m3` + `normalize_embeddings=True`. Khác model → khoảng cách vô nghĩa.
- **Khoảng cách**: cosine `<=>` (nhỏ = giống nhau). `similarity = 1 - (a <=> b)`.
- **Coverage**: embeddings refresh **thủ công** (Colab) → không đảm bảo mọi job đều có vector mọi lúc. Job chưa embed = không có row. Kiểm độ phủ bằng `LEFT JOIN fact_job_postings`.

**Tìm 5 job giống nhất với một job (thay `:id` bằng job_id):**
```sql
WITH anchor AS (
    SELECT embedding FROM warehouse_warehouse.job_embeddings WHERE job_id = :id
)
SELECT f.job_id, f.job_title, 1 - (e.embedding <=> a.embedding) AS similarity
FROM warehouse_warehouse.job_embeddings e
JOIN warehouse_warehouse.fact_job_postings f USING (job_id)
CROSS JOIN anchor a
WHERE e.job_id <> :id
ORDER BY e.embedding <=> a.embedding
LIMIT 5;
```

**Search bằng câu chữ tự do (Python — tự embed query bằng bge-m3):**
```python
qvec = model.encode(["Python backend, Docker, Kubernetes"], normalize_embeddings=True)[0]
# rồi: ORDER BY embedding <=> '<qvec>'::vector LIMIT 5
```

> Refresh embeddings: notebook `notebooks/embeding_jobs.ipynb` chạy trên **Colab GPU**
> (đọc Neon → bge-m3 → UPSERT). Tự động hoá qua Airflow: **deferred**.

---

## 4. Dành cho người CHẠY pipeline (developer)

### 4.1. Chuẩn bị

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # rồi điền giá trị thật (MinIO, Postgres, NEON_*)
docker compose up -d          # MinIO (9001) + Airflow (8080) + Redis
```

### 4.2. Chạy ETL ở môi trường DEV (Postgres localhost)

```bash
# Từng tầng (thủ công)
python -c "from pipeline.bronze import run; run('2026-05-24')"   # API → Bronze JSON
python -c "from pipeline.silver import run; run('2026-05-24')"   # Bronze → Silver parquet
python -m pipeline.silver_to_postgres                            # Silver → silver.jobs

# Warehouse + Marts (dbt) — target mặc định = dev (localhost)
cd dbt_vietnamworks
dbt build --profiles-dir .         # seed → run → test toàn bộ
```

Hoặc để **Airflow** chạy tự động: mở http://localhost:8080 → trigger DAG `vietnamworks_etl`
(5 task: `ingest_to_bronze → extract_to_silver → silver_to_postgres → dbt_build`).

### 4.3. PUBLISH data lên NeonDB (prod) cho team

> Vì Postgres không query chéo DB, **cả chuỗi silver → warehouse → marts phải build trên Neon**.
> NeonDB **bắt buộc SSL** → set `POSTGRES_SSLMODE=require`. Các biến `NEON_*` lấy từ `.env`.

```bash
# Gom env Neon cho 2 script Python (chỉ áp cho lệnh đó, không dính shell)
NEON="POSTGRES_HOST=$NEON_HOST POSTGRES_PORT=$NEON_PORT POSTGRES_DB=$NEON_DB \
      POSTGRES_USER=$NEON_USER POSTGRES_PASSWORD=$NEON_PASSWORD POSTGRES_SSLMODE=require"

# 1) Tạo schema/bảng silver trên Neon
env $NEON python -m source.setup_db

# 2) Đổ silver.jobs lên Neon (đọc parquet từ MinIO local → ghi Neon)
env $NEON python -c "from pipeline.silver_to_postgres import run; run('2026-05-24')"

# 3) Build warehouse + marts trên Neon (dbt có target sẵn → KHÔNG cần override env)
cd dbt_vietnamworks
dbt build --target prod --profiles-dir .
```

Verify:
```bash
dbt debug --target prod --profiles-dir .   # Connection test: OK
# Trong DataGrip (connection Neon): SELECT count(*) FROM warehouse_marts.mart_salary_features;
```

> **Giới hạn hiện tại:** publish lên Neon đang chạy **thủ công**. Tự động hoá DAG ghi thẳng prod là task tiếp theo (deferred).

---

## 5. Cấu trúc thư mục

```
data-pipeline/
├── source/                      # module tái sử dụng (không chứa business logic)
│   ├── vietnamworks_client.py   #   HTTP client (pagination, retry)
│   ├── spark_session.py         #   SparkSession factory (S3A + JDBC)
│   ├── storage.py               #   path abstraction MinIO (local) / ADLS (cloud)
│   └── setup_db.py              #   DDL idempotent: schema silver + silver.jobs
├── pipeline/                    # các bước chạy được (1 file = 1 tầng)
│   ├── bronze.py · silver.py · silver_to_postgres.py
│   └── export_salary_features.py  # (optional) export snapshot CSV cho train offline
├── dags/                        # vietnamworks_etl_dag.py
├── dbt_vietnamworks/            # dbt project
│   ├── models/  staging/ · warehouse/ · marts/
│   ├── seeds/   dim_job_level.csv
│   ├── tests/   singular tests
│   ├── dbt_project.yml          # cấu hình + vars (top_skills cho feature table)
│   └── profiles.yml             # target dev (localhost) + prod (Neon)
├── docker-compose.yml           # MinIO + Redis + Airflow
├── Dockerfile.airflow
└── .env(.example)               # secrets (gitignored)
```

> Schema trong Postgres (dbt naming `{target}_{custom}`): `warehouse_staging` (stg_jobs) ·
> `warehouse_warehouse` (fact + dims) · `warehouse_marts` (marts).

---

## 6. Đội ngũ

### Nhóm 6 — CQ 2023/22
* Võ Trần Duy Hoàng — 23120266
* Võ Gia Huy — 23120277
* Nguyễn Hữu Khánh Hưng — 23120271
* Vũ Trần Phúc — 23120333
* Trần Nguyễn Minh Quân — 23120342

### Giảng viên hướng dẫn
* TS. Trần Duy Hoàng (Lý thuyết)
* ThS. Ngô Ngọc Đăng Khoa · ThS. Hồ Tuấn Thanh (Thực hành)
