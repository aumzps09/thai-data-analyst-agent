"""Web search tool — Tavily primary, Brave fallback, mock offline."""

from __future__ import annotations

import os


def search(query: str, max_results: int = 5) -> list[dict]:
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=tavily_key)
            res = client.search(query, max_results=max_results, search_depth="basic")
            return [
                {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")[:500]}
                for r in res.get("results", [])
            ]
        except Exception:
            pass
    brave_key = os.getenv("BRAVE_API_KEY")
    if brave_key:
        try:
            import httpx

            r = httpx.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": brave_key},
                params={"q": query, "count": max_results},
                timeout=10,
            )
            r.raise_for_status()
            return [
                {"title": it.get("title", ""), "url": it.get("url", ""), "snippet": it.get("description", "")[:500]}
                for it in r.json().get("web", {}).get("results", [])
            ]
        except Exception:
            pass
    # offline fallback so graph/evals still run
    return [{"title": f"(mock) {query}", "url": "", "snippet": "ตั้งค่า TAVILY_API_KEY เพื่อเปิด web search จริง"}]
