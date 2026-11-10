"""Charts. Same look as the other two projects: validated blue / orange / aqua slots, thin marks, 2px surface gaps,
recessive grid and direct labels."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .economics import LINES

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"


def _ax(figsize=(8.2, 4.8), grid="x"):
    fig, ax = plt.subplots(figsize=figsize, dpi=160)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.grid(axis=grid, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    return fig, ax


def _title(ax, title, sub):
    ax.set_title(title, loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=30)
    ax.text(0, 1.035, sub, transform=ax.transAxes, fontsize=9, color=INK2, va="bottom")


def _save(fig, out, name):
    fig.tight_layout()
    fig.savefig(Path(out) / name, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def fig_waterfall(out, po, aov):
    labels = dict(LINES)
    labels.update(variable_contribution="Contribution before store costs", store_fixed="Store rent and staff",
                  contribution="Contribution", central="Central costs (tech, corporate)", adj_ebitda="Adjusted EBITDA")
    order = [k for k, _ in LINES] + ["variable_contribution", "store_fixed", "contribution", "central", "adj_ebitda"]
    totals = {"variable_contribution", "contribution", "adj_ebitda"}
    fig, ax = _ax((8.6, 5.6), "x")
    y = np.arange(len(order))[::-1]
    run = 0.0
    for yi, k in zip(y, order):
        v = po[k]
        if k in totals:
            left, width, color = 0.0, v, INK2
            run = v
        else:
            left, width = run, v
            color = BLUE if v >= 0 else ORANGE
            run += v
        ax.barh(yi, width, left=left, height=0.56, color=color, edgecolor=SURFACE, linewidth=1.6, zorder=3)
        end = max(left, left + width)
        ax.text(end + 2.5, yi, f"{v:+.1f}" if k not in totals else f"{v:.1f}  ({100 * v / aov:.1f}% of order value)", va="center",
                fontsize=9, color=INK, fontweight="bold" if k in totals else "normal")
    ax.set_yticks(y)
    ax.set_yticklabels([labels[k] for k in order], fontsize=9, color=INK2)
    ax.axvline(0, color=AXIS, linewidth=1)
    ax.set_xlim(min(0, min(0, po["store_fixed"], po["adj_ebitda"]) - 5), ax.get_xlim()[1] * 1.28)
    ax.set_xlabel("Rupees per order", fontsize=9.5, color=INK2, labelpad=8)
    _title(ax, "Where each order's money goes", f"Mature store at about {po['_density']:,.0f} orders a day, average order Rs {aov:,.0f}. Blue adds, orange subtracts. Model, calibrated to Blinkit's reported margins.")
    _save(fig, out, "fig_waterfall.png")


def fig_breakeven(out, curve, p, be_cm, be_ebitda):
    fig, ax = _ax((8.2, 4.8), "both")
    ax.axhline(0, color=AXIS, linewidth=1)
    ax.axvspan(p["breakeven_low"], p["breakeven_high"], color=GRID, alpha=0.9, zorder=1)
    ax.plot(curve["orders_per_store_day"], curve["contribution_pct"] * 100, color=BLUE, linewidth=2, zorder=3)
    ax.plot(curve["orders_per_store_day"], curve["adj_ebitda_pct"] * 100, color=ORANGE, linewidth=2, zorder=3)
    ax.axvline(p["orders_per_store_day"], color=MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=2)
    ax.axvline(p["nonmetro_orders"], color=MUTED, linewidth=1, linestyle=(0, (1, 3)), zorder=2)
    bottom = ax.get_ylim()[0]
    pad = (ax.get_ylim()[1] - bottom) * 0.03
    ax.text(p["orders_per_store_day"] + 25, bottom + pad, "Base case:\nabout 1,500 a day", fontsize=8.6, color=INK2, va="bottom")
    ax.text(p["nonmetro_orders"] - 25, bottom + pad, "Typical non-metro\nstore: about 850", fontsize=8.6, color=INK2, ha="right", va="bottom")
    ax.text((p["breakeven_low"] + p["breakeven_high"]) / 2, bottom + pad, "Industry\nbreak-even\nestimate", fontsize=8.6, color=INK2, ha="center", va="bottom")
    x_end = curve["orders_per_store_day"].iloc[-1]
    ax.text(x_end + 30, curve["contribution_pct"].iloc[-1] * 100, "Contribution", fontsize=9, color=INK, fontweight="bold", va="center")
    ax.text(x_end + 30, curve["adj_ebitda_pct"].iloc[-1] * 100, "Adjusted EBITDA", fontsize=9, color=INK, fontweight="bold", va="center")
    for be, c, lab in ((be_cm, BLUE, f"{be_cm:,.0f}"), (be_ebitda, ORANGE, f"{be_ebitda:,.0f}")):
        ax.scatter([be], [0], s=46, color=c, edgecolor=SURFACE, linewidth=1.6, zorder=5)
        ax.annotate(lab, (be, 0), xytext=(0, -16 if c == BLUE else 9), textcoords="offset points", ha="center", fontsize=9, color=INK, fontweight="bold")
    ax.set_xlim(curve["orders_per_store_day"].iloc[0], x_end * 1.13)
    ax.set_xlabel("Orders per store per day", fontsize=9.5, color=INK2, labelpad=8)
    ax.set_ylabel("Margin, % of order value", fontsize=9.5, color=INK2, labelpad=8)
    _title(ax, "A store has to be busy to make money", "Same costs per order, but the store's rent and staff are spread over more orders as volume rises. Dots: break-even points.")
    _save(fig, out, "fig_breakeven.png")


def fig_tornado(out, t):
    d = t.iloc[::-1].reset_index(drop=True)
    fig, ax = _ax((8.2, 4.9), "x")
    y = np.arange(len(d))
    gains = np.where(d["up_10pct"] > d["down_10pct"], d["up_10pct"], d["down_10pct"])
    losses = np.where(d["up_10pct"] > d["down_10pct"], d["down_10pct"], d["up_10pct"])
    ax.barh(y, gains, height=0.55, color=BLUE, edgecolor=SURFACE, linewidth=1.6, zorder=3, label="Moves in the helpful direction")
    ax.barh(y, losses, height=0.55, color=ORANGE, edgecolor=SURFACE, linewidth=1.6, zorder=3, label="Moves in the harmful direction")
    for yi, g, l in zip(y, gains, losses):
        ax.text(g + 0.25, yi, f"+{g:.1f}", va="center", fontsize=8.8, color=INK)
        ax.text(l - 0.25, yi, f"{l:.1f}", va="center", ha="right", fontsize=8.8, color=INK)
    ax.axvline(0, color=AXIS, linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(d["dial"], fontsize=9, color=INK2)
    lim = max(abs(gains).max(), abs(losses).max()) * 1.22
    ax.set_xlim(-lim, lim)
    ax.set_xlabel("Change in contribution per order (Rs) when the dial moves 10% either way", fontsize=9.5, color=INK2, labelpad=8)
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK2, loc="upper left", bbox_to_anchor=(0, -0.16), ncol=2)
    _title(ax, "Which dials move the money most", "Each dial changed 10% up and 10% down, everything else fixed. Base contribution: about Rs 28 per order.")
    _save(fig, out, "fig_tornado.png")


def fig_rice(out, rice, stab):
    d = rice.sort_values("rice_score").reset_index(drop=True)
    pf = stab.set_index("key")["p_first"]
    fig, ax = _ax((8.6, 4.4), "x")
    y = np.arange(len(d))
    ax.barh(y, d["rice_score"] / 1e6, height=0.55, color=BLUE, edgecolor=SURFACE, linewidth=1.6, zorder=3)
    for yi, (_, r) in zip(y, d.iterrows()):
        ax.text(r["rice_score"] / 1e6 + 0.03, yi, f"{r['rice_score'] / 1e6:.2f}   comes first in {100 * pf[r['key']]:.0f}% of re-scores",
                va="center", fontsize=8.8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(d["bet"], fontsize=9, color=INK2)
    ax.set_xlim(0, ax.get_xlim()[1] * 1.55)
    ax.set_xlabel("RICE score: Rs million of monthly contribution gained per person-month of effort", fontsize=9.5, color=INK2, labelpad=8)
    _title(ax, "Which product bet first", "Impact comes from the unit-economics model; confidence and effort are my estimates. Right: how often each wins when the inputs are jiggled.")
    _save(fig, out, "fig_rice.png")


def fig_ltv(out, ltv, cac):
    d = ltv.iloc[::-1].reset_index(drop=True)
    fig, ax = _ax((8.2, 3.9), "x")
    y = np.arange(len(d))
    ax.barh(y, d["ltv_rs"], height=0.52, color=BLUE, edgecolor=SURFACE, linewidth=1.6, zorder=3)
    ax.axvline(cac, color=ORANGE, linewidth=1.6, zorder=4)
    ax.set_ylim(-1.0, len(d) - 0.5)
    ax.text(cac + 8, -0.72, f"Cost to acquire a user: Rs {cac:,.0f}", fontsize=8.8, color=INK, va="center")
    for yi, (_, r) in zip(y, d.iterrows()):
        extra = "" if r["ltv_change_vs_base_pct"] == 0 else f"  ({r['ltv_change_vs_base_pct']:+.0f}%)"
        ax.text(r["ltv_rs"] + 8, yi, f"Rs {r['ltv_rs']:,.0f}{extra}", va="center", fontsize=9, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(d["scenario"], fontsize=9, color=INK2)
    ax.set_xlim(0, d["ltv_rs"].max() * 1.35)
    ax.set_xlabel("Discounted contribution from one new user over 24 months (Rs)", fontsize=9.5, color=INK2, labelpad=8)
    _title(ax, "What a new customer is worth", "Retention and funnel numbers are assumptions, not data. The comparison between levers is the point.")
    _save(fig, out, "fig_ltv.png")


def make_figures(out, p, po, curve, be, tor, rice, stab, ltv):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fig_waterfall(out, dict(po, _density=p["orders_per_store_day"]), p["aov"])
    fig_breakeven(out, curve, p, be["contribution"], be["adj_ebitda"])
    fig_tornado(out, tor)
    fig_rice(out, rice, stab)
    fig_ltv(out, ltv, p["cac"])
    print(f"charts written to {out}/")
