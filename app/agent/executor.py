from app.agent.strategies import Strategy
from app.agent.llm import generate_reply
from app.agent.extractor import extract_intel

MAX_TURNS = 8
MAX_INTEL_ITEMS = 2

def select_strategy(state: dict) -> Strategy:
    risk = state["risk_state"]["exposure_risk"]
    intel_items = state["evaluation_state"]["intel_gained"]
    uses = state["strategy_state"].get("uses", 0)
    current = state["strategy_state"].get("current_strategy")

    # Enough intel → slow play
    if len(intel_items) >= MAX_INTEL_ITEMS:
        return Strategy.SLOW_PLAY

    # High risk → extraction
    if risk >= 0.5:
        return Strategy.EXTRACTION

    # Strategy rotation
    if uses >= 2:
        if current == Strategy.TRUST_BUILDING:
            return Strategy.VERIFICATION_TRAP
        if current == Strategy.VERIFICATION_TRAP:
            return Strategy.EXTRACTION

    return Strategy.TRUST_BUILDING


def run_agent(state: dict) -> dict:
    # Engagement cap
    if state["metrics"]["turns"] >= MAX_TURNS:
        state["termination_state"]["exit_required"] = True
        reply = "I’m checking this with my bank app now, please wait."
        state["memory"]["commitments"]["agent"].append(reply)

        return {
            "reply": reply,
            "strategy": "exit",
            "intel_extracted": None,
            "explanation": "exit=turn_limit_reached"
        }

    strategy = select_strategy(state)

    # Update strategy usage
    if state["strategy_state"].get("current_strategy") == strategy:
        state["strategy_state"]["uses"] += 1
    else:
        state["strategy_state"]["current_strategy"] = strategy
        state["strategy_state"]["uses"] = 1

    reply = generate_reply(strategy.value, state)
    state["memory"]["commitments"]["agent"].append(reply)

    # Intel extraction
    intel = extract_intel(state["last_message"]["content"])
    if intel:
        state["evaluation_state"]["intel_gained"].append(intel)

    explanation = (
        f"stage={state['conversation_stage']['current']}; "
        f"strategy={strategy.value}; "
        f"risk={round(state['risk_state']['exposure_risk'],2)}; "
        f"turns={state['metrics']['turns']}"
    )

    return {
        "reply": reply,
        "strategy": strategy.value,
        "intel_extracted": intel,
        "explanation": explanation
    }
