"""Run the whole case: model -> tables -> charts -> findings -> PRD and test plan.   python run_analysis.py"""
import argparse
from pathlib import Path

import pandas as pd

from src import abtest, docs
from src.economics import breakeven_density, calibrate, density_curve, per_order, tornado
from src.inputs import as_rows
from src.report import make_figures
from src.retention import funnel_table, funnel_whatif, ltv_table
from src.rice import rank_stability, rice_table


def findings(p, po, be, tor, rice, stab, ltv, design):
    t = tor.set_index("dial")
    pf = stab.set_index("key")["p_first"]
    top = rice.iloc[0]
    b = ltv.set_index("scenario")
    lines = [
        "# Findings (generated from the model; every number traces to `results/inputs.csv`)", "",
        "**Read this first:** the cost lines per order are my assumptions, calibrated so the total matches the margins Blinkit reports. "
        "Only the totals are public. The model shows how levers *compare*, not what any company's true cost per order is.", "",
        f"## 1. Money per order\nAn order of Rs {p['aov']:.0f} earns Rs {po['variable_contribution']:.1f} before store costs, "
        f"Rs {po['contribution']:.1f} of contribution ({100 * po['contribution'] / p['aov']:.1f}%) after the store's rent and staff, "
        f"and Rs {po['adj_ebitda']:.1f} ({100 * po['adj_ebitda'] / p['aov']:.1f}%) after central costs.", "",
        f"## 2. Density is the master variable\nThe store costs Rs {p['store_fixed_per_day']:,.0f} a day whatever it sells. Contribution breaks even at "
        f"{be['contribution']:,.0f} orders a day and adjusted EBITDA at {be['adj_ebitda']:,.0f} (Redseer's published estimate for mature metro stores: "
        f"{p['breakeven_low']:,.0f}-{p['breakeven_high']:,.0f}; its margin level is not stated, so I compare it with the EBITDA figure). "
        f"Non-metro stores at about {p['nonmetro_orders']:,.0f} orders a day sit below that line.", "",
        f"## 3. What moves contribution most (10% change in each dial)\n" + "\n".join(
            f"- {r.dial}: {r.up_10pct:+.2f} / {r.down_10pct:+.2f} Rs per order" for r in tor.head(5).itertuples()),
        f"\nProduct margin and basket size dominate. Product margin is mostly category mix and sourcing, which a product team moves slowly; basket size is the one a product team can test.", "",
        f"## 4. Which bet first\nBy RICE, **{top['bet']}** ranks first ({top['rice_score'] / 1e6:.2f} M Rs of monthly contribution per person-month). "
        f"It comes first in {100 * pf[top['key']]:.0f}% of 5,000 re-scores with the inputs jiggled; the free-delivery progress bar comes first in "
        f"{100 * pf['nudge']:.0f}%. The two are close and share a screen, so the plan suggests testing them together. Confidence and effort are my judgement.", "",
        f"## 5. Customer value (assumed retention curve)\nA new customer is worth about Rs {b.loc['Base case', 'ltv_rs']:.0f} over {p['horizon_months']} months "
        f"against an acquisition cost of Rs {p['cac']:.0f} (ratio {b.loc['Base case', 'ltv_to_cac']:.1f}). A 4% bigger basket adds "
        f"{b.loc['Basket +4% (order value)', 'ltv_change_vs_base_pct']:.0f}%; three more points of long-run regulars add "
        f"{b.loc['Regulars +3 points (retention)', 'ltv_change_vs_base_pct']:.0f}%. These curves are assumptions; there is no public cohort data.", "",
        f"## 6. Test sizing\nTo see a 2% basket lift you need about {design['n_cuped']:,} orders per arm; a city collects that in {design['days_needed']} days, "
        f"so the two-week minimum decides the length. The guardrail (refund rate) needs {design['n_guard']:,} orders per arm. See `docs/AB_TEST_PLAN.md`.", "",
        "## Limits",
        "- AOV and orders per store come from secondary sources and are approximate; store fixed cost and central cost are *derived* by calibration, not observed.",
        "- Funnel rates, retention, CAC, bet reach, confidence and effort are assumptions.",
        "- Bet effects (for example '+4% basket on touched orders') are hypotheses the A/B test is meant to measure.",
        "- No company-internal data was used.", ""]
    return "\n".join(lines)


def main(out="results", docs_dir="docs", sims=3000):
    out, docs_dir = Path(out), Path(docs_dir)
    out.mkdir(exist_ok=True)
    docs_dir.mkdir(exist_ok=True)
    p = calibrate()
    po = per_order(p)
    curve = density_curve(p)
    be = {"contribution": breakeven_density(p), "adj_ebitda": breakeven_density(p, "adj_ebitda")}
    tor, rice, stab, ltv = tornado(p), rice_table(p), rank_stability(p), ltv_table(p)
    fun, what = funnel_table(p), funnel_whatif(p)

    pd.DataFrame(as_rows()).to_csv(out / "inputs.csv", index=False)
    pd.Series({k: v for k, v in po.items()}, name="rs_per_order").to_csv(out / "waterfall.csv")
    curve.to_csv(out / "density_curve.csv", index=False)
    tor.to_csv(out / "tornado.csv", index=False)
    rice.drop(columns=["what"]).to_csv(out / "rice.csv", index=False)
    stab.to_csv(out / "rank_stability.csv", index=False)
    ltv.to_csv(out / "ltv.csv", index=False)
    fun.to_csv(out / "funnel.csv", index=False)
    what.to_csv(out / "funnel_whatif.csv", index=False)
    make_figures(out, p, po, curve, be, tor, rice, stab, ltv)

    design = docs.design_numbers(p, rice.iloc[0])
    sim = {"sims": sims,
           "null": abtest.simulate_power(p["aov"], p["aov_cv"], 0.0, design["n_raw"], sims=sims),
           "power": abtest.simulate_power(p["aov"], p["aov_cv"], docs.MDE_AOV_REL, design["n_raw"], sims=sims)}
    (out / "findings.md").write_text(findings(p, po, be, tor, rice, stab, ltv, design))
    (docs_dir / "PRD.md").write_text(docs.prd(p, rice, stab, tor, design, ltv))
    (docs_dir / "AB_TEST_PLAN.md").write_text(docs.ab_plan(p, design, sim))
    (docs_dir / "METRICS_TREE.md").write_text(docs.metrics_tree(p, fun, what))
    print(f"contribution Rs {po['contribution']:.2f}/order ({100 * po['contribution'] / p['aov']:.2f}%), "
          f"breakeven {be['contribution']:.0f} / {be['adj_ebitda']:.0f} orders/day; test sim: false-positive {sim['null']:.3f}, power {sim['power']:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results")
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--sims", type=int, default=3000)
    a = ap.parse_args()
    main(a.out, a.docs, a.sims)
