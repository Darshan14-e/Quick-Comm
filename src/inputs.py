"""Every number the model uses, with where it came from.

Tags:  D = disclosed by a company or a named source (see `source`)
       C = calibrated: chosen so the model reproduces a disclosed figure
       A = my assumption (no public figure exists for it); change it and re-run

The cost lines per order are NOT disclosed anywhere I could find. They are assumptions. What is anchored to public
data is the TOTAL: the model is calibrated so the base case reproduces Blinkit's reported contribution margin and
adjusted EBITDA margin. Treat the individual lines as plausible, not measured.
"""
from dataclasses import dataclass, field

BS = "https://www.business-standard.com/amp/markets/news/eternal-eyes-faster-blinkit-expansion-as-margins-and-order-values-grow-126102201467_1.html"
ANGEL = "https://www.angelone.in/news/stocks/eternal-share-price-gains-2-7-as-blinkit-net-order-value-jumps-79-3-in-q2-fy27"
BT = "https://www.businesstoday.in/markets/trending-stocks/story/swiggy-q2-results-loss-narrows-to-rs-922-cr-revenue-jumps-36-instamart-loss-at-rs-895-cr-563095-2026-10-22"
MEDIANAMA = "https://www.medianama.com/2026/10/223-eternal-q2-fy27-results-ai-strategy/"
LAPAAS = "https://lapaasvoice.com/blinkit-q1-fy27-daily-orders-cross-36-lakh-as-dark-store-count-tops-2400"
REDSEER = "https://redseer.com/digests/quick-commerce-india-scale-dark-stores-growth/"


@dataclass(frozen=True)
class Item:
    key: str
    label: str
    value: float
    unit: str
    tag: str
    source: str = ""
    note: str = ""


ITEMS = [
    # ---- the base case: a Blinkit-like mature store
    Item("aov", "Average order value (net)", 520.0, "Rs", "D", LAPAAS,
         "Reported as Rs 518 (Q1 FY27) and Rs 525 (Q4 FY26) by secondary sources; I could not open Eternal's own letter. "
         "The same article had an implausible revenue figure, so treat this one as approximate."),
    Item("item_price", "Average price per item", 85.0, "Rs", "A", "", "Gives about 6 items per order."),
    Item("orders_per_store_day", "Orders per store per day", 1500.0, "orders", "D", LAPAAS,
         "36 lakh+ daily orders / about 2,443 stores = about 1,475; the store count grew during the quarter, so this is approximate."),
    Item("margin_pct", "Product gross margin, share of order value", 0.170, "share", "A", "", "Blended across categories; own inventory is about 90-95% of sales (Medianama)."),
    Item("fees", "Delivery, handling and small-cart fees collected per order", 14.0, "Rs", "A", "", "Average across free and paid deliveries."),
    Item("ads_pct", "Brand ad income, share of order value", 0.040, "share", "A", "", "Management says neutral shelf space earns ad revenue (Medianama) but gives no figure."),
    Item("discount_pct", "Company-funded discounts, share of order value", 0.015, "share", "A"),
    Item("inv_loss_pct", "Inventory loss (wastage, shrink), share of order value", 0.018, "share", "D", MEDIANAMA, "Stated for July 2026; mostly perishables."),
    Item("delivery_cost", "Last-mile delivery cost per order", 36.0, "Rs", "A", "", "Rider pay, fuel and incentives."),
    Item("pickpack_total", "Picking and packing cost per order at base basket", 20.0, "Rs", "A"),
    Item("pickpack_per_item", "Extra picking cost per additional item", 1.0, "Rs", "A", "", "Used when a lever changes basket size."),
    Item("payment_pct", "Payment processing, share of order value", 0.009, "share", "A"),
    Item("support", "Customer support and other variable cost per order", 3.0, "Rs", "A"),
    # ---- anchors the model is calibrated to
    Item("target_cm_pct", "Blinkit contribution margin, Q2 FY27", 0.053, "share", "D", BS,
         "Reported as 5.3%; the article does not say the base, and the company has defined it as a share of GOV, not of net order value."),
    Item("target_ebitda_pct", "Blinkit adjusted EBITDA margin, Q2 FY27", 0.009, "share", "D", BS + " ; " + ANGEL, "Reported as 0.9%."),
    # ---- context
    Item("stores_now", "Blinkit stores, end of September 2026", 2751, "stores", "D", ANGEL),
    Item("breakeven_low", "Orders per day for a mature metro store to break even (low)", 1200, "orders", "D", REDSEER, "Industry estimate (Redseer); the margin level it refers to is not stated, so I compare it with EBITDA breakeven."),
    Item("breakeven_high", "Orders per day for a mature metro store to break even (high)", 1250, "orders", "D", REDSEER),
    Item("nonmetro_orders", "Typical non-metro store orders per day", 850, "orders", "D", REDSEER),
    Item("instamart_cm", "Instamart contribution margin, Q2 FY27", -0.01, "share", "D", BT, "As a share of GOV."),
    Item("instamart_ebitda", "Instamart adjusted EBITDA margin, Q2 FY27", -0.097, "share", "D", BT),
    # ---- retention and acquisition (no public figures: all assumptions)
    Item("ret_floor", "Share of new users who become long-run regulars", 0.20, "share", "A"),
    Item("ret_tau", "Months over which the other new users drop off", 1.5, "months", "A"),
    Item("orders_per_user_month", "Orders per active user per month", 4.0, "orders", "A"),
    Item("cac", "Cost to acquire one new user", 250.0, "Rs", "A"),
    Item("discount_rate_month", "Monthly discount rate", 0.015, "share", "A"),
    Item("horizon_months", "Customer lifetime horizon", 24, "months", "A"),
    # ---- AOV distribution for test sizing
    Item("aov_cv", "Spread of order value (std dev / mean)", 0.83, "ratio", "A", "", "Order values are right-skewed; replace with your own data."),
]

INPUTS = {i.key: i for i in ITEMS}
TAGS = {"D": "Disclosed (source linked)", "C": "Calibrated to a disclosed figure", "A": "My assumption"}


def values():
    return {i.key: i.value for i in ITEMS}


def as_rows():
    return [{"key": i.key, "label": i.label, "value": i.value, "unit": i.unit, "tag": i.tag, "source": i.source, "note": i.note} for i in ITEMS]
