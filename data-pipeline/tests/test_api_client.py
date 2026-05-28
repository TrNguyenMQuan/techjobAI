# tests/test_api_client.py
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

# ─── Dữ liệu giả trả về từ API ──────────────────────────────────────────────
FAKE_RESPONSE = {
    "meta": {"nbHits": 2, "page": 0, "nbPages": 1},
    "data": [
        {"jobId": 1001, "jobTitle": "Data Engineer", "companyId": 501},
        {"jobId": 1002, "jobTitle": "ML Engineer",   "companyId": 502},
    ],
}

# ─── Fixture: client đã được patch sẵn boto3 (tránh cần MinIO) ──────────────
@pytest.fixture
def client():
    # patch boto3.client: VietnamWorksClient.__init__ tạo boto3 client → cần mock
    # nếu không patch, test sẽ fail vì không kết nối được MinIO
    with patch("source.vietnamworks_client.boto3.client"):
        from source.vietnamworks_client import VietnamWorksClient
        return VietnamWorksClient()


# ─── Test 1: fetch_page trả về đúng data ────────────────────────────────────
@pytest.mark.asyncio
async def test_fetch_page_returns_data(client):
    # Tạo mock response: .raise_for_status() không làm gì, .json() trả về FAKE
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = FAKE_RESPONSE

    # AsyncMock: khi code gọi `await client.post(...)`, trả về mock_response
    mock_httpx = AsyncMock()
    mock_httpx.post = AsyncMock(return_value=mock_response)

    # Truyền mock_httpx vào thay cho httpx.AsyncClient thật
    result = await client.fetch_page(mock_httpx, page=0)

    assert result["meta"]["nbHits"] == 2          # meta đúng
    assert len(result["data"]) == 2               # đủ 2 jobs
    assert result["data"][0]["jobId"] == 1001      # job đầu tiên đúng


# ─── Test 2: retry khi server trả 500 ───────────────────────────────────────
@pytest.mark.asyncio
async def test_fetch_page_raises_on_http_error(client):
    import httpx
    from tenacity import wait_none

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500", request=MagicMock(), response=MagicMock()
    )

    mock_httpx = AsyncMock()
    mock_httpx.post = AsyncMock(return_value=mock_response)

    # Patch wait → wait_none() để retry không sleep thật trong test
    client.fetch_page.retry.wait = wait_none()

    with pytest.raises(httpx.HTTPStatusError):
        await client.fetch_page(mock_httpx, page=0)


# ─── Test 3: payload gửi đi có đúng filter IT không ────────────────────────
@pytest.mark.asyncio
async def test_fetch_page_sends_it_filter(client):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = FAKE_RESPONSE

    mock_httpx = AsyncMock()
    mock_httpx.post = AsyncMock(return_value=mock_response)

    await client.fetch_page(mock_httpx, page=0)

    # Kiểm tra payload đã gửi: call_args[1]["json"] là dict truyền vào post()
    sent_payload = mock_httpx.post.call_args[1]["json"]
    filter_field = sent_payload["filter"][0]["field"]
    assert filter_field == "jobFunction"           # đúng filter field
    assert sent_payload["hitsPerPage"] == 50       # page size đúng
