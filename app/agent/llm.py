from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_reply(strategy: str, state: dict) -> str:
    prompt = f"""
You are a normal, non-technical user.
Do NOT reveal you suspect a scam.

Strategy: {strategy}
Last message: {state['last_message']['content']}

Respond naturally in one short sentence.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=60
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # HARD fallback (mandatory for evaluation)
        return "Can you please explain that again?"
