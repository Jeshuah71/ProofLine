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


def test_url_analysis_endpoint():
    # Send a misleading URL to our API
    response = client.post("/analyze-url", json={
        "url": "https://example.com@fake-recruiter.test/jobs"
    })

    # Verify the API responded successfully
    assert response.status_code == 200

    result = response.json()

    # Verify the actual hostname
    assert result["hostname"] == "fake-recruiter.test"

    # Verify a warning was detected
    assert len(result["signals"]) == 1


def test_analyze_offer_with_url():
    # Send a job offer containing a suspicious URL
    response = client.post("/analyze", json={
        "message": "We would like to schedule an interview.",
        "job_url": "https://example.com@fake-recruiter.test/jobs"
    })

    # Verify the request succeeded
    assert response.status_code == 200

    data = response.json()

    # Verify URL analysis was included
    assert data["url_check"]["status"] == "checked"

    # Verify the actual hostname
    assert data["url_check"]["hostname"] == "fake-recruiter.test"

    # Verify a warning was detected
    assert len(data["url_check"]["signals"]) == 1

def test_rejects_oversized_message():
    # Message exceeds the 10,000-character limit
    response = client.post("/analyze", json={
        "message": "A" * 10001
    })
    
    assert response.status_code == 422
    
def test_rejects_oversized_posting():
    # Description exceeds the 15,000-character limit 
    response = client.post("/analyze-posting", json= {
        "title": "Software Engineer",
        "description": "A" * 15001
    })
    
    assert response.status_code == 422
    
    
def test_cors_allows_frontend():
    # Simulate a browser's CORS preflight request
    response = client.options(
        "/analyze",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200

    assert response.headers.get(
        "access-control-allow-origin"
    ) == "http://localhost:5173"


def test_cors_rejects_unknown_origin():
    # Simulate a request from an unapproved website
    response = client.options(
        "/analyze",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400

    assert response.headers.get(
        "access-control-allow-origin"
    ) is None


def test_private_input_not_reflected_in_validation_error():
    # Send an oversized message containing a private marker
    private_message = "PRIVATE_TEST_VALUE_" + "A" * 10001

    response = client.post("/analyze", json={
        "message": private_message
    })

    # Invalid input should be rejected
    assert response.status_code == 422

    # The private marker should not appear in the response
    assert "PRIVATE_TEST_VALUE_" not in response.text


def test_analysis_response_has_privacy_headers():
    response = client.post("/analyze", json={
        "message": "We would like to schedule an interview."
    })

    assert response.status_code == 200

    assert response.headers["cache-control"] == "no-store"

    assert response.headers["x-content-type-options"] == "nosniff"


def test_payment_amount_updates_assessment():
    response = client.post("/analyze", json={
        "message": "To start your new job, pay $250."
    })

    assert response.status_code == 200

    data = response.json()

    assert any(
        "pay $250" in warning
        for warning in data["warnings"]
    )

    assert data["warning_count"] == 1
    assert data["assessment"] == "Review recommended"

def test_rejects_whitespace_message():
    # Message contains only spaces
    response = client.post("/analyze", json={
        "message": "    "
    })
    
    assert response.status_code == 422


def test_rejects_missing_message():
    # Required message field is missing
    response = client.post("/analyze", json={})

    assert response.status_code == 422
    

def test_rejects_oversized_request_body():
    # Create an HTTP body larger than 256 KiB
    response = client.post(
        "/analyze",
        json={"message": "A" * 300000}
    )

    # The server should reject the oversized body
    assert response.status_code == 413


def test_accepts_normal_request_body():
    # A normal request should continue working
    response = client.post(
        "/analyze",
        json={
            "message": "We would like to schedule an interview."
        }
    )

    assert response.status_code == 200
