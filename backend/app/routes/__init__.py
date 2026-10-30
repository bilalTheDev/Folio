"""Compatibility shims — prefer backend.app.api for new code."""

from backend.app.api import documents, health, me, providers, sample, threads

__all__ = ["documents", "health", "me", "providers", "sample", "threads"]
