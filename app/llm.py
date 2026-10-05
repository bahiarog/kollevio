import os
import logging

logger = logging.getLogger(__name__)

MODEL_ID = "claude-sonnet-5"
FALLBACK_MESSAGE = (
    "Dieser digitale Mitarbeiter ist eingestellt, aber noch nicht aktiviert — "
    "ein API-Schlüssel muss hinterlegt werden."
)


async def get_agent_reply(system_prompt: str, history: list[dict], user_message: str) -> str:
    """Call the Anthropic Messages API. Returns a graceful fallback string if
    no API key is configured or the call fails, so the chat endpoint never
    crashes for lack of a key."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return FALLBACK_MESSAGE

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=api_key)
        messages = []
        for m in history:
            role = "assistant" if m["sender"] == "agent" else "user"
            messages.append({"role": role, "content": m["content"]})
        messages.append({"role": "user", "content": user_message})

        response = await client.messages.create(
            model=MODEL_ID,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
        return "\n".join(parts).strip() or FALLBACK_MESSAGE
    except Exception:
        logger.exception("LLM call failed")
        return (
            "Entschuldigung, bei der Verarbeitung ist ein technisches Problem aufgetreten. "
            "Bitte versuchen Sie es in Kürze erneut."
        )
