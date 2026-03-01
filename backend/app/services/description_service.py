import logging
from app.config import settings

logger = logging.getLogger(__name__)


def generate_description(
    merchant_name: str,
    amount: float,
    rail: str,
    user_provided: str | None = None,
) -> str:
    if user_provided:
        return user_provided

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=60,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Generate a brief (10-15 word) realistic transaction description "
                        f"for a ${amount:.2f} payment to {merchant_name} via {rail}. "
                        f"Be specific to the merchant type. Reply with only the description, no quotes."
                    ),
                }
            ],
        )
        return message.content[0].text.strip()
    except Exception as e:
        logger.warning("description_service: Claude API call failed: %s", e)
        return f"Payment to {merchant_name} via {rail.upper()}"
