from app.agent.strategies import Strategy
from app.agent.llm import generate_reply
from app.agent.extractor import extract_intel

def select_strategy(state: dict) -> Strategy:
    risk = state["risk_state"]["exposure_risk"]
    intel = state["evaluation_state"]["intel_gained"]
    uses = state["strategy_state"].get("uses", 0)
    current = state["strategy_state"].get("current_strategy")

    # Reset usage if strategy changes
    if current is None:
        state["strategy_state"]["uses"] = 0

    # If we already extracted intel → slow play
    if intel:
        return Strategy.SLOW_PLAY

    # High risk → extraction
    if risk >= 0.5:
        return Strategy.EXTRACTION

    # Rotate if overused
    if uses >= 2:
        if current == Strategy.TRUST_BUILDING:
            return Strategy.VERIFICATION_TRAP
        if current == Strategy.VERIFICATION_TRAP:
            return Strategy.EXTRACTION

    return Strategy.TRUST_BUILDING


def run_agent(state: dict) -> dict:
    strategy = select_strategy(state)

    # Update strategy state
    if state["strategy_state"].get("current_strategy") == strategy:
        state["strategy_state"]["uses"] += 1
    else:
        state["strategy_state"]["current_strategy"] = strategy
        state["strategy_state"]["uses"] = 1

    reply = generate_reply(strategy.value, state)

    # Save reply memory
    state["memory"]["commitments"]["agent"].append(reply)

    # Extract intelligence
    intel = extract_intel(state["last_message"]["content"])
    if intel:
        state["evaluation_state"]["intel_gained"].append(intel)

    explanation = (
        f"stage={state['conversation_stage']['current']}; "
        f"strategy={strategy.value}; "
        f"risk={state['risk_state']['exposure_risk']}; "
        f"turns={state['metrics']['turns']}"
    )

    return {
        "reply": reply,
        "strategy": strategy.value,
        "intel_extracted": intel,
        "explanation": explanation
    }
