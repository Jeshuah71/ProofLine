from fastapi.testclient import TestClient
from company_registry import get_reference_record
from main import app

# Create a client to test our API
client = TestClient(app)

def test_payment_warning():
    # Send a suspicious message
    response = client.post("/analyze", json={
        "message": "You must send money before your interview."
    })
    
    # Check that the API responded successfully
    assert response.status_code == 200
    
    # Check that the payment warning was detected
    warnings = response.json()["warnings"]
    assert any("send money" in w for w in warnings)
    
def test_negated_payment_warning():
    # Send a message advising against payment
    response = client.post("analyze", json={
        "message": "We will never ask you to send moeny."
    })
    
    # The negated phrase should not trigger a warning
    warnings = response.json()["warnings"]
    assert not any("send money" in w for w in warnings)
    

def test_urgency_warning():
    # Test a message that pressures the applicant
    response = client.post("/analyze", json={
        "message": "Act immediately to accept this job offer."
    })

    warnings = response.json()["warnings"]

    # Verify that an urgency warning exists
    assert response.status_code == 200
    assert any("Urgency:" in w for w in warnings)


def test_no_warning_signs():
    # Test a message without known warning patterns
    response = client.post("/analyze", json={
        "message": "We would like to schedule an interview next week."
    })

    warnings = response.json()["warnings"]

    # Expect no matches from our current rules
    assert response.status_code == 200
    assert len(warnings) == 0
    
def test_misleading_website_url():
    # Test a URL containing misleading user information 
    response = client.post("/analyze", json={
        "message": "We would like to invite you to an interview.",
        "recruiter_email": "jobs@example.com",
        "company_website": "https://example.com@fake-recruiter.test/jobs"
    })
    
    assert response.status_code == 200
    
    # The comparison should reject this URL 
    assert response.json()["domain_check"] is None


def test_lookalike_domain():
    # Test a domain with '1' instead of 'l'
    response = client.post("/analyze", json={
        "message": "We would like to invite you to an interview.",
        "recruiter_email": "recruiter@examp1e.com",
        "company_website": "https://example.com"
    })

    assert response.status_code == 200

    domain = response.json()["domain_check"]

    # Verify our lookalike rule detected the difference
    assert domain["potential_lookalike"] is True

def test_more_lookalike_variants():
    # Test missing, extra and swapped characters
    domains = [
        "exaple.com",
        "exammple.com",
        "examlpe.com"
    ]
    
    for domain in domains:
        response = client.post("/analyze", json={
            "message": "We would like to invite you to an interview.",
            "recruiter_email": f"jobs@{domain}",
            "company_website": "https://example.com"
        })
        
        assert response.status_code == 200
        
        result = response.json()["domain_check"]
        assert result["potential_lookalike"] is True
        
def test_microsoft_reference():
    # Look up the company's stored reference
    record = get_reference_record("Microsoft")

    # Verify the expected domain and source metadata
    assert record is not None
    assert record["domain"] == "microsoft.com"
    assert record["verified"] is True
    assert record["verification_scope"] == "company_domain_only"
