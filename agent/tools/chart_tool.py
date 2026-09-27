"""Chart tool — bar/line PNG from rows (matplotlib Agg, no display needed)."""

from __future__ import annotations

import os
import uuid

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def render_chart(
    rows: list[dict],
    x: str | None = None,
    y: str | None = None,
    kind: str = "bar",
    out_dir: str = "charts",
) -> str | None:
    if not rows:
        return None
    os.makedirs(out_dir, exist_ok=True)
    cols = list(rows[0].keys())
    x = x or cols[0]
    # pick first numeric col as y
    if y is None:
        for c in cols[1:]:
            if isinstance(rows[0].get(c), (int, float)):
                y = c
                break
        y = y or cols[-1]
    xs = [str(r.get(x, ""))[:20] for r in rows[:20]]
    ys = []
    for r in rows[:20]:
        try:
            ys.append(float(r.get(y) or 0))
        except (TypeError, ValueError):
            ys.append(0.0)

    fig, ax = plt.subplots(figsize=(8, 4))
    if kind == "line":
        ax.plot(xs, ys, marker="o")
    else:
        ax.bar(xs, ys)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    path = os.path.join(out_dir, f"chart_{uuid.uuid4().hex[:8]}.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
