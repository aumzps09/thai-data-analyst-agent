"""Chart tool — bar/line PNG from rows (matplotlib Agg + Pillow RAQM for Thai)."""

from __future__ import annotations

import os
import uuid

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.ticker import FuncFormatter
from matplotlib.transforms import blended_transform_factory
from PIL import Image, ImageDraw, ImageFont

_FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fonts")
_REGULAR = os.path.join(_FONT_DIR, "GoogleSans-Regular.ttf")
_BOLD = os.path.join(_FONT_DIR, "GoogleSans-Bold.ttf")


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = _BOLD if bold else _REGULAR
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def _render_text_rgba(
    text: str,
    size: int,
    bold: bool = False,
    color: tuple[int, int, int, int] = (26, 26, 26, 255),
) -> Image.Image:
    font = _load_font(size, bold)
    bbox = font.getbbox(text)
    w = max(bbox[2] - bbox[0], 1)
    h = max(bbox[3] - bbox[1], 1)
    pad = 2
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=color)
    return img


def _render_text_pt(
    fig: plt.Figure,
    text: str,
    fontsize: int,
    bold: bool = False,
) -> tuple[Image.Image, float]:
    scale = fig.dpi / 72
    px = max(int(round(fontsize * scale)), 1)
    return _render_text_rgba(text, px, bold), 1.0 / scale


def _place_figure_text(
    fig: plt.Figure,
    img: Image.Image,
    x: float,
    y: float,
    zoom: float,
    box_alignment: tuple[float, float] = (0.5, 0.5),
) -> None:
    ab = AnnotationBbox(
        OffsetImage(np.asarray(img), zoom=zoom),
        (x, y),
        xycoords="figure fraction",
        box_alignment=box_alignment,
        frameon=False,
        zorder=10,
    )
    fig.add_artist(ab)


def _place_tick_text(
    ax: plt.Axes,
    img: Image.Image,
    x: float,
    y_axes_frac: float,
    zoom: float,
) -> None:
    trans = blended_transform_factory(ax.transData, ax.transAxes)
    ab = AnnotationBbox(
        OffsetImage(np.asarray(img), zoom=zoom),
        (x, y_axes_frac),
        xycoords=trans,
        box_alignment=(0.5, 1.0),
        frameon=False,
        zorder=10,
    )
    ax.add_artist(ab)


def _chart_title(x_col: str, y_col: str) -> str:
    if y_col == "ยอดขาย" and x_col == "หมวด":
        return "ยอดขายตามหมวดสินค้า"
    if y_col == "ลูกค้า" and x_col == "จังหวัด":
        return "จำนวนลูกค้าตามจังหวัด"
    return f"{y_col} ตาม {x_col}"


def _decorate_thai_text(
    fig: plt.Figure,
    ax: plt.Axes,
    xs: list[str],
    x_col: str,
    y_col: str,
    title: str,
) -> None:
    title_img, title_zoom = _render_text_pt(fig, title, 13, bold=True)
    _place_figure_text(fig, title_img, 0.5, 0.97, title_zoom, box_alignment=(0.5, 1.0))

    xlabel_img, xlabel_zoom = _render_text_pt(fig, x_col, 11)
    _place_figure_text(fig, xlabel_img, 0.5, 0.04, xlabel_zoom, box_alignment=(0.5, 0.0))

    ylabel_img, ylabel_zoom = _render_text_pt(fig, y_col, 11)
    ylabel_img = ylabel_img.rotate(
        90, expand=True, resample=Image.Resampling.BICUBIC, fillcolor=(0, 0, 0, 0)
    )
    _place_figure_text(fig, ylabel_img, 0.07, 0.55, ylabel_zoom, box_alignment=(0.5, 0.5))

    for i, label in enumerate(xs):
        tick_img, tick_zoom = _render_text_pt(fig, label, 10)
        tick_img = tick_img.rotate(
            25, expand=True, resample=Image.Resampling.BICUBIC, fillcolor=(0, 0, 0, 0)
        )
        _place_tick_text(ax, tick_img, i, -0.01, tick_zoom)


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
    if y is None:
        for c in cols[1:]:
            if isinstance(rows[0].get(c), (int, float)):
                y = c
                break
        y = y or cols[-1]

    xs = [str(r.get(x, "")) for r in rows[:20]]
    ys: list[float] = []
    for r in rows[:20]:
        try:
            ys.append(float(r.get(y) or 0))
        except (TypeError, ValueError):
            ys.append(0.0)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    positions = list(range(len(xs)))

    if kind == "line":
        ax.plot(positions, ys, marker="o", color="#2563eb", linewidth=2, markersize=6)
    else:
        bars = ax.bar(positions, ys, color="#2563eb", edgecolor="#1d4ed8", linewidth=0.5)
        for bar, val in zip(bars, ys, strict=True):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:,.0f}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                color="#1a1a1a",
            )

    ax.set_xticks(positions)
    ax.set_xticklabels([])
    ax.set_xlim(-0.6, len(xs) - 0.4)
    ymax = max(ys) if ys else 1
    ax.set_ylim(0, ymax * 1.18)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: f"{v:,.0f}"))
    ax.tick_params(axis="y", labelsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    fig.subplots_adjust(left=0.14, right=0.96, top=0.88, bottom=0.28)

    _decorate_thai_text(fig, ax, xs, x, y, _chart_title(x, y))

    path = os.path.join(out_dir, f"chart_{uuid.uuid4().hex[:8]}.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
