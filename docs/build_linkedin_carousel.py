from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import textwrap

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch


@dataclass
class SlideIssue:
    slide: int
    kind: str
    detail: str


BG = "#F8FAFC"
INK = "#0F172A"
MUTED = "#475569"
ACCENT = "#0F766E"
ACCENT_2 = "#2563EB"
ACCENT_3 = "#D97706"


OUTPUT_PDF = Path("docs/LinkedIn_Carousel_Procurement_Spend_Analysis.pdf")
OUTPUT_AUDIT = Path("docs/LinkedIn_Carousel_Audit.txt")


def _intersects(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)


def _in_bounds(box: tuple[float, float, float, float], lo: float = 0.02, hi: float = 0.98) -> bool:
    x0, y0, x1, y1 = box
    return x0 >= lo and y0 >= lo and x1 <= hi and y1 <= hi


def _text_box_axes(fig, ax, txt) -> tuple[float, float, float, float]:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox_disp = txt.get_window_extent(renderer=renderer)
    bbox_axes = bbox_disp.transformed(ax.transAxes.inverted())
    return (bbox_axes.x0, bbox_axes.y0, bbox_axes.x1, bbox_axes.y1)


def _add_card(ax, x: float, y: float, w: float, h: float, face: str = "#FFFFFF") -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            linewidth=1.1,
            edgecolor="#E2E8F0",
            facecolor=face,
            transform=ax.transAxes,
        )
    )


def _wrap(lines: list[str], width: int = 58) -> str:
    wrapped = []
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=width) if line else [""])
    return "\n".join(wrapped)


def _slide_canvas() -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(10, 10), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def _render_slide(
    index: int,
    title: str,
    subtitle: str,
    bullets: list[str],
    footer: str,
    accent: str,
) -> tuple[plt.Figure, list[SlideIssue]]:
    fig, ax = _slide_canvas()
    issues: list[SlideIssue] = []
    boxes: list[tuple[float, float, float, float]] = []

    ax.add_patch(plt.Rectangle((0.06, 0.90), 0.88, 0.012, color=accent, transform=ax.transAxes, linewidth=0))
    ax.add_patch(plt.Rectangle((0.06, 0.085), 0.88, 0.006, color="#E2E8F0", transform=ax.transAxes, linewidth=0))

    card_h = 0.70 if len(bullets) <= 4 else 0.76
    _add_card(ax, 0.06, 0.16, 0.88, card_h)

    t_idx = ax.text(0.06, 0.945, f"Slide {index}/8", fontsize=11, color=MUTED, va="bottom", ha="left", transform=ax.transAxes)
    boxes.append(_text_box_axes(fig, ax, t_idx))

    t_title = ax.text(0.08, 0.855, title, fontsize=28, fontweight="bold", color=INK, va="top", ha="left", transform=ax.transAxes)
    boxes.append(_text_box_axes(fig, ax, t_title))

    t_sub = ax.text(
        0.08,
        0.80,
        _wrap([subtitle], width=58),
        fontsize=13,
        color=MUTED,
        va="top",
        ha="left",
        linespacing=1.45,
        transform=ax.transAxes,
    )
    boxes.append(_text_box_axes(fig, ax, t_sub))

    bullet_text = "\n\n".join([f"• {line}" for line in bullets])
    t_bullets = ax.text(
        0.10,
        0.72,
        _wrap(bullet_text.split("\n"), width=62),
        fontsize=14,
        color=INK,
        va="top",
        ha="left",
        linespacing=1.5,
        transform=ax.transAxes,
    )
    boxes.append(_text_box_axes(fig, ax, t_bullets))

    t_footer = ax.text(
        0.08,
        0.115,
        footer,
        fontsize=11,
        color=MUTED,
        va="bottom",
        ha="left",
        transform=ax.transAxes,
    )
    boxes.append(_text_box_axes(fig, ax, t_footer))

    # Audit checks
    for box in boxes:
        if not _in_bounds(box):
            issues.append(SlideIssue(index, "out_of_bounds", f"Text box out of safe bounds: {box}"))

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if _intersects(boxes[i], boxes[j]):
                issues.append(SlideIssue(index, "overlap", f"Text box {i} overlaps with {j}"))

    total_area = 0.0
    for (x0, y0, x1, y1) in boxes:
        total_area += max(0.0, x1 - x0) * max(0.0, y1 - y0)
    if total_area > 0.40:
        issues.append(SlideIssue(index, "clutter_risk", f"Text density too high: {total_area:.2f}"))

    return fig, issues


