import ipaddress 
from urllib.parse import urlsplit
def analyze_url(url: str) -> dict:
    # Store possible warning signals 
    signals = []
    
    # Reject unusual control characters or backslashes 
    if any(ord(c) < 32 or ord(c) == 127 for c in url) or "\\" in url:
        return {"status": "invalid", "signals": ["Invalid URL format"] }
    
    try:
        # Separate the URL into componets
        parsed = urlsplit(url.strip())
        hostname = parsed.hostname
        
    except ValueError:
        return {"status": "invalid", "signals": ["Invalid URL format"]}
    
    # Require a usable HTTP or HTTPS URL
    if parsed.scheme not in ("http", "https") or not hostname:
        return {"status": "invalid", "signals": ["Invalid URL format"]}
    
    # Detect potentially misleading user information
    if parsed.username is not None or parsed.password is not None:
        signals.append("URL contains user information before @")
        
    # Check whether HTTPS is missing 
    if parsed.scheme == "http":
        signals.append("URL does not use HTTPS")        
        
    # Detect a numerical IP address instead of a domain
    try:
        ipaddress.ip_address(hostname)
        signals.append("URL uses an IP address")
    
    except ValueError:
        pass
    
    return {
        "status": "checked",
        "hostname": hostname,
        "signals": signals 
    }