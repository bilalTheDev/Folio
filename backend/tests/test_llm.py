import httpx
import openai

from app.core.logging import redact
from app.services.providers.errors import map_provider_error


def _status_error(status_code: int, cls=openai.APIStatusError):
    request = httpx.Request("POST", "https://router.huggingface.co/v1/chat/completions")
    response = httpx.Response(status_code, request=request, json={"error": {"message": "provider"}})
    return cls("provider", response=response, body={"error": {"message": "provider"}})


def test_maps_missing_inference_credits():
    error = map_provider_error("huggingface", "hf_inference_providers", _status_error(402))
    assert error.status_code == 402
    assert error.code == "provider_credits"
    assert "native provider key" in error.message.lower() or "credits" in error.message.lower()


def test_maps_native_groq_auth_failure():
    error = map_provider_error("groq", "native", _status_error(401, openai.AuthenticationError))
    assert error.code == "provider_auth"
    assert "Groq API key was rejected" in error.message


def test_maps_auth_and_rate_limit():
    auth = map_provider_error("huggingface", "hf_inference_providers", _status_error(401, openai.AuthenticationError))
    assert auth.code == "provider_auth" and auth.status_code == 502

    limited = map_provider_error("cerebras", "native", _status_error(429, openai.RateLimitError))
    assert limited.code == "provider_rate_limited"


def test_maps_unavailable_model_and_timeout():
    missing = map_provider_error("groq", "native", _status_error(404, openai.NotFoundError))
    assert missing.code == "provider_model_unavailable"

    timeout = map_provider_error(
        "groq", "native", openai.APITimeoutError(request=httpx.Request("POST", "https://example.com"))
    )
    assert timeout.status_code == 504 and timeout.code == "provider_timeout"


def test_generic_provider_failure():
    error = map_provider_error("cerebras", "native", _status_error(503))
    assert error.status_code == 502
    assert error.code == "provider_error"
    assert "Cerebras" in error.message


def test_redacts_native_and_hf_keys():
    assert "gsk_[REDACTED]" in redact("used gsk_abcdefghijklmnopqrstuvwxyz")
    assert "csk_[REDACTED]" in redact("used csk_abcdefghijklmnopqrstuvwxyz")
    assert "hf_[REDACTED]" in redact("used hf_abcdefghijklmnopqrstuvwxyz")
    assert "gsk_abcdefghijklmnopqrstuvwxyz" not in redact("gsk_abcdefghijklmnopqrstuvwxyz")
