"""Read-only SQL tool with guardrails.

Rules (per plan §6):
- Denylist: DROP, DELETE, UPDATE, INSERT, ALTER, GRANT, COPY (+ TRUNCATE, CREATE)
- Single statement only (no `;` chaining)
- Auto-append LIMIT 100 when missing
- statement_timeout enforced at connection level (10s)
- PII masking before rows reach the LLM
"""

from __future__ import annotations

import os
import re

DENYLIST = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "GRANT", "COPY", "TRUNCATE", "CREATE"]
ROW_LIMIT = 100
STATEMENT_TIMEOUT_MS = 10_000

_PII_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PII_PHONE_TH = re.compile(r"0\d[\d\-\s]{7,12}\d")


class SQLBlockedError(ValueError):
    pass


def validate_sql(sql: str) -> str:
    """Raise SQLBlockedError if forbidden. Returns normalised SQL."""
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        raise SQLBlockedError("SQL ว่างเปล่า")
    upper = cleaned.upper()
    for kw in DENYLIST:
        if re.search(rf"\b{kw}\b", upper):
            raise SQLBlockedError(f"คำสั่ง {kw} ถูกบล็อก (read-only mode)")
    # block stacked statements / comments that smuggle payloads
    if ";" in cleaned:
        raise SQLBlockedError("ไม่อนุญาตหลาย statements ในครั้งเดียว")
    if "--" in cleaned or "/*" in cleaned:
        raise SQLBlockedError("ไม่อนุญาต SQL comments (ป้องกัน smuggling)")
    if not upper.startswith("SELECT") and not upper.startswith("WITH"):
        raise SQLBlockedError("อนุญาตเฉพาะ SELECT / WITH เท่านั้น")
    return cleaned


def ensure_limit(sql: str, limit: int = ROW_LIMIT) -> str:
    """Auto-append LIMIT when the query has none."""
    if re.search(r"\bLIMIT\b\s+\d+", sql, re.IGNORECASE):
        return sql
    return f"{sql.rstrip()} LIMIT {limit}"


def mask_pii(rows: list[dict]) -> list[dict]:
    """Mask email + Thai phone numbers before sending rows to the LLM."""
    masked: list[dict] = []
    for r in rows:
        nr = {}
        for k, v in r.items():
            if isinstance(v, str):
                v = _PII_EMAIL.sub("***@***", v)
                v = _PII_PHONE_TH.sub("0**-***-****", v)
            nr[k] = v
        masked.append(nr)
    return masked


def get_dsn() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://analyst:analyst@localhost:5432/analyst",
    )


def execute_sql(sql: str, *, timeout_ms: int = STATEMENT_TIMEOUT_MS) -> list[dict]:
    """Validate → LIMIT → execute (read-only) → mask PII."""
    import psycopg
    from psycopg.rows import dict_row

    cleaned = ensure_limit(validate_sql(sql))
    with psycopg.connect(get_dsn(), row_factory=dict_row, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET statement_timeout = {timeout_ms}")
            # force read-only transaction as defence in depth
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(cleaned)
            rows = list(cur.fetchall()) if cur.description else []
    return mask_pii(rows)
