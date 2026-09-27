"""Web agent — search + summarize hook."""

from agent.tools.search_tool import search


def web_agent_node(state: dict) -> dict:
    hits = search(state.get("question", ""))
    return {"web_hits": hits}
