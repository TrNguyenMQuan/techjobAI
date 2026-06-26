# Hướng Dẫn Chạy & Sử Dụng Backend API (TechJob AI)

Backend API của TechJob AI được xây dựng bằng **FastAPI** và kết nối với **PostgreSQL Local** (với `pgvector`) để cung cấp dữ liệu thống kê, biểu đồ và tìm kiếm thông minh (Hybrid Search = Keyword + AI Semantic).

## 1. Hướng dẫn chạy Backend API cục bộ (Local)

### 1.1. Yêu cầu hệ thống
- Python 3.10+
- Chạy chung môi trường ảo (`.venv`) của dự án gốc.
- Đã cài đặt các dependencies trong `requirements.txt`.
- Yêu cầu cấu hình biến môi trường kết nối PostgreSQL cục bộ (`POSTGRES_HOST`, `POSTGRES_PORT`...) trong file `.env` (Bỏ qua `NEON_*` nếu muốn chạy Local).

### 1.2. Các bước chạy API

**Bước 1:** Mở terminal (PowerShell hoặc Bash) tại thư mục gốc của dự án `techjobAI`.

**Bước 2:** Kích hoạt môi trường ảo Python (Virtual Environment):
*Trên Windows:*
```powershell
.\.venv\Scripts\Activate.ps1
```
*Trên Mac/Linux:*
```bash
source .venv/bin/activate
```

**Bước 3:** Di chuyển vào thư mục chứa code data-pipeline:
```powershell
cd data-pipeline
```

**Bước 4:** Khởi chạy server Uvicorn (Hot-reload):
```powershell
uvicorn be.main:app --reload --host 0.0.0.0 --port 8000
```
Server sẽ khởi động và lắng nghe ở địa chỉ: **http://localhost:8000**

> [!TIP]
> **Tài liệu API tự động (Swagger UI)**: Bạn có thể mở trình duyệt và truy cập vào **http://localhost:8000/docs** để xem giao diện tương tác, test API trực tiếp mà không cần dùng Postman.

---

## 2. Chi Tiết Các API Endpoints

Dưới đây là danh sách các API đang hoạt động để cấp dữ liệu cho Frontend Dashboard và Job List. Tất cả đều trả về dữ liệu định dạng JSON.

### 2.1. API Tổng quan (Dashboard)

#### GET `/api/stats`
- **Mô tả:** Lấy thông số KPI chung (tổng tin tuyển dụng, số thành phố, kỹ năng, công ty).
- **Kết quả:** `{"total_jobs": 12045, "total_cities": 63, "total_skills": 1500, "total_companies": 433}`

#### GET `/api/jobs-by-level`
- **Mô tả:** Đếm số lượng công việc phân bố theo các cấp bậc (Thực tập sinh, Nhân viên, Trưởng phòng...). Dùng cho biểu đồ ngang.
- **Kết quả:** `{"data": [{"level_name_vi": "Nhân viên", "job_count": 5000}, ...]}`

#### GET `/api/locations`
- **Mô tả:** Thống kê số lượng việc làm theo từng thành phố/tỉnh thành. Dùng cho biểu đồ Donut Chart.
- **Kết quả:** `{"data": [{"city_name_vi": "Hồ Chí Minh", "job_count": 6000}, ...]}`

#### GET `/api/trends`
- **Mô tả:** Xu hướng tuyển dụng tổng thể theo từng tháng.
- **Kết quả:** `{"data": [{"month": "2026-06-01", "job_count": 1200}, ...]}`

### 2.2. API Kỹ Năng & Lương (Insights)

#### GET `/api/top-skills`
- **Mô tả:** Lấy danh sách Top kỹ năng IT được yêu cầu nhiều nhất trên thị trường.
- **Tham số (Query):** `limit` (int, mặc định 20) - Giới hạn số lượng trả về.
- **Kết quả:** `{"data": [{"skill_name": "SQL", "total_jobs": 800}, ...]}`

#### GET `/api/skill-trends`
- **Mô tả:** Lấy biến động nhu cầu tuyển dụng qua các tháng của **Top 5 kỹ năng hot nhất**. Dùng cho biểu đồ Line Chart đa tuyến.
- **Kết quả:** `{"data": [{"skill_name": "Python", "month": "2026-06-01", "job_count": 400}, ...]}`

#### GET `/api/salary-by-title`
- **Mô tả:** Lấy mức lương trung bình (tối thiểu và tối đa) nhóm theo kỹ năng và cấp bậc. Dùng cho Box Plot hoặc Market Insights.
- **Kết quả:** `{"data": [{"skill_name": "Java", "level_name_vi": "Senior", "median_salary_min": 1500, "median_salary_max": 2500, "sample_size": 150}, ...]}`

### 2.3. API Tìm Kiếm Việc Làm (Jobs)

#### GET `/api/jobs`
- **Mô tả:** Danh sách các công việc IT, hỗ trợ phân trang và tìm kiếm theo từ khóa thông thường.
- **Tham số (Query):** 
  - `page` (int, mặc định 1)
  - `size` (int, mặc định 20, hỗ trợ lên tới 2000)
  - `keyword` (str, tùy chọn) - Tìm chính xác (ILIKE) trong tiêu đề công việc hoặc tên công ty.
  - `ai_estimate` (str, "true"|"false") - Tính năng dự đoán lương AI (truyền "false" để tăng tốc độ load danh sách).
- **Kết quả:** `{"total": 840, "page": 1, "size": 20, "data": [...]}`

#### GET `/api/jobs/{job_id}`
- **Mô tả:** Lấy chi tiết toàn bộ thông tin của một tin đăng tuyển cụ thể (Mô tả công việc, yêu cầu, quyền lợi...).
- **Tham số (Path):** `job_id` (int) - ID của tin tuyển dụng.
- **Kết quả:** `{"data": {"job_id": 12345, "title": "Backend Developer", "job_description": "...", ...}}`

#### GET `/api/search`
- **Mô tả:** **Hybrid Search (Tìm kiếm lai)**. Sử dụng AI embedding (`pgvector`) kết hợp với khớp từ khóa (Keyword match). Cộng điểm cực mạnh cho các job chứa từ khoá trong Title/Company, đồng thời mang lại kết quả theo ngữ nghĩa cho các từ khóa dài.
- **Tham số (Query):** 
  - `q` (str) - Câu mô tả hoặc từ khóa tìm kiếm.
  - `limit` (int, mặc định 50) - Số lượng kết quả trả về.
  - `ai_estimate` (str, "true"|"false") - Bật/tắt dự đoán lương.
- **Kết quả:** `{"query": "Lập trình web bằng python", "results": [...]}`

#### GET `/api/jobs/{job_id}/related`
- **Mô tả:** Gợi ý các công việc tương tự (Related Jobs) với công việc hiện tại dựa trên mức độ tương đồng ngữ nghĩa của Vector.
- **Tham số (Path):** `job_id` (int) - ID của công việc làm mốc.
- **Tham số (Query):** `limit` (int, mặc định 5)
- **Kết quả:** `{"target_job_id": 12345, "data": [...]}`
