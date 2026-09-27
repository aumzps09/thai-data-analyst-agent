"""Graph tests — 3 main routes pass offline (DB mocked)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["ANALYST_DB_OFFLINE"] = "1"

from agent.graph import build_graph  # noqa: E402


def test_sql_route():
    out = build_graph().invoke({"question": "ยอดขายแต่ละหมวดคือเท่าไหร่", "trace_id": "t1", "retries": 0})
    assert out["plan"] == "sql"
    assert "SELECT" in out["sql"]
    assert out["answer"]


def test_doc_route():
    out = build_graph().invoke({"question": "นโยบายคืนสินค้าคืออะไร", "trace_id": "t2", "retries": 0})
    assert out["plan"] == "doc"
    assert out["answer"]


def test_web_route():
    out = build_graph().invoke({"question": "ข่าวราคาตลาดข้าวหอมมะลิล่าสุด", "trace_id": "t3", "retries": 0})
    assert out["plan"] == "web"
    assert out["answer"]
