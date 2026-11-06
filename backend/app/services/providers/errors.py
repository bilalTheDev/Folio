"""Map provider HTTP failures to Folio AppErrors without leaking request bodies or tokens."""

import openai

from app.core.errors import AppError

HF_CREDITS = (
    "Your Hugging Face token has no Inference Provider credits. "
    "Add credits, upgrade to PRO, or switch to a native provider key in Settings."
)

_DISPLAY = {
    "groq": "Groq",
    "cerebras": "Cerebras",
    "huggingface": "Hugging Face",
}


def map_provider_error(provider: str, auth_mode: str, exc: Exception) -> AppError:
    status = getattr(exc, "status_code", None)
    name = _DISPLAY.get(provider, provider)
    native = auth_mode == "native"

    if isinstance(exc, openai.AuthenticationError | openai.PermissionDeniedError) or status in (401, 403):
        if native:
            return AppError(502, "provider_auth", f"Your {name} API key was rejected. Check it in Settings.")
        return AppError(502, "provider_auth", "Hugging Face rejected your token. Update it in Settings.")
    if status == 402:
        if native:
            return AppError(
                402,
                "provider_credits",
                f"Your {name} account is out of credits. Add billing in {name}'s console, or pick another provider in Settings.",
            )
        return AppError(402, "provider_credits", HF_CREDITS)
    if isinstance(exc, openai.RateLimitError) or status == 429:
        return AppError(502, "provider_rate_limited", f"{name} is rate limiting your key. Try again shortly.")
    if isinstance(exc, openai.NotFoundError | openai.BadRequestError) or status in (400, 404, 422):
        return AppError(
            502,
            "provider_model_unavailable",
            f"The selected model isn't available on {name}. Pick another in Settings.",
        )
    if isinstance(exc, openai.APITimeoutError) or status in (408, 504):
        return AppError(504, "provider_timeout", f"{name} took too long to answer. Try again.")
    return AppError(502, "provider_error", f"{name} returned an error. Try again, or switch provider in Settings.")
