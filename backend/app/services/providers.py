"""Allowlisted inference providers and models, routed through Hugging Face Inference Providers.

The HF router picks the provider from a `<model>:<provider>` suffix; "auto" sends the bare model id
and lets Hugging Face choose.
"""

PROVIDERS = [
    {
        "id": "groq",
        "name": "Groq",
        "description": "LPU inference with very low latency.",
        "models": [
            {"id": "openai/gpt-oss-120b", "label": "GPT-OSS 120B"},
            {"id": "openai/gpt-oss-20b", "label": "GPT-OSS 20B"},
        ],
    },
    {
        "id": "cerebras",
        "name": "Cerebras",
        "description": "Wafer-scale inference with high token throughput.",
        "models": [
            {"id": "openai/gpt-oss-120b", "label": "GPT-OSS 120B"},
            {"id": "Qwen/Qwen3.8-27B", "label": "Qwen 3.8 27B"},
        ],
    },
    {
        "id": "auto",
        "name": "Hugging Face (auto)",
        "description": "Hugging Face routes to an available provider for the model.",
        "models": [
            {"id": "meta-llama/Llama-3.3-70B-Instruct", "label": "Llama 3.3 70B Instruct"},
            {"id": "meta-llama/Llama-3.1-8B-Instruct", "label": "Llama 3.1 8B Instruct"},
            {"id": "Qwen/Qwen2.5-72B-Instruct", "label": "Qwen 2.5 72B Instruct"},
        ],
    },
]

_BY_ID = {p["id"]: p for p in PROVIDERS}


def is_allowed(provider: str, model: str) -> bool:
    entry = _BY_ID.get(provider)
    return entry is not None and any(m["id"] == model for m in entry["models"])


def provider_name(provider: str | None) -> str | None:
    entry = _BY_ID.get(provider or "")
    return entry["name"] if entry else None


def router_model(provider: str, model: str) -> str:
    return model if provider == "auto" else f"{model}:{provider}"
