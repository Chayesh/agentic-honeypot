from openai import OpenAI
from app.config import settings
from app.agent.prompts import STRATEGY_PROMPTS

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_reply(strategy: str, state: dict) -> str:
    system_prompt = STRATEGY_PROMPTS[strategy]

    history = state.get("memory", {}).get("commitments", {}).get("agent", [])
    last_reply = history[-1] if history else ""

    prompt = f"""
{system_prompt}

Previous reply (do NOT repeat):
"{last_reply}"

Latest scammer message:
"{state['last_message']['content']}"

Respond naturally in 1–2 sentences.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt}
            ],
            max_tokens=80,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    except Exception:
        # SAFE FALLBACK (never repeat!)
        fallbacks = {
            "trust_building": "I’m not fully understanding what happened to my account.",
            "verification_trap": "Is there any reference number I can check?",
            "extraction": "Which account are you referring to exactly?",
            "slow_play": "The app is taking time to load, please stay."
        }
        return fallbacks[strategy]
