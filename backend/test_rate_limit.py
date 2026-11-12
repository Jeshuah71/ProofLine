
from fastapi.testclient import TestClient
from main import app, limiter


def test_ml_rate_limit():
    # Start with fresh counters
    limiter.reset()

    client = TestClient(app)

    try:
        # Send six requests to the ML endpoint
        responses = []

        for _ in range(6):
            response = client.post(
                "/analyze-posting",
                json={
                    "title": "Software Engineer",
                    "description": "We are hiring a developer."
                }
            )
            responses.append(response.status_code)

        # First five requests should succeed
        assert responses[:5] == [200] * 5

        # Sixth request should be blocked
        assert responses[5] == 429

    finally:
        # Avoid affecting other tests
        limiter.reset()
