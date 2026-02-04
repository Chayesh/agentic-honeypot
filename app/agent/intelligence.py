import re


def extract_intelligence(message: str, state: dict) -> dict:
    intel = {}

    # UPI ID detection
    upi_match = re.search(r"\b[\w.-]+@[\w.-]+\b", message)
    if upi_match:
        intel["upi_id"] = upi_match.group()

    # URL detection
    url_match = re.search(r"https?://\S+", message)
    if url_match:
        intel["phishing_url"] = url_match.group()

    # Amount detection
    amt_match = re.search(r"\b(?:rs|₹)?\s?\d{3,6}\b", message.lower())
    if amt_match:
        intel["amount"] = amt_match.group()

    if intel:
        intel["scam_type"] = state["scam_assessment"]["scam_type"]
        intel["turn"] = state["metrics"]["turns"]

    return intel
