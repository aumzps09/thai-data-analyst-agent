"""Shared agent state — single source of truth for the LangGraph."""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    question: str
    lang: str  # "th" | "en"
    plan: str  # router decision: sql | doc | web | mixed
    sql: str
    rows: list[dict[str, Any]]
    row_count: int
    docs: list[dict[str, Any]]
    web_hits: list[dict[str, Any]]
    chart_path: str | None
    draft: str
    verdict: str  # pass | retry | fail
    verdict_reason: str
    answer: str
    trace_id: str
    retries: int
