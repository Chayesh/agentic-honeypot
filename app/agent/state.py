from datetime import datetime

def initialize_state(conversation_id: str):
    return {
        "conversation_id": conversation_id,
        "created_at": datetime.utcnow().isoformat(),

        "scam_assessment": {
            "scam_detected": False,
            "confidence": 0.0,
            "scam_type": None,
            "scammer_profile": {
                "style": None,
                "aggression_level": 0.0,
                "scripted": False
            }
        },

        "agent_goal": {
            "primary": None,
            "secondary": [],
            "completed": []
        },

        "conversation_stage": {
            "current": "passive",
            "previous": None,
            "stage_entry_turn": 0
        },

        "persona_state": {
            "persona_type": "non_technical_user",
            "tone": "neutral",
            "assertiveness": 0.3,
            "technical_level": 0.2,
            "consistency_tolerance": 0.15
        },

        "memory": {
            "facts": {},
            "commitments": {
                "agent": [],
                "scammer": []
            },
            "behavior": {}
        },

        "strategy_state": {
            "current_strategy": None,
            "next_action": None
        },

        "risk_state": {
            "exposure_risk": 0.0,
            "risk_factors": []
        },

        "evaluation_state": {
            "last_turn_success": None,
            "intel_gained": [],
            "trust_delta": 0.0,
            "risk_delta": 0.0
        },

        "termination_state": {
            "exit_required": False,
            "exit_reason": None,
            "exit_style": None
        },

        "metrics": {
            "turns": 0,
            "engagement_start": None
        }
    }
