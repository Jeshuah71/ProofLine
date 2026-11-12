
from fastapi.testclient import TestClient
import main


def test_domain_registration_rate_limit(monkeypatch):
    # Avoid making real network requests
    def fake_lookup(company_name):
        return {
            "status": "checked",
            "domain": "microsoft.com",
            "registered_at": None
        }

    monkeypatch.setattr(
        main, "get_domain_registration", fake_lookup
    )

    # Clear previous rate-limit counters
    main.limiter.reset()

    try:
        with TestClient(main.app) as client:
            responses = []

            for _ in range(11):
                response = client.get(
                    "/domain-registration",
                    params={"company_name": "Microsoft"}
                )
                responses.append(response.status_code)

        # First ten requests should succeed
        assert responses[:10] == [200] * 10

        # Eleventh request should be limited
        assert responses[10] == 429

    finally:
        main.limiter.reset()
