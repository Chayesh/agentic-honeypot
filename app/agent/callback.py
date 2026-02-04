import requests
from app.config import settings

def send_final_result(state):
    payload = {
        "sessionId": state["conversation_id"],
        "scamDetected": True,
        "totalMessagesExchanged": state["metrics"]["turns"],
        "extractedIntelligence": state["evaluation_state"]["intel_gained"],
        "agentNotes": "Urgency tactics, payment redirection, phishing signals detected"
    }

    try:
        requests.post(
            "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
            json=payload,
            timeout=5
        )
    except Exception:
        pass
