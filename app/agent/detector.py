import re

SCAM_KEYWORDS = [
    "kyc", "blocked", "suspended", "verify",
    "urgent", "click", "immediately", "pay",
    "upi", "account", "warning"
]

URL_REGEX = re.compile(r"https?://\S+")
UPI_REGEX = re.compile(r"\b[\w.-]+@upi\b", re.IGNORECASE)
PHONE_REGEX = re.compile(r"\b\d{10}\b")


def detect_scam(text: str) -> dict:
    text_lower = text.lower()

    keyword_hits = [k for k in SCAM_KEYWORDS if k in text_lower]
    has_link = bool(URL_REGEX.search(text))
    has_upi = bool(UPI_REGEX.search(text))
    has_phone = bool(PHONE_REGEX.search(text))
    has_urgency = any(w in text_lower for w in ["urgent", "immediately", "final"])

    confidence = 0.0
    confidence += 0.15 * len(keyword_hits)
    confidence += 0.2 if has_link else 0
    confidence += 0.2 if has_upi else 0
    confidence += 0.1 if has_phone else 0
    confidence += 0.1 if has_urgency else 0

    confidence = min(confidence, 1.0)

    return {
        "confidence": confidence,
        "scam_type": "phishing" if has_link else "payment_fraud" if has_upi else None,
        "signals": {
            "keywords": keyword_hits,
            "link": has_link,
            "upi": has_upi,
            "phone": has_phone,
            "urgency": has_urgency
        }
    }
