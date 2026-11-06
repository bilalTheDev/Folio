"""Allowlisted providers, credential helpers, and chat dispatch."""

from app.config import settings
from app.core.errors import AppError
from app.services.providers import cerebras, groq, huggingface
from app.services.providers.openai_compat import invoke_rewrite

HF_DOCS = "https://huggingface.co/settings/tokens"
HF_MODE = {
    "id": "hf_inference_providers",
    "label": "Use via Hugging Face Inference Providers",
    "hint": "Requires Hugging Face Inference Provider credits.",
    "token_prefix": "hf_",
    "docs_url": HF_DOCS,
}

GROQ_HF_MODELS = [
    {"id": "openai/gpt-oss-120b", "label": "GPT-OSS 120B"},
    {"id": "openai/gpt-oss-20b", "label": "GPT-OSS 20B"},
]
CEREBRAS_HF_MODELS = [
    {"id": "openai/gpt-oss-120b", "label": "GPT-OSS 120B"},
    {"id": "Qwen/Qwen3.8-27B", "label": "Qwen 3.8 27B"},
]

PROVIDERS = [
    {
        "id": "groq",
        "name": "Groq",
        "description": "LPU inference with very low latency.",
        "auth_modes": [
            {
                "id": "native",
                "label": "Use my Groq API key directly",
                "hint": "Free tier available on Groq.",
                "token_prefix": "gsk_",
                "docs_url": "https://console.groq.com/keys",
                "models": [
                    {"id": "openai/gpt-oss-120b", "label": "GPT-OSS 120B"},
                    {"id": "openai/gpt-oss-20b", "label": "GPT-OSS 20B"},
                ],
            },
            {**HF_MODE, "models": GROQ_HF_MODELS},
        ],
    },
    {
        "id": "cerebras",
        "name": "Cerebras",
        "description": "Wafer-scale inference with high token throughput.",
        "auth_modes": [
            {
                "id": "native",
                "label": "Use my Cerebras API key directly",
                "hint": "Free trial available on Cerebras.",
                "token_prefix": "csk_",
                "docs_url": "https://cloud.cerebras.ai",
                "models": [
                    {"id": "gpt-oss-120b", "label": "GPT-OSS 120B"},
                    {"id": "qwen-3.8-27b", "label": "Qwen 3.8 27B"},
                ],
            },
            {**HF_MODE, "models": CEREBRAS_HF_MODELS},
        ],
    },
    {
        "id": "huggingface",
        "name": "Hugging Face",
        "description": "Hugging Face routes to an available provider for the model.",
        "auth_modes": [
            {
                **HF_MODE,
                "models": [
                    {"id": "meta-llama/Llama-3.3-70B-Instruct", "label": "Llama 3.3 70B Instruct"},
                    {"id": "meta-llama/Llama-3.1-8B-Instruct", "label": "Llama 3.1 8B Instruct"},
                    {"id": "Qwen/Qwen2.5-72B-Instruct", "label": "Qwen 2.5 72B Instruct"},
                ],
            }
        ],
    },
]

_BY_ID = {p["id"]: p for p in PROVIDERS}

AUTH_MODES = ("native", "hf_inference_providers")


def provider_entry(provider: str) -> dict | None:
    return _BY_ID.get(provider)


def auth_mode_entry(provider: str, auth_mode: str) -> dict | None:
    entry = _BY_ID.get(provider)
    if not entry:
        return None
    return next((m for m in entry["auth_modes"] if m["id"] == auth_mode), None)


def is_allowed(provider: str, auth_mode: str, model: str) -> bool:
    mode = auth_mode_entry(provider, auth_mode)
    return mode is not None and any(m["id"] == model for m in mode["models"])


def expected_prefix(provider: str, auth_mode: str) -> str:
    mode = auth_mode_entry(provider, auth_mode)
    return (mode or {}).get("token_prefix") or ""


def provider_name(provider: str | None) -> str | None:
    entry = _BY_ID.get(provider or "")
    return entry["name"] if entry else None


def active_credential(user: dict) -> dict | None:
    creds = user.get("credentials") or []
    for cred in creds:
        if cred.get("is_active"):
            return cred
    return None


def is_complete(cred: dict | None) -> bool:
    return bool(
        cred
        and cred.get("token_encrypted")
        and cred.get("provider")
        and cred.get("model")
        and cred.get("auth_mode")
    )


async def complete(
    *, credential: dict, token: str, question: str, history: list[dict], sources: list[dict]
) -> str:
    provider = credential["provider"]
    auth_mode = credential["auth_mode"]
    model = credential["model"]
    if not is_allowed(provider, auth_mode, model):
        raise AppError(409, "missing_provider", "Choose a provider and model in Settings first.")
    if auth_mode == "hf_inference_providers":
        return await huggingface.chat_completion(
            token=token, model=model, provider=provider, question=question, history=history, sources=sources
        )
    if provider == "groq":
        return await groq.chat_completion(token=token, model=model, question=question, history=history, sources=sources)
    if provider == "cerebras":
        return await cerebras.chat_completion(
            token=token, model=model, question=question, history=history, sources=sources
        )
    raise AppError(422, "invalid_provider", "That provider isn't supported.")


async def complete_rewrite(*, credential: dict, token: str, question: str, history: list[dict]) -> str:
    provider = credential["provider"]
    auth_mode = credential["auth_mode"]
    model = credential["model"]
    if not is_allowed(provider, auth_mode, model):
        raise AppError(409, "missing_provider", "Choose a provider and model in Settings first.")
    if auth_mode == "hf_inference_providers":
        return await invoke_rewrite(
            base_url=settings.hf_router_base_url,
            token=token,
            model=huggingface.routed_model(provider, model),
            question=question,
            history=history,
            provider=provider,
            auth_mode=auth_mode,
        )
    if provider == "groq":
        return await invoke_rewrite(
            base_url=groq.BASE_URL,
            token=token,
            model=model,
            question=question,
            history=history,
            provider=provider,
            auth_mode=auth_mode,
        )
    if provider == "cerebras":
        return await invoke_rewrite(
            base_url=cerebras.BASE_URL,
            token=token,
            model=model,
            question=question,
            history=history,
            provider=provider,
            auth_mode=auth_mode,
        )
    raise AppError(422, "invalid_provider", "That provider isn't supported.")
