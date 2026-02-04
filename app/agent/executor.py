from app.agent.planner import select_strategy
from app.agent.strategies import Strategy
from app.agent.llm import generate_reply
from app.agent.intelligence import extract_intelligence


def run_agent(state: dict) -> dict:
    strategy = select_strategy(state)
    state["strategy_state"]["current_strategy"] = strategy.value

    explanation = []

    # Explainability hook
    explanation.append(f"stage={state['conversation_stage']['current']}")
    explanation.append(f"risk={state['risk_state']['exposure_risk']}")
    explanation.append(f"turns={state['metrics']['turns']}")

    # Trust-building transition
    if strategy == Strategy.PROBE:
        if state["conversation_stage"]["current"] == "engaged":
            state["conversation_stage"]["previous"] = "engaged"
            state["conversation_stage"]["current"] = "trust_building"
            state["conversation_stage"]["stage_entry_turn"] = state["metrics"]["turns"]
            explanation.append("transitioned_to=trust_building")

    # Exit handling
    if strategy == Strategy.EXIT:
        state["termination_state"]["exit_required"] = True
        state["termination_state"]["exit_style"] = "technical_failure"

    reply = generate_reply(strategy.value, state)

    # Structured intelligence extraction
    intel = extract_intelligence(state["last_message"]["content"], state)
    if intel:
        state["evaluation_state"]["intel_gained"].append(intel)

    return {
        "strategy": strategy.value,
        "reply": reply,
        "explanation": "; ".join(explanation),
        "intel_extracted": intel if intel else None
    }
