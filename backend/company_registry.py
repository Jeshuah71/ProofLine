# Demo reference data - not independently verified 
COMPANY_DOMAINS = {
    "example technologies": {
        "domain": "example.com",
        "source": "demo",
        "verified": False
    },
    "sample labs": {
        "domain": "sample.test",
        "source": "demo",
        "verified": False
    },
    "microsoft": {
        "domain": "microsoft.com",
        "source": "https://careers.microsoft.com/v2/global/en/hiringfaqs.html",
        "verified": True,
        "checked_at": "2026-11-01",
        "verification_scope": "company_domain_only"
    },
}

def get_reference_record(company_name: str | None):
    # Return None when no company was provided 
    if not company_name:
        return None
    
    # Normalize company name
    name = company_name.strip().lower()
    
    # look up the domain in our reference dictionary
    return COMPANY_DOMAINS.get(name)

def get_reference_domain(company_name: str | None):
    # Reuse our existing lookup function
    record = get_reference_record(company_name)
    
    return record["domain"] if record else None
