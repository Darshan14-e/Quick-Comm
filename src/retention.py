"""Funnel and retention: how conversion drives order density, and what a new customer is worth.

There is no public cohort data for Indian quick commerce, so the retention curve and the funnel rates are
stated assumptions (see inputs.py). The value of this module is the structure: it shows how each lever moves
lifetime value and store density, and which one matters most, not what the true curve is.
"""
import numpy as np
import pandas as pd

from .economics import per_order

# stage, share of users at the previous stage who continue (assumptions)
FUNNEL = [("Opens the app", 1.00), ("Browses or searches", 0.88), ("Adds to cart", 0.42),
          ("Starts checkout", 0.78), ("Pays successfully", 0.94), ("Order delivered", 0.985)]


def survival(p, months=None):
    """Share of a new cohort still ordering in month t (t = 0 is the first month)."""
    n = int(p["horizon_months"] if months is None else months)
    t = np.arange(n)
    return p["ret_floor"] + (1 - p["ret_floor"]) * np.exp(-t / p["ret_tau"])


def lifetime_value(p, contribution_per_order=None, floor_add=0.0, freq_mult=1.0):
    """Discounted contribution from one newly acquired user over the horizon, in rupees."""
    q = dict(p, ret_floor=min(1.0, p["ret_floor"] + floor_add))
    cm = per_order(p)["contribution"] if contribution_per_order is None else contribution_per_order
    s = survival(q)
    t = np.arange(len(s))
    disc = (1 + p["discount_rate_month"]) ** (-t)
    return float((s * p["orders_per_user_month"] * freq_mult * cm * disc).sum())


def ltv_table(p):
    """Base case and what each customer-side lever does to lifetime value and payback."""
    base_cm = per_order(p)["contribution"]
    scen = [("Base case", dict()),
            ("Regulars +3 points (retention)", dict(floor_add=0.03)),
            ("Orders per user +5% (frequency)", dict(freq_mult=1.05)),
            ("Basket +4% (order value)", dict(contribution_per_order=per_order(p, p["aov"] * 1.04)["contribution"]))]
    rows = []
    for name, kw in scen:
        ltv = lifetime_value(p, **kw)
        s = survival(dict(p, ret_floor=min(1.0, p["ret_floor"] + kw.get("floor_add", 0.0))))
        monthly = p["orders_per_user_month"] * kw.get("freq_mult", 1.0) * kw.get("contribution_per_order", base_cm)
        cum = np.cumsum(s * monthly * (1 + p["discount_rate_month"]) ** (-np.arange(len(s))))
        payback = next((i + 1 for i, c in enumerate(cum) if c >= p["cac"]), None)
        rows.append({"scenario": name, "ltv_rs": ltv, "ltv_to_cac": ltv / p["cac"], "payback_months": payback})
    t = pd.DataFrame(rows)
    t["ltv_change_vs_base_pct"] = (t["ltv_rs"] / t.loc[0, "ltv_rs"] - 1) * 100
    return t


def funnel_table(p):
    rows, share = [], 1.0
    for name, rate in FUNNEL:
        share *= rate
        rows.append({"stage": name, "step_conversion": rate, "share_of_openers": share})
    return pd.DataFrame(rows)


def funnel_whatif(p, pp=0.01):
    """If one step converts `pp` (one percentage point) better, how many more orders per store and what is each order then worth?
    A point is worth more where the step converts poorly, which is the point of the table."""
    base_cm = per_order(p)["contribution"]
    rows = []
    for name, rate in FUNNEL[1:]:
        lift = min(1.0 - rate, pp) / rate
        d = p["orders_per_store_day"] * (1 + lift)
        rows.append({"step": name, "current_conversion": rate, "relative_lift": lift, "extra_orders_per_store_day": d - p["orders_per_store_day"],
                     "contribution_per_order_rs": per_order(p, density=d)["contribution"],
                     "gain_per_order_rs": per_order(p, density=d)["contribution"] - base_cm})
    return pd.DataFrame(rows).sort_values("relative_lift", ascending=False).reset_index(drop=True)
