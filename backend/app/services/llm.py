"""LangChain chain that answers from retrieved context via the Hugging Face Inference Providers router."""

import logging

import openai
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.config import settings
from app.core.errors import AppError
from app.services.providers import router_model

logger = logging.getLogger("folio.llm")

SYSTEM_PROMPT = """You are Folio, an assistant that answers strictly from the user's own documents.

Rules:
- Use only the numbered context passages below. Do not use outside knowledge.
- Cite every claim with the passage number in square brackets, e.g. [1] or [2][3].
- If the passages do not contain the answer, say you couldn't find it in the documents and suggest what to upload or ask instead.
- Be concise. Prefer short paragraphs or bullet points.

Context passages:
{context}"""

PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)


def format_context(sources: list[dict]) -> str:
    blocks = []
    for n, source in enumerate(sources, start=1):
        where = f", {source['page_or_section']}" if source.get("page_or_section") else ""
        blocks.append(f"[{n}] ({source.get('filename') or 'document'}{where})\n{source['chunk_text']}")
    return "\n\n".join(blocks)


def to_history(messages: list[dict]) -> list[BaseMessage]:
    return [
        HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
        for m in messages
    ]


def _provider_error(exc: Exception) -> AppError:
    # Never surface the provider's raw body: it can echo request details.
    if isinstance(exc, openai.AuthenticationError | openai.PermissionDeniedError):
        return AppError(502, "provider_auth", "Hugging Face rejected your token. Update it in Settings.")
    if isinstance(exc, openai.RateLimitError):
        return AppError(502, "provider_rate_limited", "The provider is rate limiting your token. Try again shortly.")
    if isinstance(exc, openai.NotFoundError | openai.BadRequestError):
        return AppError(
            502, "provider_model_unavailable", "The selected model isn't available on this provider. Pick another in Settings."
        )
    if isinstance(exc, openai.APITimeoutError):
        return AppError(504, "provider_timeout", "The provider took too long to answer. Try again.")
    return AppError(502, "provider_error", "The inference provider returned an error. Try again.")


async def answer(
    *, hf_token: str, provider: str, model: str, question: str, history: list[dict], sources: list[dict]
) -> str:
    llm = ChatOpenAI(
        model=router_model(provider, model),
        api_key=hf_token,
        base_url=settings.hf_router_base_url,
        timeout=settings.llm_timeout_seconds,
        max_retries=1,
        temperature=0.2,
    )
    chain = PROMPT | llm | StrOutputParser()
    try:
        text = await chain.ainvoke(
            {"context": format_context(sources), "history": to_history(history), "question": question}
        )
    except openai.APIError as exc:
        logger.warning("Provider call failed (%s, %s): %s", provider, model, type(exc).__name__)
        raise _provider_error(exc) from None
    return text.strip()
