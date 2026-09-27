"""Verifier — 1 retry max, else fail gracefully (never hallucinate)."""

from agent.tools.sql_tool import validate_sql


def verifier_node(state: dict) -> dict:
    retries = state.get("retries", 0)
    if state.get("verdict") == "fail":
        return {"verdict": "fail"}
    sql = state.get("sql", "")
    if state.get("plan") in ("sql", "mixed") and sql:
        try:
            validate_sql(sql)
        except Exception as e:
            if retries < 1:
                return {"verdict": "retry", "verdict_reason": str(e), "retries": retries + 1}
            return {"verdict": "fail", "verdict_reason": str(e)}
    if not any([state.get("rows"), state.get("docs"), state.get("web_hits")]):
        if retries < 1:
            return {"verdict": "retry", "verdict_reason": "ไม่มีข้อมูลจาก tool ใดเลย", "retries": retries + 1}
        return {"verdict": "fail", "verdict_reason": "ไม่มีข้อมูลจาก tool ใดเลย"}
    return {"verdict": "pass"}
