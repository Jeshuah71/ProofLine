from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import re

# Create the API application
app = FastAPI()

# Allow our React development server to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# Define what data the API expects
class JobOfferRequest(BaseModel):
    message: str

# Endpoint to check whether the backend is running 
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Receive a job-offer message
@app.post("/analyze")
def analyze_offer(job_offer: JobOfferRequest):
    
    # Remove unnecessary spaces 
    clean_message = job_offer.message.strip()
    text = clean_message.lower()
    
    # Phrases that may indicate suspicious payments
    warning_rules = {
        "Payment Requests": [
            "registration fee",
            "pay upfront",
            "send money"
        ],
        "Urgency": [
            "act immediately",
            "limited time",
            "respond within 24 hours"
        ]
    }
    # Store the warning we find 
    warnings = []
    
    # Check every category and its phrases
    for category, phrases in warning_rules.items():
        for phrase in phrases:
            
            # Find each occurence of the phrase
            for match in re.finditer(
                rf"\b{re.escape(phrase)}\b", text
            ):
                # Read up to 20 characters before the match
                before = text[max(0, match.start() - 20):match.start()]
                
                # Ignore some explicitly negated phrases
                if before.endswith(("do not", "don't ", "never ", "never ask you to ", "do not ask you to ")):
                    continue
                
                warnings.append(
                    f"{category}: detected `{phrase}`"
                )
                break
    # Determine an assessment based on detected warning 
    warning_count = len(warnings)
    
    if warning_count == 0:
        assessment = "No warning signs detected"
        
    elif warning_count == 1:
        assessment = "Review recommended"
    else:
        assessment = "Multiple warning signs detected"
                
    # Detect requests to pay a dollar amount
    payment_pattern = r"\b(?:pay|send|transfer)\s+\$\d+(?:\.\d{2})?\b"
    
    # Search for the pattern in the message
    payment_match = re.search(payment_pattern, text)
    
    # Add a warning if a match is found
    if payment_match:
        warnings.append(
            f"Payment Requests: possible payment of "
            f"{payment_match.group()}"
        )
        
    # Store advice based on detected warning categories
    recommendations = []
    
    # Check if any payment-related warning exists
    if any(w.startswith("Payment Requests:") for w in warnings):
        recommendations.append(
            "Be cautious about paying money to secure a job. "
            "Verify the request with the employer independently."
            
        )
        
    # Check if any urgency-related warning exists
    if any(w.startswith("Urgency:") for w in warnings):
        recommendations.append(
            "Avoid making rushed decisions. "
            "Verify the offer through the company's official website."
        )
    # Return the analysis results
    return {
        "status": "analyzed",
        "characters": len(clean_message),
        "warning_count": len(warnings),
        "warnings": warnings,
        "assessment": assessment,
        "recommendations": recommendations
    }
    