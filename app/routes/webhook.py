from fastapi import APIRouter, Header, HTTPException
from uuid import uuid4
from datetime import datetime

from app.storage.redis_store import get_state, save_state
from app.agent.state import initialize_state
from app.agent.detector import detect_scam
from app.agent.executor import run_agent
from app.config import settings

router = APIRouter()


@router.post("/webhook/message")
async def receive_message(payload: dict, x_api_key: str = Header(None)):
    # ------------------ AUTH ------------------
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # ------------------ NORMALIZE INPUT ------------------
    session_id = (
        payload.get("sessionId")
        or payload.get("conversation_id")
        or f"auto-{uuid4()}"
    )

    message_obj = payload.get("message", {})
    message_text = (
        message_obj.get("text")
        if isinstance(message_obj, dict)
        else payload.get("message")
    ) or "[EMPTY_MESSAGE]"

    timestamp = (
        message_obj.get("timestamp")
        if isinstance(message_obj, dict)
        else payload.get("timestamp")
    ) or int(datetime.utcnow().timestamp() * 1000)

    conversation_history = payload.get("conversationHistory", [])
    metadata = payload.get("metadata", {})

    # ------------------ LOAD / INIT STATE ------------------
    state = get_state(session_id)
    if not state:
        state = initialize_state(session_id)

    # ------------------ METRICS ------------------
    state["metrics"]["turns"] += 1
    if not state["metrics"]["engagement_start"]:
        state["metrics"]["engagement_start"] = timestamp

    # ------------------ MEMORY ------------------
    state["last_message"] = {
        "from": "scammer",
        "content": message_text,
        "timestamp": timestamp,
    }

    state["memory"]["history"] = conversation_history
    state["memory"]["metadata"] = metadata

    # ------------------ DETECTION ------------------
    detection = detect_scam(message_text)

    if detection["confidence"] > 0:
        state["scam_assessment"]["confidence"] = max(
            state["scam_assessment"]["confidence"],
            detection["confidence"]
        )
    else:
        state["scam_assessment"]["confidence"] = max(
            0.0,
            state["scam_assessment"]["confidence"] - 0.1
        )

    state["scam_assessment"]["scam_type"] = detection["scam_type"]
    state["scam_assessment"]["scam_detected"] = (
        state["scam_assessment"]["confidence"] >= 0.5
    )

    # ------------------ RISK ------------------
    if detection["signals"]["urgency"]:
        state["risk_state"]["exposure_risk"] += 0.1
    if detection["signals"]["link"]:
        state["risk_state"]["exposure_risk"] += 0.2

    state["risk_state"]["exposure_risk"] = min(
        state["risk_state"]["exposure_risk"], 1.0
    )

    # ------------------ STAGE ------------------
    if state["scam_assessment"]["scam_detected"]:
        if state["conversation_stage"]["current"] == "passive":
            state["conversation_stage"]["previous"] = "passive"
            state["conversation_stage"]["current"] = "engaged"
            state["conversation_stage"]["stage_entry_turn"] = state["metrics"]["turns"]
    else:
        state["conversation_stage"]["current"] = "passive"

    # ------------------ AGENT ------------------
    agent_output = None
    if state["conversation_stage"]["current"] != "passive":
        agent_output = run_agent(state)

    save_state(session_id, state)

    # ------------------ RESPONSE (MATCHES SPEC) ------------------
    return {
        "status": "success",
        "sessionId": session_id,
        "scamDetected": state["scam_assessment"]["scam_detected"],
        "stage": state["conversation_stage"]["current"],
        "risk": round(state["risk_state"]["exposure_risk"], 2),
        "reply": agent_output["reply"] if agent_output else None,
        "strategy": agent_output["strategy"] if agent_output else None,
        "intel": agent_output["intel_extracted"] if agent_output else {},
        "explanation": agent_output["explanation"] if agent_output else "passive_monitoring"
    }
