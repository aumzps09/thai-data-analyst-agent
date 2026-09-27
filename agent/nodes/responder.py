"""Responder — Thai answer + SQL + sources."""

from __future__ import annotations


def responder_node(state: dict) -> dict:
    if state.get("verdict") == "fail":
        reason = state.get("verdict_reason", "ข้อมูลไม่พอ")
        return {"answer": f"หาคำตอบไม่ได้เพราะ{reason} ลองถามให้เจาะจงขึ้น เช่น ระบุหมวด/ช่วงเดือน ครับ"}
    lines = [state.get("draft", "")]
    if state.get("sql"):
        lines.append(f"\nSQL ที่ใช้:\n```sql\n{state['sql']}\n```")
    sources = []
    for d in state.get("docs") or []:
        if d.get("source") and d["source"] != "mock":
            sources.append(f"- doc: {d['source']}")
    for h in state.get("web_hits") or []:
        if h.get("url"):
            sources.append(f"- web: {h['title']} ({h['url']})")
    if state.get("rows") is not None:
        sources.append(f"- db: {state.get('row_count', len(state['rows']))} แถวจาก PostgreSQL")
    if state.get("chart_path"):
        sources.append(f"- chart: {state['chart_path']}")
    if sources:
        lines.append("\nแหล่งที่มา:\n" + "\n".join(sources))
    return {"answer": "\n".join(lines).strip()}
