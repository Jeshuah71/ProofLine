from fastapi.testclient import TestClient
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
