from app.services.providers.openai_compat import invoke_chat

BASE_URL = "https://api.cerebras.ai/v1"


async def chat_completion(*, token: str, model: str, question: str, history: list[dict], sources: list[dict]) -> str:
    return await invoke_chat(
        base_url=BASE_URL,
        token=token,
        model=model,
        question=question,
        history=history,
        sources=sources,
        provider="cerebras",
        auth_mode="native",
    )
