
import httpx
import rdap_lookup


def test_rdap_uses_fixed_server(monkeypatch):
    # Replace the network request with a controlled response
    def fake_get(url, **kwargs):
        assert url == (
            "https://rdap.verisign.com/com/v1/domain/microsoft.com"
        )
        assert kwargs["follow_redirects"] is False

        return httpx.Response(
            200,
            json={
                "events": [{
                    "eventAction": "registration",
                    "eventDate": "2000-01-01T00:00:00Z"
                }]
            }
        )

    monkeypatch.setattr(rdap_lookup.httpx, "get", fake_get)

    result = rdap_lookup.get_domain_registration("Microsoft")

    assert result["status"] == "checked"
    assert result["registered_at"] == "2000-01-01T00:00:00Z"


def test_rdap_does_not_follow_redirect(monkeypatch):
    # Simulate a redirect to a local address
    def fake_get(url, **kwargs):
        assert kwargs["follow_redirects"] is False

        return httpx.Response(
            302,
            headers={"Location": "http://127.0.0.1/admin"}
        )

    monkeypatch.setattr(rdap_lookup.httpx, "get", fake_get)

    result = rdap_lookup.get_domain_registration("Microsoft")

    assert result["status"] == "unavailable"
