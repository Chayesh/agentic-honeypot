from openai import OpenAI, RateLimitError, APIError
from app.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


FALLBACK_REPLIES = {
    "delay": "Okay, I will check this and get back to you.",
    "clarify": "Can you explain what exactly I need to do?",
    "probe": "Is there another way to do this if that doesn’t work?",
    "extract": "Where should the payment be sent?",
    "deescalate": "Sorry, I’m a bit confused right now.",
    "exit": "My app is not working properly. I will try later."
}


def generate_reply(strategy: str, state: dict) -> str:
    """
    Generate a human-like reply using LLM.
    Falls back gracefully if OpenAI is unavailable.
    """

    persona = state["persona_state"]
    last_msg = state["last_message"]["content"]

    system_prompt = (
        "You are a normal, non-technical person chatting on a messaging app. "
        "You are cooperative, slightly confused, and casual. "
        "Never mention AI, automation, security, or policy."
    )

    strategy_prompts = {
        "delay": "Respond politely and say you will check later.",
        "clarify": "Ask one simple question to understand what needs to be done.",
        "probe": "Ask if there is another way in case something does not work.",
        "extract": "Ask where the payment should be sent.",
        "deescalate": "Apologize and say you are confused.",
        "exit": "Explain a technical issue and end the conversation naturally."
    }

    user_prompt = (
        f"Last message:\n{last_msg}\n\n"
        f"Goal:\n{strategy_prompts.get(strategy, 'Respond normally.')}\n\n"
        "Reply in one short message."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=60
        )

        return response.choices[0].message.content.strip()

    except (RateLimitError, APIError, Exception) as e:
        # Graceful fallback — NEVER crash the agent
        return FALLBACK_REPLIES.get(strategy, "Okay.")
