-- ============================================
-- Tạo extension pgvector
-- ============================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- Tạo database riêng cho Airflow metadata
-- ============================================
CREATE USER airflow WITH PASSWORD 'airflow';
CREATE DATABASE airflow OWNER airflow;

-- ============================================
-- Tạo schema staging (Silver)
-- ============================================
CREATE SCHEMA IF NOT EXISTS staging;

-- Bảng raw jobs từ VietnamWorks API
CREATE TABLE staging.raw_jobs (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(100) UNIQUE NOT NULL,   -- ID gốc từ VietnamWorks
    source_name VARCHAR(50) DEFAULT 'vietnamworks',
    raw_title TEXT,
    raw_company_name TEXT,
    raw_location TEXT,
    raw_salary TEXT,                           -- Giữ nguyên text gốc "10-20 triệu" hoặc "Thỏa thuận"
    raw_experience TEXT,
    raw_job_type TEXT,                         -- Full-time, Part-time...
    raw_work_mode TEXT,                        -- Onsite, Remote, Hybrid
    raw_description TEXT,
    raw_requirements TEXT,
    raw_benefits TEXT,
    raw_skills TEXT,                           -- JSON array hoặc comma-separated
    raw_company_size TEXT,
    raw_logo_url TEXT,
    raw_source_url TEXT,                       -- Link gốc trên VietnamWorks
    raw_posted_date TEXT,
    raw_deadline TEXT,
    raw_quantity TEXT,
    raw_payload JSONB,                         -- Lưu nguyên JSON response để backup
    ingested_at TIMESTAMP DEFAULT NOW(),
    is_processed BOOLEAN DEFAULT FALSE
);
ALTER TABLE staging.raw_jobs ADD CONSTRAINT raw_jobs_source_id_unique UNIQUE (source_id);
-- Index cho query thường dùng
CREATE INDEX idx_raw_jobs_source_id ON staging.raw_jobs(source_id);
CREATE INDEX idx_raw_jobs_is_processed ON staging.raw_jobs(is_processed);

-- ============================================
-- Tạo schema warehouse (Gold)
-- ============================================
CREATE SCHEMA IF NOT EXISTS warehouse;

-- Dimension: Công ty
CREATE TABLE warehouse.dim_company (
    company_id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    company_size VARCHAR(50),
    logo_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_name)
);

-- Dimension: Kỹ năng
CREATE TABLE warehouse.dim_skill (
    skill_id SERIAL PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),                      -- language, framework, tool, soft_skill...
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(skill_name)
);

-- Dimension: Địa điểm
CREATE TABLE warehouse.dim_location (
    location_id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    normalized_city VARCHAR(50),               -- HCM, HN, DN...
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(city)
);

-- Fact: Tin tuyển dụng
CREATE TABLE warehouse.fact_job (
    job_id SERIAL PRIMARY KEY,
    source_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    company_id INT REFERENCES warehouse.dim_company(company_id),
    location_id INT REFERENCES warehouse.dim_location(location_id),
    salary_min NUMERIC,
    salary_max NUMERIC,
    salary_currency VARCHAR(10) DEFAULT 'VND',
    is_salary_estimated BOOLEAN DEFAULT FALSE, -- TRUE nếu lương do ML dự đoán
    experience_level VARCHAR(50),              -- intern, fresher, junior, mid, senior, lead
    years_of_experience_min INT,
    years_of_experience_max INT,
    job_type VARCHAR(50),                      -- full-time, part-time, contract, freelance
    work_mode VARCHAR(50),                     -- onsite, remote, hybrid
    description TEXT,
    requirements TEXT,
    benefits TEXT,
    source_url TEXT,
    posted_date DATE,
    deadline DATE,
    quantity INT,
    is_active BOOLEAN DEFAULT TRUE,
    embedding vector(768),                     -- Vector cho semantic search
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Bridge: Job - Skill (nhiều-nhiều)
CREATE TABLE warehouse.job_skill (
    job_id INT REFERENCES warehouse.fact_job(job_id) ON DELETE CASCADE,
    skill_id INT REFERENCES warehouse.dim_skill(skill_id) ON DELETE CASCADE,
    is_required BOOLEAN DEFAULT TRUE,          -- TRUE = bắt buộc, FALSE = ưu tiên
    PRIMARY KEY (job_id, skill_id)
);

-- ============================================
-- Bảng dashboard cache (pre-computed)
-- ============================================
CREATE TABLE warehouse.agg_top_skills (
    skill_name VARCHAR(100),
    job_count INT,
    percentage NUMERIC(5,2),
    computed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE warehouse.agg_salary_by_title (
    title_group VARCHAR(100),
    avg_salary NUMERIC,
    median_salary NUMERIC,
    p25_salary NUMERIC,
    p75_salary NUMERIC,
    min_salary NUMERIC,
    max_salary NUMERIC,
    sample_count INT,
    computed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE warehouse.agg_trend_monthly (
    month DATE,
    metric_name VARCHAR(50),                   -- job_count, avg_salary, skill_demand
    metric_value NUMERIC,
    dimension VARCHAR(100),                    -- Tên skill hoặc title nếu cần
    computed_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Index cho performance
-- ============================================
CREATE INDEX idx_fact_job_company ON warehouse.fact_job(company_id);
CREATE INDEX idx_fact_job_location ON warehouse.fact_job(location_id);
CREATE INDEX idx_fact_job_posted_date ON warehouse.fact_job(posted_date);
CREATE INDEX idx_fact_job_experience ON warehouse.fact_job(experience_level);
CREATE INDEX idx_fact_job_active ON warehouse.fact_job(is_active);

-- Vector index cho semantic search (HNSW)
CREATE INDEX idx_fact_job_embedding ON warehouse.fact_job 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
