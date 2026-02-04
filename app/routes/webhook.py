from fastapi import APIRouter, Header, HTTPException
from app.storage.redis_store import get_state, save_state
from app.agent.state import initialize_state
from app.agent.detector import detect_scam
from app.agent.executor import run_agent
from app.config import settings
import time

router = APIRouter()


@router.post("/webhook/message")
async def receive_message(
    payload: dict,
    x_api_key: str = Header(None)
):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # -----------------------------
    # 🔁 BACKWARD-COMPATIBLE PARSING
    # -----------------------------

    # session / conversation id
    session_id = (
        payload.get("sessionId")
        or payload.get("conversation_id")
        or "tester-session"
    )

    raw_message = payload.get("message")

    # Case 1: message is already structured
    if isinstance(raw_message, dict):
        message_text = raw_message.get("text", "")
        timestamp = raw_message.get("timestamp", int(time.time() * 1000))
    # Case 2: message is plain string (GUVI tester)
    elif isinstance(raw_message, str):
        message_text = raw_message
        timestamp = int(time.time() * 1000)
    else:
        raise HTTPException(status_code=400, detail="INVALID_REQUEST_BODY")

    if not message_text:
        raise HTTPException(status_code=400, detail="INVALID_REQUEST_BODY")

    # -----------------------------
    # 🔁 STATE HANDLING
    # -----------------------------

    state = get_state(session_id)
    if not state:
        state = initialize_state(session_id)

    state["metrics"]["turns"] += 1
    if not state["metrics"]["engagement_start"]:
        state["metrics"]["engagement_start"] = timestamp

    state["last_message"] = {
        "from": "scammer",
        "content": message_text
    }

    # -----------------------------
    # 🔍 SCAM DETECTION
    # -----------------------------

    detection = detect_scam(message_text)

    state["scam_assessment"]["confidence"] = max(
        state["scam_assessment"]["confidence"],
        detection["confidence"]
    )

    state["scam_assessment"]["scam_type"] = detection["scam_type"]
    state["scam_assessment"]["scam_detected"] = (
        state["scam_assessment"]["confidence"] >= 0.5
    )

    # risk modeling
    if detection["signals"].get("urgency"):
        state["risk_state"]["exposure_risk"] += 0.1
    if detection["signals"].get("link"):
        state["risk_state"]["exposure_risk"] += 0.2
    if detection["signals"].get("upi"):
        state["risk_state"]["exposure_risk"] += 0.2

    state["risk_state"]["exposure_risk"] = min(
        state["risk_state"]["exposure_risk"], 1.0
    )

    # -----------------------------
    # 🎭 STAGE TRANSITION
    # -----------------------------

    if state["scam_assessment"]["scam_detected"]:
        if state["conversation_stage"]["current"] == "passive":
            state["conversation_stage"]["current"] = "engaged"
            state["conversation_stage"]["stage_entry_turn"] = state["metrics"]["turns"]
    else:
        state["conversation_stage"]["current"] = "passive"

    # -----------------------------
    # 🤖 AGENT EXECUTION
    # -----------------------------

    agent_output = None
    if state["conversation_stage"]["current"] != "passive":
        agent_output = run_agent(state)

    save_state(session_id, state)

    # -----------------------------
    # ✅ RESPONSE (TESTER FRIENDLY)
    # -----------------------------

    return {
        "status": "success",
        "sessionId": session_id,
        "scamDetected": state["scam_assessment"]["scam_detected"],
        "stage": state["conversation_stage"]["current"],
        "risk": round(state["risk_state"]["exposure_risk"], 2),
        "reply": agent_output["reply"] if agent_output else "",
        "strategy": agent_output["strategy"] if agent_output else "",
        "intel": agent_output["intel_extracted"] if agent_output else {},
        "explanation": agent_output["explanation"] if agent_output else "passive_monitoring"
    }
