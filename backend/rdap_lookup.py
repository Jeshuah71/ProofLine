import httpx
from company_registry import get_reference_record

def get_domain_registration(company_name: str) -> dict:
    # Only use documented registery references
    record = get_reference_record(company_name)
    
    if not record or not record.get("verified", False):
        return {"status": "no_reference"}
    
    domain = record["domain"]
    
    try:
        # Request registration information from RDAP
        response = httpx.get(
            f"https://rdap.org/domain/{domain}",
            timeout=8.0,
            follow_redirects=True
        )
        
        response.raise_for_status()
        data = response.json()
        
    except (httpx.HTTPError, ValueError):
        # Handle network errors or invalid responses
        return {"status": "unavailable", "domain": domain}
    
    # Find the registration event
    registered_at = None
    
    for event in data.get("events", []):
        if event.get("eventAction") == "registration":
            registered_at = event.get("eventDate")
            break
    
    return {
        "status": "checked",
        "domain": domain,
        "registered_at": registered_at
    }
    
# RUN this example only when executing this file directly
if __name__ == "__main__":
    print(get_domain_registration("Microsoft"))