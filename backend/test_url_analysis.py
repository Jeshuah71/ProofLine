from url_analysis import analyze_url

def test_misleading_url():
    result = analyze_url(
        "https://example.com@fake-recruiter.test/jobs"
    )
    
    assert result["hostname"] == "fake-recruiter.test"
    assert len(result["signals"]) == 1
    
    
def test_regular_url():
    result = analyze_url("https://example.com/jobs")
    
    assert result["hostname"] == "example.com"
    assert result["signals"] == []
    

def test_http_url():
    result = analyze_url("http://example.com/jobs")
    
    assert "URL does not use HTTPS" in result["signals"]
    

def test_url_without_scheme():
    # A URL without HTTP or HTTPS is invalid
    result = analyze_url("example.com/jobs")

    assert result["status"] == "invalid"


def test_url_with_backslash():
    # Reject potentially confusing URL formatting
    result = analyze_url(
        "https://example.com\\@fake-recruiter.test"
    )

    assert result["status"] == "invalid"
