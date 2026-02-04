from app.agent.strategies import Strategy


def select_strategy(state: dict) -> Strategy:
    risk = state["risk_state"]["exposure_risk"]
    stage = state["conversation_stage"]["current"]
    scam_detected = state["scam_assessment"]["scam_detected"]
    turns = state["metrics"]["turns"]

    # Hard safety exit
    if risk >= 0.8:
        return Strategy.EXIT

    # No scam yet → passive delay
    if not scam_detected:
        return Strategy.DELAY

    # Engaged phase → trust building
    if stage == "engaged":
        if turns <= state["conversation_stage"]["stage_entry_turn"] + 1:
            return Strategy.CLARIFY
        return Strategy.PROBE

    # Trust building → extraction
    if stage == "trust_building":
        return Strategy.EXTRACT

    return Strategy.DELAY
