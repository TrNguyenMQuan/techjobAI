Dựa trên các tài liệu Thiết kế Phần mềm (Software Design) và Kiểm thử Phần mềm (Software Testing) của dự án TechJob AI, hệ sinh thái trí tuệ nhân tạo của dự án không chỉ dừng lại ở một tính năng đơn lẻ mà được phân bổ thành một **kiến trúc 4 tầng trí tuệ**.

Dưới đây là mô tả chi tiết và đầy đủ về toàn bộ các nhiệm vụ của AI được tích hợp trong nền tảng này:

### 1. Tác nhân AI Tự trị (Autonomous ReAct Agent)

Đây là "bộ não" giao tiếp chính của hệ thống, giúp người dùng (Ứng viên/Nhà phân tích) tương tác với dữ liệu thị trường thông qua ngôn ngữ tự nhiên.

* **Mô hình sử dụng:** LLM (ChatOpenAI / GPT-4o) kết hợp cùng thư viện LangGraph.


* **Cơ chế hoạt động:** Agent hoạt động dựa trên vòng lặp Suy luận - Hành động (Reason-Act-Observe). Tác nhân có khả năng tự phân tích câu hỏi, quyết định xem đã đủ thông tin chưa (Reason), và tự động gọi các công cụ thực tế (Act) để tìm câu trả lời.


* **Trực quan hóa dữ liệu (Inline Charts):** Khi được yêu cầu phân tích (ví dụ: "So sánh mức lương Backend/Frontend ở HCM"), AI có khả năng thu thập dữ liệu và trả về kết quả dưới dạng biểu đồ hiển thị trực tiếp trong khung chat.



### 2. Thực thi Công cụ An toàn (Model Context Protocol - MCP Server)

Thay vì để AI truy cập tự do vào cơ sở dữ liệu (tiềm ẩn rủi ro bảo mật và SQL Injection), dự án phân nhiệm vụ tương tác cơ sở dữ liệu cho một cổng MCP Server riêng biệt.

* **Nhiệm vụ Text-to-SQL (SQL Sandbox):** Biến đổi ngôn ngữ tự nhiên thành câu lệnh SQL thông qua `execute_sql_tool`. Đặc biệt, công cụ này bị giới hạn kết nối bằng một phiên làm việc chỉ có quyền Đọc (Read-only view), tự động từ chối và chặn đứng các ảo giác của mô hình nếu AI sinh ra mã thao tác dữ liệu (`DELETE`, `UPDATE`).


* **Nhiệm vụ tra cứu RAG (Retrieval-Augmented Generation):** MCP Server cung cấp `execute_rag_culture_tool` để AI truyền tên công ty vào và trích xuất các đoạn ngữ cảnh (context) về đánh giá môi trường, văn hóa doanh nghiệp từ cơ sở dữ liệu.



### 3. Tìm kiếm Ngữ nghĩa & Xử lý Vector (Semantic Vector Search)

Hệ thống sử dụng AI để thay thế bộ lọc từ khóa truyền thống bằng một bộ máy tìm kiếm hiểu được ngữ cảnh.

* **Mô hình sử dụng:** Sentence Transformers, cụ thể là mô hình mã hóa cục bộ `all-MiniLM-L6-v2`.


* **Nhiệm vụ Mã hóa (Embedding):** Chuyển đổi văn bản tự do (câu hỏi của người dùng, văn hóa công ty, hoặc tin tuyển dụng) thành các mảng số thực gồm 384 chiều (`vector(384)`).


* **Nhiệm vụ Tìm kiếm (Similarity Search):** Sử dụng extension `pgvector` trên PostgreSQL kết hợp với toán tử Cosine Distance để đo lường độ tương đồng ý nghĩa. Ví dụ: Khi người dùng tìm "xử lý dữ liệu thời gian thực", hệ thống AI sẽ tự hiểu và trả về các tin tuyển dụng chứa kỹ năng "Apache Kafka" hoặc "Spark" trong vòng dưới 2 giây.



### 4. Dự đoán Lương bằng Máy học (Hidden Salary Prediction)

Đây là một nhiệm vụ vận dụng Machine Learning truyền thống (Tầng 2) nhằm tăng cường trải nghiệm minh bạch cho ứng viên.

* **Mô hình sử dụng:** Thuật toán `RandomForestRegressor` kết hợp bộ mã hóa đặc trưng `TargetEncoder` thuộc thư viện scikit-learn.


* **Nhiệm vụ:** Rất nhiều tin tuyển dụng trên thị trường để mức lương ẩn (chỉ ghi `is_negotiable = True` hoặc "Thỏa thuận"). AI sẽ thu thập các đặc trưng (Features) như: Kỹ năng công nghệ, số năm kinh nghiệm, địa điểm làm việc... để nội suy và tính toán ra một dải lương tối thiểu/tối đa dự đoán (`predict_hidden_salary`).


* **Hiển thị:** Kết quả này sẽ được hiển thị trên giao diện Job Detail với nhãn "AI Predicted" (Dự đoán bởi AI) mà không ghi đè hay làm sai lệch dữ liệu gốc.



### 5. Khởi tạo Thư ứng tuyển cá nhân hóa (Cover Letter Generation)

Nhiệm vụ này giải quyết trực tiếp "nỗi đau" khi ứng tuyển của người dùng bằng AI tạo sinh (Generative AI) ở Tầng 3.

* **Mô hình sử dụng:** LLM Parser (Mô hình ngôn ngữ lớn) kết hợp với các kỹ thuật prompt template chuẩn hóa văn phong chuyên nghiệp.


* **Nhiệm vụ:** Tự động tiếp nhận nội dung văn bản thô từ tệp CV của ứng viên (PDF) và đồng bộ với nội dung Mô tả công việc (JD) của tin tuyển dụng đang xem.


* **Kết quả:** Sinh ra một bản Cover Letter được cá nhân hóa sâu sắc, tập trung làm nổi bật các kỹ năng của ứng viên sao cho khớp nhất với tiêu chí nhà tuyển dụng, đồng thời loại bỏ các thông tin dư thừa hoặc ảo giác không có trong CV gốc.



Tóm lại, trong dự án TechJob AI, AI không đóng vai trò như một tính năng gắn thêm (add-on), mà chính là cốt lõi (core) chi phối toàn bộ hành trình trải nghiệm: từ lúc **hiểu truy vấn tìm kiếm** -> **dự đoán dải lương** -> **tự động viết thư ứng tuyển** -> cho đến **trò chuyện phân tích thị trường chuyên sâu**.