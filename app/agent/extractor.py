import re

UPI_REGEX = re.compile(r"\b[\w.-]+@[\w.-]+\b")
URL_REGEX = re.compile(r"https?://[^\s]+")
PHONE_REGEX = re.compile(r"\+91[-\s]?\d{10}")
ACCOUNT_REGEX = re.compile(r"\b\d{9,18}\b")

def extract_intel(text: str) -> dict | None:
    intel = {}

    upi_ids = UPI_REGEX.findall(text)
    urls = URL_REGEX.findall(text)
    phones = PHONE_REGEX.findall(text)
    accounts = ACCOUNT_REGEX.findall(text)

    if upi_ids:
        intel["upi_id"] = upi_ids
    if urls:
        intel["phishing_url"] = urls
    if phones:
        intel["phone_number"] = phones
    if accounts:
        intel["bank_account"] = accounts

    return intel if intel else None
