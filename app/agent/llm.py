from openai import OpenAI
from app.config import settings
from app.agent.prompts import STRATEGY_PROMPTS

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_reply(strategy: str, state: dict) -> str:
    system_prompt = STRATEGY_PROMPTS[strategy]

    previous_replies = state["memory"]["commitments"]["agent"]
    last_reply = previous_replies[-1] if previous_replies else ""

    prompt = f"""
{system_prompt}

IMPORTANT RULES:
- Never repeat the same sentence.
- Sound human, slightly confused or stressed.
- Do NOT accuse or reveal scam detection.
- Keep replies short (1–2 sentences).

Previous reply (do NOT repeat):
"{last_reply}"

Latest scammer message:
"{state['last_message']['content']}"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=80
        )
        reply = response.choices[0].message.content.strip()

    except Exception:
        fallback = {
            "trust_building": "I’m a bit confused about what’s going on with my account.",
            "verification_trap": "Is there some reference number I can verify?",
            "extraction": "Which account is this related to exactly?",
            "slow_play": "The app is loading slowly, please wait."
        }
        reply = fallback[strategy]

    # HARD STOP: prevent repetition
    if previous_replies and reply.strip() == previous_replies[-1].strip():
        reply = "I’m trying to check this on my phone, please hold on."

    return reply