def build_carousel() -> list[SlideIssue]:
    slides = [
        {
            "title": "Project Launch",
            "subtitle": "Procurement Spend Analysis and Supplier Optimization for FMCG operations in Nigeria.",
            "bullets": [
                "Analyzed ₦310.4B procurement spend across 24 months, 2,500 orders, and 40 suppliers.",
                "Built an end-to-end analytics pipeline: data generation, SQL model, optimization, and dashboard.",
                "Objective: convert transaction data into ranked, quantified decisions.",
            ],
            "footer": "Live dashboard: procurementspendanalysis.streamlit.app",
            "accent": ACCENT,
        },
        {
            "title": "What Problem Does It Solve?",
            "subtitle": "Most teams can report transactions, but cannot explain where money leaks or what to fix first.",
            "bullets": [
                "Spend visibility gaps across categories and suppliers.",
                "Inconsistent pricing for the same material across teams.",
                "Late-delivery and quality failures hidden from invoice-level reporting.",
                "Maverick buying and FX exposure not quantified for leadership decisions.",
            ],
            "footer": "From record-keeping to decision intelligence.",
            "accent": ACCENT_2,
        },
        {
            "title": "How It Works",
            "subtitle": "Five-layer system from raw files to executive-ready insights.",
            "bullets": [
                "1) Generate realistic procurement data (suppliers, materials, POs, incidents).",
                "2) Load into SQLite and build analytics views.",
                "3) Compute KPIs and savings opportunities in Python + SQL.",
                "4) Run optimization, scenarios, and Monte Carlo uncertainty.",
                "5) Publish outputs in a 5-page Streamlit dashboard.",
            ],
            "footer": "Tech stack: Python, SQL, SQLite, Streamlit, Plotly.",
            "accent": ACCENT,
        },
        {
            "title": "Key Findings",
            "subtitle": "The numbers revealed high-value actions already available in existing data.",
            "bullets": [
                "Total identified savings: ₦185.9B (59.9% of spend).",
                "Price standardization opportunity: ₦18.5B.",
                "Supplier performance opportunity: ₦167.5B.",
                "Maverick spend exposure: ₦40.6B (13.08%).",
                "USD exposure: $132.4M with 99.84% FX volatility.",
            ],
            "footer": "Insight: performance losses outweighed pure price inefficiencies.",
            "accent": ACCENT_3,
        },
        {
            "title": "Decision Logic",
            "subtitle": "Supplier decisions are ranked with a transparent weighted model.",
            "bullets": [
                "Composite score weights: cost 45%, delivery 30%, quality 15%, risk 10%.",
                "Top suppliers are selected per category and assigned recommended share.",
                "Constraints enforce minimum performance and risk thresholds.",
                "Result: lower total cost, better resilience, and clearer governance.",
            ],
            "footer": "Optimization turns strategy into executable sourcing actions.",
            "accent": ACCENT_2,
        },
        {
            "title": "Planning Under Uncertainty",
            "subtitle": "Single-point savings claims are risky. This project includes confidence ranges.",
            "bullets": [
                "Scenario analysis: Conservative, Base, and Aggressive outcomes.",
                "Monte Carlo simulation: 10,000 runs for uncertainty quantification.",
                "Outputs include P05, median, and P95 savings bounds for realistic planning.",
                "Supports CFO-grade budgeting and risk-adjusted target setting.",
            ],
            "footer": "Use median for planning and percentile bounds for contingency.",
            "accent": ACCENT,
        },
        {
            "title": "Decisions You Can Make",
            "subtitle": "Built to drive action across Finance, Procurement, and Operations.",
            "bullets": [
                "Prioritize renegotiation by highest-value categories.",
                "Replace or remediate underperforming suppliers.",
                "Cut maverick spend through stronger vendor governance.",
                "Set FX hedging with quantified USD exposure and volatility.",
            ],
            "footer": "Every recommendation is tied to expected financial impact.",
            "accent": ACCENT_3,
        },
        {
            "title": "Launch and Access",
            "subtitle": "Procurement Spend Analysis is now live and open for review.",
            "bullets": [
                "Live app: procurementspendanalysis.streamlit.app",
                "Code: github.com/DavidMaco/Procurement_Spend_Analysis",
                "Includes dashboard, reports, optimization outputs, and test suite.",
                "Open to feedback from procurement, analytics, and finance leaders.",
            ],
            "footer": "Built by David Igbonaju | Data + Procurement Analytics",
            "accent": ACCENT_2,
        },
    ]

    issues: list[SlideIssue] = []
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(OUTPUT_PDF) as pdf:
        for idx, slide in enumerate(slides, start=1):
            fig, slide_issues = _render_slide(
                index=idx,
                title=slide["title"],
                subtitle=slide["subtitle"],
                bullets=slide["bullets"],
                footer=slide["footer"],
                accent=slide["accent"],
            )
            issues.extend(slide_issues)
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)

    return issues


def write_audit(issues: list[SlideIssue]) -> None:
    lines: list[str] = []
    lines.append("LinkedIn Carousel Audit")
    lines.append("=======================")
    lines.append(f"PDF: {OUTPUT_PDF.as_posix()}")
    lines.append("")

    if not issues:
        lines.append("Status: PASS")
        lines.append("No overlaps, no out-of-bounds elements, and no clutter-risk density flags detected.")
    else:
        lines.append("Status: REVIEW NEEDED")
        lines.append(f"Issues found: {len(issues)}")
        lines.append("")
        for issue in issues:
            lines.append(f"- Slide {issue.slide} | {issue.kind} | {issue.detail}")

    OUTPUT_AUDIT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    detected_issues = build_carousel()
    write_audit(detected_issues)
    if detected_issues:
        print(f"Generated with {len(detected_issues)} audit issue(s). See {OUTPUT_AUDIT.as_posix()}.")
    else:
        print(f"Generated successfully with clean audit. See {OUTPUT_PDF.as_posix()} and {OUTPUT_AUDIT.as_posix()}.")