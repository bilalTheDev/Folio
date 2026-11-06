"""Chat completion entry point used by the chat service."""

import logging

from app.services.providers import complete as _complete
from app.services.providers import complete_rewrite as _complete_rewrite

logger = logging.getLogger("folio.llm")


async def answer(*, token: str, credential: dict, question: str, history: list[dict], sources: list[dict]) -> str:
    return await _complete(
        credential=credential, token=token, question=question, history=history, sources=sources
    )


async def condense_query(*, token: str, credential: dict, question: str, history: list[dict]) -> str:
    if not history:
        return question
    try:
        rewritten = await _complete_rewrite(
            credential=credential, token=token, question=question, history=history
        )
        return rewritten or question
    except Exception:
        logger.exception("Query rewrite failed; searching with the original question")
        return question
