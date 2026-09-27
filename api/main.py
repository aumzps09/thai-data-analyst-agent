"""FastAPI + SSE streaming: thinking → sql → rows(n) → chart → answer."""

from __future__ import annotations

import json
import os
import uuid

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from agent.graph import build_graph
from api.schemas import AskRequest

app = FastAPI(title="Thai Data Analyst Agent", version="0.1.0")
_traces: dict[str, dict] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/trace/{trace_id}")
def get_trace(trace_id: str):
    t = _traces.get(trace_id)
    if not t:
        return JSONResponse({"error": "trace not found"}, status_code=404)
    ls = os.getenv("LANGSMITH_PROJECT")
    if ls:
        t = {**t, "langsmith_url": f"https://smith.langchain.com (project={ls})"}
    return t


@app.post("/v1/ask")
async def ask(req: AskRequest):
    trace_id = uuid.uuid4().hex[:8]
    graph = build_graph()
    init = {"question": req.question_th, "trace_id": trace_id, "retries": 0}

    async def gen():
        yield {"event": "thinking", "data": json.dumps({"trace_id": trace_id}, ensure_ascii=False)}
        final: dict = {}
        for chunk in graph.stream(init, stream_mode="updates"):
            for node, out in chunk.items():
                final.update(out or {})
                if node == "router" and out.get("plan"):
                    yield {"event": "plan", "data": json.dumps(out, ensure_ascii=False, default=str)}
                if node == "sql_agent" and out.get("sql"):
                    yield {"event": "sql", "data": json.dumps({"sql": out["sql"]}, ensure_ascii=False)}
                    if out.get("row_count") is not None:
                        yield {"event": "rows", "data": json.dumps({"n": out["row_count"]}, ensure_ascii=False)}
                if node == "analyst" and out.get("chart_path"):
                    yield {"event": "chart", "data": json.dumps({"chart_url": out["chart_path"]}, ensure_ascii=False)}
        answer = final.get("answer", "")
        _traces[trace_id] = {"trace_id": trace_id, **final, "question": req.question_th}
        yield {"event": "answer", "data": json.dumps({"answer": answer, "trace_id": trace_id}, ensure_ascii=False)}

    return EventSourceResponse(gen())
