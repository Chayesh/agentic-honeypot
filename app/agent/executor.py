import re
from app.agent.llm import generate_reply
from app.agent.callback import send_final_result


URL_REGEX = re.compile(r"https?://\S+")
UPI_REGEX = re.compile(r"\b[\w.-]+@upi\b", re.IGNORECASE)


def run_agent(state: dict) -> dict:
    turns = state["metrics"]["turns"]
    risk = state["risk_state"]["exposure_risk"]

    # ---- STRATEGY SELECTION ----
    if turns <= 2:
        strategy = "trust_building"
    elif risk < 0.5:
        strategy = "clarify"
    else:
        strategy = "extract"

    # ---- GENERATE REPLY ----
    reply = generate_reply(strategy, state)

    # ---- INTEL EXTRACTION ----
    text = state["last_message"]["content"]
    intel = {}

    links = URL_REGEX.findall(text)
    upis = UPI_REGEX.findall(text)

    if links:
        intel["phishing_url"] = links
    if upis:
        intel["upi_id"] = upis

    if intel:
        state["evaluation_state"]["intel_gained"].append(intel)

    # ---- EXIT CONDITION ----
    explanation = f"stage={state['conversation_stage']['current']}; risk={risk}; turns={turns}"

    if risk >= 0.8 or turns >= 15:
        state["termination_state"]["exit_required"] = True
        state["termination_state"]["exit_reason"] = "risk_or_depth"
        send_final_result(state)
        explanation += "; final_callback_sent"

    return {
        "reply": reply,
        "strategy": strategy,
        "intel_extracted": intel,
        "explanation": explanation
    }
