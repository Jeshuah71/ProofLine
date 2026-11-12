
from fastapi.testclient import TestClient
from main import app, limiter


def test_job_offer_rate_limit():
    limiter.reset()

    try:
        with TestClient(app) as client:
            responses = [
                client.post("/analyze", json={
                    "message": "Interview invitation."
                }).status_code
                for _ in range(21)
            ]

        assert responses[:20] == [200] * 20
        assert responses[20] == 429

    finally:
        limiter.reset()


def test_url_analysis_rate_limit():
    limiter.reset()

    try:
        with TestClient(app) as client:
            responses = [
                client.post("/analyze-url", json={
                    "url": "https://example.com/jobs"
                }).status_code
                for _ in range(21)
            ]

        assert responses[:20] == [200] * 20
        assert responses[20] == 429

    finally:
        limiter.reset()
