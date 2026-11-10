"""Unit economics of one dark store: money per order, store break-even and which lever matters.

Two levels of margin, as the companies report them:
  contribution  = what is left after product margin, ads and fees, minus every cost of serving the order AND the
                  store's own running costs (rent, staff) spread over the orders it handles
  adj. EBITDA   = contribution minus central costs (tech, corporate, marketing) per order

The store's fixed cost is why order density (orders per store per day) is the master variable: a store that
handles more orders spreads the same rent over more of them.
"""
from collections import OrderedDict
from copy import deepcopy

import numpy as np
import pandas as pd

from .inputs import values

# lines in waterfall order: key, label
LINES = [("gross_margin", "Product margin"), ("fees", "Customer fees"), ("ads", "Brand ad income"),
         ("discounts", "Discounts"), ("inventory_loss", "Inventory loss"), ("delivery", "Last-mile delivery"),
         ("pickpack", "Picking and packing"), ("payment", "Payment processing"), ("support", "Support and other")]


def calibrate(p=None):
    """Fill in the two numbers nobody discloses (store fixed cost per day, central cost per order) so the base case
    reproduces the reported contribution margin and adjusted EBITDA margin."""
    p = dict(values() if p is None else p)
    p["items_base"] = p["aov"] / p["item_price"]
    p["pickpack_base"] = p["pickpack_total"] - p["pickpack_per_item"] * p["items_base"]
    v = variable_contribution(p, p["aov"])
    p["store_fixed_per_day"] = (v - p["target_cm_pct"] * p["aov"]) * p["orders_per_store_day"]
    p["central_per_order"] = (p["target_cm_pct"] - p["target_ebitda_pct"]) * p["aov"]
    return p


def _lines(p, aov):
    items = aov / p["item_price"]
    return OrderedDict([
        ("gross_margin", p["margin_pct"] * aov),
        ("fees", p["fees"]),
        ("ads", p["ads_pct"] * aov),
        ("discounts", -p["discount_pct"] * aov),
        ("inventory_loss", -p["inv_loss_pct"] * aov),
        ("delivery", -p["delivery_cost"]),
        ("pickpack", -(p["pickpack_base"] + p["pickpack_per_item"] * items)),
        ("payment", -p["payment_pct"] * aov),
        ("support", -p["support"]),
    ])


def variable_contribution(p, aov):
    """Rupees left per order before the store's fixed costs."""
    if "pickpack_base" not in p:
        p = dict(p, pickpack_base=p["pickpack_total"] - p["pickpack_per_item"] * p["aov"] / p["item_price"])
    return float(sum(_lines(p, aov).values()))


def per_order(p, aov=None, density=None):
    """Full waterfall for one order. Returns an ordered dict of rupee amounts."""
    aov = p["aov"] if aov is None else aov
    density = p["orders_per_store_day"] if density is None else density
    d = _lines(p, aov)
    d["variable_contribution"] = sum(d.values())
    d["store_fixed"] = -p["store_fixed_per_day"] / density
    d["contribution"] = d["variable_contribution"] + d["store_fixed"]
    d["central"] = -p["central_per_order"]
    d["adj_ebitda"] = d["contribution"] + d["central"]
    return d


def margin_pct(p, aov=None, density=None, level="contribution"):
    aov = p["aov"] if aov is None else aov
    return per_order(p, aov, density)[level] / aov


def breakeven_density(p, level="contribution", aov=None):
    """Orders per store per day at which the chosen margin level is zero."""
    aov = p["aov"] if aov is None else aov
    v = variable_contribution(p, aov) - (p["central_per_order"] if level == "adj_ebitda" else 0.0)
    if v <= 0:
        return float("inf")
    return p["store_fixed_per_day"] / v


def density_curve(p, lo=200, hi=2600, n=121):
    d = np.linspace(lo, hi, n)
    return pd.DataFrame({"orders_per_store_day": d,
                         "contribution_pct": [margin_pct(p, density=x) for x in d],
                         "adj_ebitda_pct": [margin_pct(p, density=x, level="adj_ebitda") for x in d]})


