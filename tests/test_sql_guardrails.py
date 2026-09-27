"""Guardrail tests — 10 attack cases must ALL be blocked (plan §8)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from agent.tools.sql_tool import SQLBlockedError, ensure_limit, mask_pii, validate_sql  # noqa: E402

ATTACKS = [
    "DROP TABLE orders",
    "DELETE FROM customers",
    "UPDATE products SET price=0",
    "INSERT INTO orders VALUES (1)",
    "ALTER TABLE orders ADD COLUMN x INT",
    "GRANT ALL ON orders TO PUBLIC",
    "COPY orders TO '/tmp/x.csv'",
    "SELECT * FROM orders; DROP TABLE orders",
    "SELECT * FROM orders -- comment",
    "TRUNCATE orders",
]


@pytest.mark.parametrize("sql", ATTACKS)
def test_attacks_blocked(sql):
    with pytest.raises(SQLBlockedError):
        validate_sql(sql)


def test_select_allowed_and_limit_appended():
    assert ensure_limit("SELECT * FROM orders") == "SELECT * FROM orders LIMIT 100"
    assert ensure_limit("SELECT * FROM orders LIMIT 5") == "SELECT * FROM orders LIMIT 5"


def test_pii_masked():
    rows = mask_pii([{"email": "a@b.com", "phone": "081-234-5678", "city": "ขอนแก่น"}])
    assert rows[0]["email"] == "***@***"
    assert "081" not in rows[0]["phone"]
