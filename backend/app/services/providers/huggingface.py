from app.config import settings
from app.services.providers.openai_compat import invoke_chat


def routed_model(provider: str, model: str) -> str:
    return model if provider == "huggingface" else f"{model}:{provider}"


async def chat_completion(
    *, token: str, model: str, provider: str, question: str, history: list[dict], sources: list[dict]
) -> str:
    return await invoke_chat(
        base_url=settings.hf_router_base_url,
        token=token,
        model=routed_model(provider, model),
        question=question,
        history=history,
        sources=sources,
        provider=provider,
        auth_mode="hf_inference_providers",
    )
