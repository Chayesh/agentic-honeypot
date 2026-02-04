import re

URGENCY_KEYWORDS = [
    "urgent", "immediately", "24 hours", "blocked", "suspended"
]

AUTHORITY_KEYWORDS = [
    "bank", "kyc", "account", "verification"
]

ACTION_KEYWORDS = [
    "click", "update", "pay", "submit"
]


def detect_scam(message: str) -> dict:
    text = message.lower()

    signals = {
        "urgency": any(k in text for k in URGENCY_KEYWORDS),
        "authority": any(k in text for k in AUTHORITY_KEYWORDS),
        "action": any(k in text for k in ACTION_KEYWORDS),
        "link": bool(re.search(r"https?://", text))
    }

    score = sum(1 for v in signals.values() if v)
    confidence = score / len(signals)

    scam_type = None
    if signals["authority"] and signals["action"]:
        scam_type = "phishing"

    return {
        "signals": signals,
        "confidence": round(confidence, 2),
        "scam_type": scam_type
    }
