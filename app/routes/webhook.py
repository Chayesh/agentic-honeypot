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
    # --- AUTH ---
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # --- INPUT NORMALIZATION ---
    session_id = payload.get("sessionId")
    message_obj = payload.get("message", {})
    message_text = message_obj.get("text")
    timestamp = message_obj.get("timestamp")

    if not session_id or not message_text:
        raise HTTPException(status_code=400, detail="Invalid request body")

    # --- STATE ---
    state = get_state(session_id)
    if not state:
        state = initialize_state(session_id)

    state["metrics"]["turns"] += 1
    state["last_message"] = {
        "from": "scammer",
        "content": message_text
    }

    # --- DETECTION ---
    detection = detect_scam(message_text)

    if detection["confidence"] > 0:
        state["scam_assessment"]["confidence"] = max(
            state["scam_assessment"]["confidence"],
            detection["confidence"]
        )
    else:
        state["scam_assessment"]["confidence"] = max(
            0.0,
            state["scam_assessment"]["confidence"] - 0.05
        )

    state["scam_assessment"]["scam_detected"] = (
        state["scam_assessment"]["confidence"] >= 0.5
    )

    # --- STAGE ---
    if state["scam_assessment"]["scam_detected"]:
        state["conversation_stage"]["current"] = "engaged"
    else:
        state["conversation_stage"]["current"] = "passive"

    agent_reply = "Okay."

    if state["conversation_stage"]["current"] == "engaged":
        agent_output = run_agent(state)
        agent_reply = agent_output["reply"]
    else:
        agent_reply = "I’m not fully understanding what you mean."

    save_state(session_id, state)

    # ✅✅ CRITICAL: EXPECTED RESPONSE FORMAT
    return {
        "status": "success",
        "reply": agent_reply
    }
