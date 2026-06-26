# TechJob AI

TechJob AI là một nền tảng tìm kiếm việc làm IT thông minh, kết hợp các công nghệ dữ liệu hiện đại và Trí tuệ Nhân tạo (AI) để mang lại trải nghiệm tối ưu cho ứng viên. Hệ thống được thiết kế hoàn chỉnh từ Data Pipeline (thu thập, xử lý dữ liệu), Data Warehouse, cho đến Backend AI và Frontend giao diện người dùng.

## Tính Năng Nổi Bật

- **Hybrid Search (Tìm kiếm lai):** Kết hợp tìm kiếm chính xác theo Keyword (SQL `ILIKE`) và tìm kiếm theo ngữ nghĩa (Semantic Search sử dụng `pgvector` và mô hình `Sentence-Transformers`).
- **AI Salary Predictor:** Dự đoán mức lương cho các công việc không hiển thị mức lương (Negotiable) dựa trên Machine Learning.
- **Smart Dashboard & Market Insights:** Thống kê thị trường việc làm, biểu đồ mức lương trung bình, và nhu cầu kỹ năng theo thời gian thực.
- **AI Cover Letter Generator:** Tự động tạo thư ứng tuyển dựa trên thông tin Profile cá nhân và mô tả công việc (JD).
- **Data Warehouse Chuẩn ELT:** Luồng dữ liệu tự động cào tin tuyển dụng, làm sạch và chuyển đổi thông qua **Apache Airflow** và **dbt**.

---

## Kiến Trúc Hệ Thống (Tech Stack)

- **Frontend:** React 18, Vite, Tailwind CSS, Recharts.
- **Backend API:** FastAPI, Uvicorn, Python 3.10+.
- **Database:** PostgreSQL (chạy Local qua Docker) tích hợp extension `pgvector`.
- **Data Engineering:** Apache Airflow, dbt (Data Build Tool), MinIO, PySpark.
- **AI / Machine Learning:** `sentence-transformers` (Tạo Vector Embeddings), Scikit-learn (Mô hình dự đoán lương), Groq API (LLM tạo Cover Letter).

---

## Hướng Dẫn Cài Đặt & Chạy Dự Án (Local)

### Yêu cầu hệ thống
- **Node.js** (v18 trở lên)
### Bước 1: Khởi động Cơ sở dữ liệu bằng Docker
Để hệ thống có chỗ lưu trữ (PostgreSQL + vector data), bạn cần chạy Docker trước:
```bash
cd data-pipeline
docker compose up -d postgres-project
```

### Bước 2: Chạy Backend API (FastAPI)
Mở một terminal mới để chạy server Backend:
```bash
cd data-pipeline
# Kích hoạt môi trường ảo (nếu có)
.\.venv\Scripts\Activate

# Khởi chạy API
uvicorn be.main:app --reload --host 0.0.0.0 --port 8000
```
- **Backend API** sẽ có sẵn tại: `http://localhost:8000`
- **Tài liệu API (Swagger)** tại: `http://localhost:8000/docs`

### Bước 3: Chạy Frontend (React)
Mở một terminal khác tại thư mục gốc của dự án (`techjobAI`):
```bash
npm install
npm run dev
```
Truy cập vào trang web tại: **http://localhost:5173**

---

---

## Cấu Trúc Thư Mục Chính
```text
techjobAI/
├── src/                # Toàn bộ mã nguồn Frontend (React, Components, Pages)
├── data-pipeline/      # Nơi chứa mã nguồn Backend và Data Engineering
│   ├── be/             # FastAPI Backend (APIs, Database Connection)
│   ├── ai/             # Các scripts xử lý AI (Embeddings, Predictor)
│   ├── dbt_vietnamworks/ # Data transformations (ELT)
│   ├── docker-compose.yml # File cấu hình Docker
│   └── ...
└── docs/               # Chứa các tài liệu thiết kế hệ thống, API Docs
```

## Chú thích thêm
- Dự án mặc định được cấu hình để trỏ vào Database PostgreSQL Local. Nếu bạn muốn kết nối với Database trên Cloud (NeonDB), hãy cấu hình các biến `NEON_` trong file `.env`.
- Để biết chi tiết các đường dẫn API Backend đang hoạt động, vui lòng xem file [docs/api_read.md](docs/api_read.md).
