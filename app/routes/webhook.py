from fastapi import APIRouter, Header, HTTPException
from app.storage.redis_store import get_state, save_state
from app.agent.state import initialize_state
from app.agent.detector import detect_scam
from app.agent.executor import run_agent
from app.config import settings

router = APIRouter()


@router.post("/webhook/message")
async def receive_message(
    payload: dict,
    x_api_key: str = Header(None)
):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conversation_id = payload.get("conversation_id")
    message = payload.get("message")
    timestamp = payload.get("timestamp")

    if not conversation_id or not message:
        raise HTTPException(status_code=400, detail="Invalid payload")

    state = get_state(conversation_id)
    if not state:
        state = initialize_state(conversation_id)

    # Metrics
    state["metrics"]["turns"] += 1
    if not state["metrics"]["engagement_start"]:
        state["metrics"]["engagement_start"] = timestamp

    # Store message
    state["last_message"] = {"from": "scammer", "content": message}

    # Scam detection
    detection = detect_scam(message)

    # --- CONFIDENCE UPDATE (IMPORTANT FIX) ---
    if detection["confidence"] > 0:
        state["scam_assessment"]["confidence"] = max(
            state["scam_assessment"]["confidence"],
            detection["confidence"]
        )
    else:
        # confidence decay on benign input
        state["scam_assessment"]["confidence"] = max(
            0.0,
            state["scam_assessment"]["confidence"] - 0.1
        )

    state["scam_assessment"]["scam_type"] = detection["scam_type"]

    # Scam detected threshold
    state["scam_assessment"]["scam_detected"] = (
        state["scam_assessment"]["confidence"] >= 0.5
    )

    # Exposure risk
    if detection["signals"]["urgency"]:
        state["risk_state"]["exposure_risk"] += 0.1
    if detection["signals"]["link"]:
        state["risk_state"]["exposure_risk"] += 0.2

    state["risk_state"]["exposure_risk"] = min(
        state["risk_state"]["exposure_risk"], 1.0
    )

    # Stage transition
    if state["scam_assessment"]["scam_detected"]:
        if state["conversation_stage"]["current"] == "passive":
            state["conversation_stage"]["previous"] = "passive"
            state["conversation_stage"]["current"] = "engaged"
            state["conversation_stage"]["stage_entry_turn"] = state["metrics"]["turns"]
    else:
        state["conversation_stage"]["current"] = "passive"

    agent_output = None
    if state["conversation_stage"]["current"] != "passive":
        agent_output = run_agent(state)

    save_state(conversation_id, state)

    return {
        "conversation_id": conversation_id,
        "scam_detected": state["scam_assessment"]["scam_detected"],
        "stage": state["conversation_stage"]["current"],
        "risk": round(state["risk_state"]["exposure_risk"], 2),
        "strategy": agent_output["strategy"] if agent_output else None,
        "agent_reply": agent_output["reply"] if agent_output else None,
        "intel": agent_output["intel_extracted"] if agent_output else None,
        "explanation": agent_output["explanation"] if agent_output else None
    }
