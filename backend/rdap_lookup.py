
import re
import httpx
from company_registry import get_reference_record


# Fixed RDAP endpoints for supported extensions
RDAP_SERVERS = {
    "com": "https://rdap.verisign.com/com/v1/domain/",
    "net": "https://rdap.verisign.com/net/v1/domain/",
}


def get_domain_registration(company_name: str) -> dict:
    # Use documented company references only
    record = get_reference_record(company_name)

    if not record or not record.get("verified", False):
        return {"status": "no_reference"}

    domain = record["domain"].strip().lower()

    # Validate domain format before constructing a URL
    domain_pattern = (
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z]{2,63}"
    )

    if len(domain) > 253 or not re.fullmatch(domain_pattern, domain):
        return {"status": "unavailable", "domain": domain}

    # Allow only supported top-level domains
    extension = domain.rsplit(".", 1)[-1]
    server = RDAP_SERVERS.get(extension)

    if server is None:
        return {"status": "unavailable", "domain": domain}

    try:
        # Use a fixed HTTPS server; do not follow redirects
        response = httpx.get(
            server + domain,
            timeout=8.0,
            follow_redirects=False,
            trust_env=False,
        )

        # Reject errors and unexpected redirects
        if response.status_code != 200:
            return {"status": "unavailable", "domain": domain}

        data = response.json()

    except (httpx.HTTPError, ValueError):
        return {"status": "unavailable", "domain": domain}

    # Extract the domain registration date
    registered_at = None

    events = data.get("events", [])

    if isinstance(events, list):
        for event in events:
            if isinstance(event, dict):
                if event.get("eventAction") == "registration":
                    registered_at = event.get("eventDate")
                    break

    return {
        "status": "checked",
        "domain": domain,
        "registered_at": registered_at,
    }


if __name__ == "__main__":
    print(get_domain_registration("Microsoft"))
