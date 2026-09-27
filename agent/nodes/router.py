"""Router — rule-based Thai classifier (offline-safe) with optional LLM override."""

from __future__ import annotations

import os
import re

SQL_PAT = re.compile(r"ยอดขาย|รายได้|top|อันดับ|เท่าไหร่|กี่|เดือน|ปี|หมวด|เทียบยอด|แนวโน้ม|ขายดี", re.I)
DOC_PAT = re.compile(r"นโยบาย|ระเบียบ|เอกสาร|คืออะไร|หมายถึง|วิธี|ขั้นตอน|คู่มือ|ประกาศ", re.I)
WEB_PAT = re.compile(r"ข่าว|ราคาตลาด|อัตรา|ค่าเงิน|หุ้น|สภาพอากาศ|ล่าสุด.*ข่าว|เว็บ", re.I)


def classify(question: str) -> str:
    q = question.strip()
    s, d, w = bool(SQL_PAT.search(q)), bool(DOC_PAT.search(q)), bool(WEB_PAT.search(q))
    hits = sum([s, d, w])
    if hits >= 2 or ("เทียบ" in q and s):
        return "mixed"
    if s:
        return "sql"
    if d:
        return "doc"
    if w:
        return "web"
    # default: numbers intent → sql, else doc
    return "sql" if re.search(r"\d|ขาย|สั่ง|ลูกค้า|order|sql", q, re.I) else "doc"


def router_node(state: dict) -> dict:
    """LangGraph node. Uses LLM only when explicitly enabled."""
    if os.getenv("ROUTER_LLM", "0") == "1":
        try:
            return {"plan": _llm_classify(state["question"])}
        except Exception:
            pass
    return {"plan": classify(state.get("question", "")), "lang": "th"}


def _llm_classify(question: str) -> str:
    # Optional: Gemini/OpenAI override — kept lazy so base install stays light.
    from langchain_core.prompts import ChatPromptTemplate

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    except ImportError:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    prompt = ChatPromptTemplate.from_messages(
        [("system", "จำแนกเป็น sql|doc|web|mixed ตอบแค่คำเดียว"), ("user", question)]
    )
    out = (prompt | llm).invoke({}).content.strip().lower()
    return out if out in {"sql", "doc", "web", "mixed"} else classify(question)
