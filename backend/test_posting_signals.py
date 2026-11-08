from posting_signals import detect_posting_signals

def test_required_registration_fee():
    text = "Applicants must pay a registration fee before starting."
    
    signals = detect_posting_signals(text)
    
    assert len(signals) == 1
    
def test_not_payment_requirement():
    text = "We never ask applicants to pay a registration fee."
    
    signals = detect_posting_signals(text)
    
    assert signals == [] 