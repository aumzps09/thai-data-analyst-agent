"""Analyst — merge rows + docs + web into draft + optional chart."""

from agent.tools.chart_tool import render_chart


def analyst_node(state: dict) -> dict:
    rows = state.get("rows") or []
    parts = []
    if rows:
        cols = list(rows[0].keys())
        parts.append(f"พบ {len(rows)} แถว (คอลัมน์: {', '.join(cols)})")
        # headline: sum of first numeric col
        for c in cols:
            if isinstance(rows[0].get(c), (int, float)):
                total = sum(float(r.get(c) or 0) for r in rows)
                parts.append(f"รวม {c} = {total:,.0f}")
                break
        preview = "\n".join(str(r) for r in rows[:5])
        parts.append(f"ตัวอย่าง:\n{preview}")
    for d in state.get("docs") or []:
        parts.append(f"เอกสาร: {d.get('text', '')[:300]}")
    for h in state.get("web_hits") or []:
        parts.append(f"เว็บ: {h.get('title')}: {h.get('snippet', '')[:200]}")
    draft = "\n".join(parts) if parts else "ไม่มีข้อมูลจาก tool ใดเลย"
    chart_path = render_chart(rows) if len(rows) >= 2 else None
    out: dict = {"draft": draft}
    if chart_path:
        out["chart_path"] = chart_path
    return out