# ------------------------------------------------------------------------------------------------ levers
def _apply(p, change):
    """change: dict with optional 'aov_mult', 'density_mult' and parameter multipliers like {'ads_pct': 1.1}."""
    q = deepcopy(p)
    aov = p["aov"] * change.get("aov_mult", 1.0)
    density = p["orders_per_store_day"] * change.get("density_mult", 1.0)
    for k, m in change.get("mult", {}).items():
        q[k] = q[k] * m
    return q, aov, density


def delta_contribution(p, change):
    """Change in contribution per order (rupees) from a lever, at the base order density."""
    q, aov, density = _apply(p, change)
    return per_order(q, aov, density)["contribution"] - per_order(p)["contribution"]


# the dials a product or ops team can actually turn. 'mult' multiplies a parameter; the others change the basket or density
DIALS = [
    ("Order value (basket size)", {"aov_mult": 1.10}),
    ("Orders per store per day", {"density_mult": 1.10}),
    ("Product gross margin", {"mult": {"margin_pct": 1.10}}),
    ("Brand ad income", {"mult": {"ads_pct": 1.10}}),
    ("Customer fees", {"mult": {"fees": 1.10}}),
    ("Last-mile delivery cost", {"mult": {"delivery_cost": 1.10}}),
    ("Picking and packing cost", {"mult": {"pickpack_total": 1.10, "pickpack_base": 1.10, "pickpack_per_item": 1.10}}),
    ("Discounts", {"mult": {"discount_pct": 1.10}}),
    ("Inventory loss", {"mult": {"inv_loss_pct": 1.10}}),
    ("Store fixed cost per day", {"mult": {"store_fixed_per_day": 1.10}}),
    ("Payment processing", {"mult": {"payment_pct": 1.10}}),
]


def _inverse(change):
    """The same dial moved by -10% instead of +10%."""
    out = {}
    if "aov_mult" in change:
        out["aov_mult"] = 0.90
    if "density_mult" in change:
        out["density_mult"] = 0.90
    if "mult" in change:
        out["mult"] = {k: 0.90 for k in change["mult"]}
    return out


def tornado(p):
    """Rupees per order gained or lost when each dial moves by 10% either way."""
    rows = []
    for name, ch in DIALS:
        rows.append({"dial": name, "up_10pct": delta_contribution(p, ch), "down_10pct": delta_contribution(p, _inverse(ch))})
    t = pd.DataFrame(rows)
    t["swing"] = (t["up_10pct"] - t["down_10pct"]).abs()
    return t.sort_values("swing", ascending=False).reset_index(drop=True)


# realistic moves for the product bets (RICE inputs). reach = share of orders touched; change = effect on a touched order
BETS = [
    dict(key="addon", name="Cart add-on recommendations", reach=0.60, change={"aov_mult": 1.04}, confidence=0.60, effort=3.0,
         what="Show 'complete your basket' items in the cart. A touched order grows 4% on average."),
    dict(key="nudge", name="Free-delivery progress bar", reach=0.25, change={"aov_mult": 1.05}, confidence=0.50, effort=1.5,
         what="Show how much more to add to remove the fee. Applies to the orders that land just under the threshold; they grow 5%."),
    dict(key="ads", name="Sponsored-product relevance", reach=0.80, change={"mult": {"ads_pct": 1.10}}, confidence=0.50, effort=4.0,
         what="Better targeting lifts ad income per order by 10% on the orders that see ads."),
    dict(key="batch", name="Rider batching", reach=0.25, change={"mult": {"delivery_cost": 0.85}}, confidence=0.40, effort=8.0,
         what="Pair nearby orders on one rider trip. Cuts delivery cost 15% on the orders that can be paired."),
    dict(key="waste", name="Perishable wastage forecasting", reach=0.40, change={"mult": {"inv_loss_pct": 0.80}}, confidence=0.50, effort=6.0,
         what="Forecast fresh-food demand per store to cut inventory loss 20% on orders with perishables."),
    dict(key="reorder", name="Reorder shortcuts", reach=0.70, change={"density_mult": 1.02}, confidence=0.50, effort=2.0,
         what="One-tap 'buy again' lifts orders per store 2% among exposed users; the gain is spread over all orders."),
]


def bet_impact(p, bet):
    """Rupees of contribution gained per touched order."""
    return delta_contribution(p, bet["change"])
