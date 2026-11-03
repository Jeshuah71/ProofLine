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