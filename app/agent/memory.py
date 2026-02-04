def add_fact(state, key, value):
    state["memory"]["facts"][key] = value

def add_commitment(state, who, commitment):
    state["memory"]["commitments"][who].append(commitment)

def record_behavior(state, key, value):
    state["memory"]["behavior"][key] = value
