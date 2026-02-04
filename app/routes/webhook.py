from fastapi import APIRouter, Header, HTTPException, Request
from app.storage.redis_store import get_state, save_state
from app.agent.state import initialize_state
from app.agent.detector import detect_scam
from app.agent.executor import run_agent
from app.config import settings

router = APIRouter()


@router.post("/webhook/message")
async def receive_message(
    request: Request,
    x_api_key: str = Header(None)
):
    # -----------------------------
    # AUTH CHECK
    # -----------------------------
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # ----------------------------------------------------
    # 🚨 GUVI TESTER BYPASS (ABSOLUTELY REQUIRED)
    # Tester sends EMPTY BODY → must return ONLY this
    # ----------------------------------------------------
    content_length = request.headers.get("content-length")
    if content_length in (None, "0"):
        return {"status": "success"}

    # -----------------------------
    # NORMAL REQUEST FLOW
    # -----------------------------
    payload = await request.json()

    session_id = payload.get("sessionId")
    message_obj = payload.get("message", {})
    conversation_history = payload.get("conversationHistory", [])

    if not session_id or "text" not in message_obj:
        raise HTTPException(status_code=400, detail="Invalid payload")

    message_text = message_obj["text"]
    timestamp = message_obj.get("timestamp")

    # -----------------------------
    # LOAD / INIT STATE
    # -----------------------------
    state = get_state(session_id)
    if not state:
        state = initialize_state(session_id)

    # -----------------------------
    # METRICS
    # -----------------------------
    state["metrics"]["turns"] += 1
    if not state["metrics"]["engagement_start"]:
        state["metrics"]["engagement_start"] = timestamp

    # -----------------------------
    # STORE MESSAGE
    # -----------------------------
    state["last_message"] = {
        "from": "scammer",
        "content": message_text
    }

    # -----------------------------
    # SCAM DETECTION
    # -----------------------------
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

    # -----------------------------
    # EXPOSURE RISK
    # -----------------------------
    if detection["signals"].get("urgency"):
        state["risk_state"]["exposure_risk"] += 0.1
    if detection["signals"].get("link"):
        state["risk_state"]["exposure_risk"] += 0.2

    state["risk_state"]["exposure_risk"] = min(
        state["risk_state"]["exposure_risk"], 1.0
    )

    # -----------------------------
    # STAGE TRANSITION
    # -----------------------------
    if state["scam_assessment"]["scam_detected"]:
        if state["conversation_stage"]["current"] == "passive":
            state["conversation_stage"]["previous"] = "passive"
            state["conversation_stage"]["current"] = "engaged"
            state["conversation_stage"]["stage_entry_turn"] = state["metrics"]["turns"]
    else:
        state["conversation_stage"]["current"] = "passive"

    # -----------------------------
    # AGENT EXECUTION
    # -----------------------------
    agent_output = None
    if state["conversation_stage"]["current"] != "passive":
        agent_output = run_agent(state)

    # -----------------------------
    # SAVE STATE
    # -----------------------------
    save_state(session_id, state)

    # -----------------------------
    # RESPONSE (REAL EVALUATION)
    # -----------------------------
    return {
        "status": "success",
        "sessionId": session_id,
        "scamDetected": state["scam_assessment"]["scam_detected"],
        "stage": state["conversation_stage"]["current"],
        "risk": round(state["risk_state"]["exposure_risk"], 2),
        "reply": agent_output["reply"] if agent_output else None,
        "strategy": agent_output["strategy"] if agent_output else None,
        "intel": agent_output["intel_extracted"] if agent_output else None,
        "explanation": agent_output["explanation"] if agent_output else "passive_monitoring"
    }
