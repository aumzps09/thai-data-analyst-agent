"""SQL agent — template Text2SQL (offline) + optional LLM + guarded execution."""

from __future__ import annotations

import os
import re

from agent.tools.sql_tool import SQLBlockedError, execute_sql

# --- template layer: covers golden questions without an LLM call ---


def draft_sql(question: str) -> str:
    q = question
    # top categories
    m = re.search(r"top\s*(\d+)", q, re.I)
    if "หมวด" in q and ("ขายดี" in q or m):
        n = m.group(1) if m else "5"
        return (
            "SELECT p.category_th AS หมวด, SUM(oi.qty * p.price) AS ยอดขาย "
            "FROM order_items oi JOIN products p ON p.id = oi.product_id "
            f"GROUP BY 1 ORDER BY 2 DESC LIMIT {n}"
        )
    if "เดือนที่แล้ว" in q or ("ยอดขาย" in q and "เดือน" in q):
        return (
            "SELECT date_trunc('month', o.order_date)::date AS เดือน, "
            "SUM(oi.qty * p.price) AS ยอดขาย FROM orders o "
            "JOIN order_items oi ON oi.order_id = o.id "
            "JOIN products p ON p.id = oi.product_id "
            "WHERE o.order_date >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month') "
            "AND o.order_date < date_trunc('month', CURRENT_DATE) "
            "GROUP BY 1 ORDER BY 1 LIMIT 100"
        )
    if "ยอดขาย" in q:
        return (
            "SELECT p.category_th AS หมวด, SUM(oi.qty * p.price) AS ยอดขาย "
            "FROM order_items oi JOIN products p ON p.id = oi.product_id "
            "JOIN orders o ON o.id = oi.order_id "
            "GROUP BY 1 ORDER BY 2 DESC LIMIT 100"
        )
    if re.search(r"ลูกค้า.*(เยอะ|มาก|top|อันดับ)|จังหวัด|city", q, re.I):
        return (
            "SELECT c.city AS จังหวัด, COUNT(DISTINCT c.id) AS ลูกค้า, COUNT(o.id) AS ออเดอร์ "
            "FROM customers c LEFT JOIN orders o ON o.customer_id = c.id "
            "GROUP BY 1 ORDER BY 2 DESC LIMIT 100"
        )
    if "นโยบาย" in q:
        return "SELECT id, title, LEFT(detail, 300) AS สรุป FROM policies ORDER BY updated_at DESC LIMIT 100"
    # safe generic fallback (never writes)
    return "SELECT p.category_th AS หมวด, COUNT(*) AS รายการ FROM products p GROUP BY 1 ORDER BY 2 DESC LIMIT 100"


def _llm_sql(question: str) -> str:
    from langchain_core.prompts import ChatPromptTemplate

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    except ImportError:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    prompt = ChatPromptTemplate.from_messages(
        [("system", open("agent/prompts.yaml", encoding="utf-8").read()), ("user", question)]
    )
    return (prompt | llm).invoke({}).content.strip().strip("`")


def sql_agent_node(state: dict) -> dict:
    q = state.get("question", "")
    sql = _llm_sql(q) if os.getenv("SQL_LLM", "0") == "1" else draft_sql(q)
    try:
        if os.getenv("ANALYST_DB_OFFLINE", "0") == "1":
            raise RuntimeError("offline")
        rows = execute_sql(sql)
    except SQLBlockedError as e:
        return {"sql": sql, "rows": [], "row_count": 0, "verdict": "fail", "verdict_reason": str(e)}
    except Exception as e:  # DB down in dev → keep graph testable
        return {"sql": sql, "rows": [], "row_count": 0, "draft": f"(DB จำลอง: {e})"}
    return {"sql": sql, "rows": rows, "row_count": len(rows)}
