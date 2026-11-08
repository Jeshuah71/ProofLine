
import re


def detect_posting_signals(text: str) -> list[str]:
    # Store warning patterns found in the posting
    signals = []

    # Detect explicit requirements to pay an employment fee
    payment_pattern = (
        r"\b(?:applicants|candidates|you)\s+"
        r"(?:(?:are\s+)?required\s+to|must|need\s+to|have\s+to)\s+"
        r"pay\s+(?:a\s+|an\s+|the\s+)?"
        r"(?:registration|processing|application|training)\s+fee\b"
    )

    if re.search(payment_pattern, text, re.IGNORECASE):
        signals.append(
            "The posting appears to require an employment-related fee."
        )

    return signals
