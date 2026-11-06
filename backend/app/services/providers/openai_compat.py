"""Shared LangChain ChatOpenAI invoke used by every OpenAI-compatible adapter."""

import logging

import openai
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.config import settings
from app.services.providers.errors import map_provider_error

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

REWRITE_SYSTEM = """Rewrite the user's latest question as a standalone document-search query.
Use chat history only to resolve pronouns, missing entities, and implied topics.
Return only the search query. No quotes and no explanation."""

REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", REWRITE_SYSTEM),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)


def format_context(sources: list[dict]) -> str:
    blocks = []
    for n, source in enumerate(sources, start=1):
        where = f", {source['page_or_section']}" if source.get("page_or_section") else ""
        body = source.get("parent_text") or source["chunk_text"]
        blocks.append(f"[{n}] ({source.get('filename') or 'document'}{where})\n{body}")
    return "\n\n".join(blocks)


def to_history(messages: list[dict]) -> list[BaseMessage]:
    return [
        HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
        for m in messages
    ]


async def invoke_chat(
    *,
    base_url: str,
    token: str,
    model: str,
    question: str,
    history: list[dict],
    sources: list[dict],
    provider: str,
    auth_mode: str,
) -> str:
    chain = PROMPT | _chat_model(base_url=base_url, token=token, model=model) | StrOutputParser()
    try:
        text = await chain.ainvoke(
            {"context": format_context(sources), "history": to_history(history), "question": question}
        )
    except openai.APIError as exc:
        logger.warning(
            "Provider call failed (%s, %s, %s): %s %s",
            provider,
            auth_mode,
            model,
            type(exc).__name__,
            getattr(exc, "status_code", ""),
        )
        raise map_provider_error(provider, auth_mode, exc) from None
    return text.strip()


def _chat_model(*, base_url: str, token: str, model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=token,
        base_url=base_url,
        timeout=settings.llm_timeout_seconds,
        max_retries=1,
        temperature=0.2,
        use_responses_api=False,
    )


async def invoke_rewrite(
    *,
    base_url: str,
    token: str,
    model: str,
    question: str,
    history: list[dict],
    provider: str,
    auth_mode: str,
) -> str:
    chain = REWRITE_PROMPT | _chat_model(base_url=base_url, token=token, model=model) | StrOutputParser()
    try:
        text = await chain.ainvoke({"history": to_history(history), "question": question})
    except openai.APIError as exc:
        logger.warning(
            "Query rewrite failed (%s, %s, %s): %s %s",
            provider,
            auth_mode,
            model,
            type(exc).__name__,
            getattr(exc, "status_code", ""),
        )
        raise map_provider_error(provider, auth_mode, exc) from None
    return " ".join((text or "").split())
