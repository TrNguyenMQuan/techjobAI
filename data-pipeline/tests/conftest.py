# tests/conftest.py
import pytest
from unittest.mock import MagicMock
from pyspark.sql import SparkSession


# scope="session": SparkSession được tạo 1 lần cho toàn bộ test run
# (khởi động Spark mất ~5s — không muốn làm điều này mỗi test function)
@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder
        .master("local[1]")        # local[1]: dùng 1 core, đủ cho test
        .appName("techjobai-tests")
        .config("spark.ui.enabled", "false")       # tắt Spark UI khi test
        .config("spark.sql.shuffle.partitions", "1") # giảm partitions cho data nhỏ
        .getOrCreate()
    )
    yield session                  # yield thay vì return → pytest chạy cleanup sau
    session.stop()                 # teardown: stop Spark sau khi tất cả tests xong


# scope="function": mock mới cho mỗi test — tránh state leak giữa các tests
@pytest.fixture(scope="function")
def mock_httpx_client():
    # MagicMock tạo object giả lập — gọi method gì cũng được, không cần network
    return MagicMock()


# Dữ liệu mẫu dùng chung cho nhiều test — 3 jobs đủ để test logic, không cần 882
@pytest.fixture
def sample_jobs():
    return [
        {
            "jobId": 1001,
            "jobTitle": "Senior Data Engineer",
            "companyId": 501,
            "companyName": "Tech Corp",
            "salaryMin": 2000,
            "salaryMax": 3000,
            "skills": [{"skillId": 1, "skillName": "Python", "skillWeight": 100}],
            "workingLocations": [{"cityId": 1, "cityName": "Ho Chi Minh", "cityNameVI": "Hồ Chí Minh", "address": ""}],
        },
        {
            "jobId": 1002,
            "jobTitle": "Data Analyst",
            "companyId": 501,          # cùng công ty với job trên — test dedup
            "companyName": "Tech Corp",
            "salaryMin": 1000,
            "salaryMax": None,         # salary null — test edge case
            "skills": [],              # không có skill — test empty array
            "workingLocations": [{"cityId": 2, "cityName": "Ha Noi", "cityNameVI": "Hà Nội", "address": ""}],
        },
        {
            "jobId": 1003,
            "jobTitle": "ML Engineer",
            "companyId": 502,
            "companyName": "AI Startup",
            "salaryMin": 3000,
            "salaryMax": 5000,
            "skills": [
                {"skillId": 1, "skillName": "Python", "skillWeight": 100},
                {"skillId": 2, "skillName": "TensorFlow", "skillWeight": 80},
            ],
            "workingLocations": [{"cityId": 1, "cityName": "Ho Chi Minh", "cityNameVI": "Hồ Chí Minh", "address": ""}],
        },
    ]
