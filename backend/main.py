from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse
from company_registry import get_reference_domain, get_reference_record
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
    
    # Additional information (optional)
    company_name: str | None = None
    recruiter_email: str | None = None
    company_website: str | None = None
    
def is_one_char_lookalike(domain_a: str, domain_b: str) -> bool:
    # Different lengths cannot be a one-character substitution
    if len(domain_a) != len(domain_b):
        return False
    
    # COunt positions containing different charactes
    differences = sum(
        a != b for a, b in zip(domain_a, domain_b)
    )
    
    # Return True if exactly one character differs
    return differences == 1

def is_typo_variant(a: str, b: str) -> bool:
    # Check single-character replacements
    if is_one_char_lookalike(a, b):
        return True
    
    # Check one missing or extra character
    if abs(len(a) - len(b)) == 1:
        shorter, longer = sorted([a,b], key=len)
        
        return any(
            longer[:i] + longer[i + 1:] == shorter
            for i in range(len(longer))
        )
    # Check two neighboring characters swapped
    if len(a) == len(b):
        return any(
            a[:i] + a[i + 1] + a[i] + a[i + 2:] == b
            for i in range(len(a) - 1)
        )
    return False

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
        
    # Store the domain comparison result
    domain_check = None
    
    # Compare only when both fields are provided
    if job_offer.recruiter_email and job_offer.company_website:
        
        # Normalize the email address
        email = job_offer.recruiter_email.strip().lower()
        
        # Parse the company website URL
        website = urlparse(job_offer.company_website.strip())
        
        # Check that both values have a usable format
        if (
            email.count("@") == 1
            and website.scheme in ("http", "https")
            and website.hostname
            # Reject URLs containing user information
            and website.username is None
            and website.password is None
        ): 
            # Extract the two domains
            email_domain = email.split("@")[1]
            website_domain = website.hostname.lower().removeprefix("www.")
            
            # Check if the domains are identical
            exact_match = email_domain == website_domain
            
            # Check if the email uses a subdomain
            is_subdomain = email_domain.endswith("." + website_domain)
            
            # Detect a possible one-character lookalike domain
            potential_lookalike = (
                not exact_match
                and not is_subdomain
                and is_typo_variant(email_domain, website_domain)
            )
            
            # Compare domains without making a trust decision
            domain_check = {
                "email_domain": email_domain,
                "website_domain": website_domain,
                "exact_match": exact_match,
                "is_subdomain": is_subdomain,
                "potential_lookalike": potential_lookalike
            }
    # No validation error by default
    domain_error = None
    
    # Both fields were entered, but comparison failed
    if (
        job_offer.recruiter_email
        and job_offer.company_website
        and domain_check is None
    ):
        domain_error = (
            "Unable to compare these domains. "
            "Check the email and website format. "
            "Avoid URLs containing misleading @ symbols."
        )
        
    # Look up the company's domain in our demo registry
    reference_domain = get_reference_domain(job_offer.company_name)
    
    # Store the comparison result
    reference_check = None
    
    # check only when we have both values
    if reference_domain and job_offer.recruiter_email:
        email = job_offer.recruiter_email.strip().lower()
        
        # Basic email structure check 
        if email.count("@") == 1:
            username, email_domain = email.split("@")
            
            if username and email_domain and " " not in email:
                # Compare against our registery
                exact = email_domain == reference_domain
                
                subdomain = email_domain.endswith(
                    "." + reference_domain
                )
                
                reference_check = {
                    "email_domain": email_domain,
                    "reference_domain": reference_domain,
                    "matches_reference": exact or subdomain
                }
    
    # Retrieve the company reference information
    reference_record = get_reference_record(job_offer.company_name)
    # Return the analysis results
    return {
        "status": "analyzed",
        "characters": len(clean_message),
        "warning_count": len(warnings),
        "warnings": warnings,
        "assessment": assessment,
        "recommendations": recommendations,
        "domain_check": domain_check,
        "domain_error": domain_error,
        "reference_domain": reference_domain,
        "reference_check": reference_check,
        "reference_record": reference_record,
    }
    