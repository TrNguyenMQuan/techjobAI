# TechJob AI - Nền tảng Thông minh về Thị trường Việc làm IT

## Giới thiệu Tổng quan (Project Overview)

TechJob AI là một hệ thống nền tảng thông minh (Smart Platform) được phát triển nhằm tối ưu hóa quá trình tuyển dụng và tìm kiếm việc làm chuyên biệt trong lĩnh vực Công nghệ Thông tin (IT).

Bằng việc ứng dụng Trí tuệ Nhân tạo (AI) và Khai phá Dữ liệu (Data Mining), TechJob AI giải quyết bài toán "lệch pha" giữa kỹ năng của ứng viên và yêu cầu của nhà tuyển dụng. Đồng thời, nền tảng cung cấp các báo cáo phân tích theo thời gian thực (Real-time Analytics) về xu hướng của thị trường lao động IT.

Dự án được thực hiện trong khuôn khổ môn học Nhập môn Công nghệ Phần mềm (Intro2SE) tại Trường Đại học Khoa học Tự nhiên, ĐHQG-HCM.

---

## Các chức năng chính (Core Features)

Hệ thống được thiết kế theo kiến trúc hướng dịch vụ với các phân hệ (Modules) chuyên biệt đáp ứng nhu cầu của từng nhóm người dùng (Actors).

### 1. Phân hệ Ứng viên (Candidate Module)

#### Quản lý Hồ sơ Điện tử (E-Profile Management)

Hỗ trợ tạo, cập nhật CV động. Tích hợp tính năng trích xuất dữ liệu (Data Parsing) từ CV định dạng PDF/Word hoặc import từ LinkedIn.

#### Khuyến nghị Việc làm Thông minh (AI-driven Job Recommendation)

Ứng dụng các thuật toán Gợi ý (Recommendation System) để đề xuất công việc (Job Matching) dựa trên bộ kỹ năng (Tech Stacks), kinh nghiệm và định hướng nghề nghiệp.

#### Phân tích Khung Năng lực (Skill Gap Analysis)

Đối chiếu hồ sơ ứng viên với các Job Description (JD) mục tiêu, từ đó phân tích các kỹ năng còn thiếu và đề xuất lộ trình học tập (Learning Path).

#### Theo dõi Trạng thái Ứng tuyển (Application Tracking)

Giao diện quản lý toàn bộ vòng đời ứng tuyển:

* Submitted
* In-review
* Interviewing
* Offered

---

### 2. Phân hệ Nhà tuyển dụng (Recruiter Module)

#### Quản lý Tin tuyển dụng (Job Posting Management)

Cung cấp các thao tác CRUD cho tin tuyển dụng, hỗ trợ gắn thẻ (Tagging) các kỹ năng yêu cầu (ví dụ: ReactJS, Python, AWS).

#### Sàng lọc CV Tự động (Automated Resume Screening)

Tự động phân tích ngữ nghĩa CV (Semantic Parsing) và chấm điểm mức độ phù hợp (Matching Score) giữa CV và JD.

#### Hệ thống Quản lý Ứng viên (ATS - Applicant Tracking System)

Trực quan hóa phễu tuyển dụng (Recruitment Funnel) qua bảng Kanban, tích hợp gửi Email tự động và xếp lịch phỏng vấn (Interview Scheduling).

---

### 3. Phân hệ Quản trị viên (Admin Module)

#### Phân quyền & Kiểm soát Truy cập (RBAC - Role-Based Access Control)

Quản lý định danh tài khoản và cấp quyền cho User/Recruiter/Admin.

#### Xác thực Doanh nghiệp (Business KYC)

Quy trình kiểm duyệt và xác thực tính hợp pháp của các công ty đăng ký tài khoản tuyển dụng để chống Spam/Scam.

#### Quản trị Nội dung (CMS)

Quản lý hệ thống dữ liệu từ điển kỹ năng (Skill Taxonomy) và các bài viết nội bộ.

---

### 4. Module Trí tuệ Nhân tạo & Báo cáo (AI & Analytics Module)

#### Bảng điều khiển Xu hướng Thị trường (Market Trend Dashboard)

Trực quan hóa dữ liệu (Data Visualization) về nhu cầu nhân lực, công nghệ xu hướng (Trending Tech Stacks) và phân bố địa lý việc làm.

#### Mô hình Dự báo Lương (Salary Prediction Model)

Đưa ra khoảng lương ước tính (Expected Salary Range) theo thời gian thực dựa vào vị trí, số năm kinh nghiệm và biến động thị trường.

---

## Đội ngũ Phát triển (Team Members)

### Nhóm 6 - CQ 2023/22

* Võ Trần Duy Hoàng - 23120266
* Võ Gia Huy - 23120277
* Nguyễn Hữu Khánh Hưng - 23120271
* Vũ Trần Phúc - 23120333
* Trần Nguyễn Minh Quân - 23120342

### Giảng viên Hướng dẫn

#### Giảng viên Lý thuyết

* TS. Trần Duy Hoàng

#### Giảng viên Thực hành

* ThS. Ngô Ngọc Đăng Khoa
* ThS. Hồ Tuấn Thanh

---

## Cài đặt & Triển khai (Setup & Deployment)

*(Chi tiết về Tech Stack (Frontend/Backend/Database/Cloud) và hướng dẫn clone, setup môi trường (Environment Setup) sẽ được cập nhật trong giai đoạn cài đặt).*
