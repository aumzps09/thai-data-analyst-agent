"""LangGraph assembly: router → (sql|doc|web|mixed) → analyst → verifier → responder."""

from __future__ import annotations

import uuid

from langgraph.graph import END, StateGraph

from agent.nodes.analyst import analyst_node
from agent.nodes.doc_agent import doc_agent_node
from agent.nodes.responder import responder_node
from agent.nodes.router import router_node
from agent.nodes.sql_agent import sql_agent_node
from agent.nodes.verifier import verifier_node
from agent.nodes.web_agent import web_agent_node
from agent.state import AgentState


def _route(state: AgentState) -> str:
    return state.get("plan", "sql")


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("router", router_node)
    g.add_node("sql_agent", sql_agent_node)
    g.add_node("doc_agent", doc_agent_node)
    g.add_node("web_agent", web_agent_node)
    g.add_node("analyst", analyst_node)
    g.add_node("verifier", verifier_node)
    g.add_node("responder", responder_node)

    g.set_entry_point("router")
    g.add_conditional_edges(
        "router",
        _route,
        {"sql": "sql_agent", "doc": "doc_agent", "web": "web_agent", "mixed": "sql_agent"},
    )
    # mixed fans out sequentially (sql → doc → web) for simplicity/traceability
    g.add_edge("sql_agent", "analyst")
    g.add_edge("doc_agent", "analyst")
    g.add_edge("web_agent", "analyst")
    g.add_edge("analyst", "verifier")
    g.add_conditional_edges(
        "verifier",
        lambda s: "retry" if s.get("verdict") == "retry" else "done",
        {"retry": "router", "done": "responder"},
    )
    g.add_edge("responder", END)
    return g.compile()


def ask(question: str) -> dict:
    app = build_graph()
    init: AgentState = {"question": question, "trace_id": uuid.uuid4().hex[:8], "retries": 0}
    return app.invoke(init)
