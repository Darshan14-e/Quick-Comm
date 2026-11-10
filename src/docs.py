"""Write the PRD, the A/B test plan and the metrics tree from the model's numbers, so the documents cannot drift from the analysis."""
from . import abtest
from .economics import per_order

# Test-design assumptions (mine; replace with your own data)
USERS_ORDERS_DEFF = 1.20        # orders from the same user are alike: inflates the sample needed
CUPED_VARIANCE_REDUCTION = 0.25  # share of variance removed by adjusting for each user's pre-test spend
EXPOSED_SHARE = 0.20            # share of eligible traffic in the test (half treatment, half control)
GUARDRAIL_BASELINE_REFUND = 0.020
GUARDRAIL_MARGIN_REFUND = 0.003
EXPOSED_PCT = int(EXPOSED_SHARE * 100)
MDE_AOV_REL = 0.02              # smallest basket lift worth shipping


def _r(x, d=0):
    return f"{x:,.{d}f}"


def design_numbers(p, rice_row):
    mean, cv = p["aov"], p["aov_cv"]
    sd = mean * cv
    delta = mean * MDE_AOV_REL
    n_raw = abtest.n_per_arm_mean(sd, delta)
    n_design = int(n_raw * USERS_ORDERS_DEFF)
    n_cuped = int(abtest.n_per_arm_mean(sd, delta, variance_reduction=CUPED_VARIANCE_REDUCTION) * USERS_ORDERS_DEFF)
    eligible_per_day = rice_row["reach_orders_per_month"] / 30
    days = abtest.duration_days(n_cuped, eligible_per_day, share_in_test=EXPOSED_SHARE)
    days_needed = abtest.duration_days(n_cuped, eligible_per_day, share_in_test=EXPOSED_SHARE, min_days=1)
    n_collected = int(eligible_per_day * EXPOSED_SHARE / 2 * days)
    mde_abs = abtest.mde_mean(sd, n_collected / USERS_ORDERS_DEFF, variance_reduction=CUPED_VARIANCE_REDUCTION)
    n_guard = abtest.n_per_arm_proportion(GUARDRAIL_BASELINE_REFUND, GUARDRAIL_MARGIN_REFUND)
    days_guard = abtest.duration_days(n_guard, eligible_per_day, share_in_test=EXPOSED_SHARE, min_days=1)
    return dict(sd=sd, delta=delta, n_raw=n_raw, n_design=n_design, n_cuped=n_cuped, eligible_per_day=eligible_per_day, days=days, days_needed=days_needed,
                n_collected=n_collected, mde_abs=mde_abs, mde_rel=mde_abs / mean, n_guard=n_guard, days_guard=days_guard)


def metrics_tree(p, funnel, whatif):
    po = per_order(p)
    rows = "\n".join(f"| {r.step} | {_r(100 * r.current_conversion, 1)}% | +{_r(r.extra_orders_per_store_day, 0)} | Rs {r.gain_per_order_rs:.2f} |" for r in whatif.itertuples())
    f_rows = "\n".join(f"| {r.stage} | {_r(100 * r.step_conversion, 1)}% | {_r(100 * r.share_of_openers, 1)}% |" for r in funnel.itertuples())
    return f"""# Metrics tree and funnel

*Structure is the point here. The funnel and retention rates are my assumptions, not data.*

## What the business is trying to grow

```
Monthly contribution (Rs)                                   <- the number the business cares about
|
+-- Orders per month
|   +-- Stores x orders per store per day                   <- density: the master variable (see fig_breakeven)
|       +-- Active users near each store
|       |   +-- New users (acquisition, cost per user Rs {_r(p['cac'])})
|       |   +-- Returning users (retention: about {_r(100 * p['ret_floor'])}% become long-run regulars)
|       +-- Orders per user per month (about {p['orders_per_user_month']:.1f})   <- frequency
|       +-- Conversion: open -> browse -> cart -> checkout -> paid -> delivered   <- funnel below
|
+-- Contribution per order (Rs {po['contribution']:.1f} now, {100 * po['contribution'] / p['aov']:.1f}% of order value)
    +-- Order value (about Rs {_r(p['aov'])})                 <- basket size: items per order x price per item
    +-- Product margin ({100 * p['margin_pct']:.0f}%), brand ad income ({100 * p['ads_pct']:.0f}%), customer fees (Rs {p['fees']:.0f})
    +-- Costs per order: delivery Rs {p['delivery_cost']:.0f}, picking and packing Rs {p['pickpack_total']:.0f}, discounts, inventory loss, payments, support
    +-- Store rent and staff, spread over the store's orders
```

## Metric definitions

| Metric | Definition | Role |
|---|---|---|
| Contribution per order | Product margin + ads + fees - discounts - inventory loss - delivery - pick/pack - payment - support - store fixed cost / orders | North star for this case |
| Order value (AOV) | Net value of the basket | Primary lever of the bet |
| Items per order | Items in the delivered basket | Diagnostic: is AOV rising because of more items or pricier ones? |
| Orders per store per day | Delivered orders / store / day | Density |
| Delivery time (p90) | Minutes from order to door, 90th percentile | Guardrail: the promise the product is built on |
| Refund and cancellation rate | Orders refunded or cancelled / orders | Guardrail |
| 30-day reorder rate | Share of users with another order within 30 days | Guardrail: protects long-run retention |

## Funnel (assumed rates)

| Stage | Step conversion | Share of app openers |
|---|---|---|
{f_rows}

## Where one extra percentage point of conversion is worth most

A point is worth more where a step converts poorly, because it is a larger relative gain. The 'orders per store' column is at {_r(p['orders_per_store_day'])} orders a day now.

| Step | Converts today | Extra orders per store per day | Gain in contribution per order |
|---|---|---|---|
{rows}
"""


def prd(p, rice, stab, tor, design, ltv):
    top = rice.iloc[0]
    second = rice.iloc[1]
    po = per_order(p)
    flow = (per_order(p, p["aov"] * 1.10)["contribution"] - po["contribution"]) / (p["aov"] * 0.10)
    fixed_per_order = p["delivery_cost"] + p["pickpack_total"]
    pf = stab.set_index("key")["p_first"]
    gain4 = top["impact_rs_per_order"]
    return f"""# PRD: "Complete your basket" add-on recommendations in the cart

**Status:** draft for a portfolio case study. **Author:** Darshan. **Numbers:** from `results/` of this repo; every assumption is tagged in `results/inputs.csv`.
No internal company data was used. The company is a generic Blinkit/Instamart/Zepto-style quick-commerce app.

## 1. Summary

At the cart, show a short row of items that go with what the customer has already chosen, each added with one tap.
The model says basket size is the second-biggest lever on contribution per order after product margin, and it is one a
product team can move. A 4% larger basket on the orders that see the feature is worth about Rs {gain4:.1f} per order, which is
{100 * gain4 / po['contribution']:.0f}% of today's contribution per order (Rs {po['contribution']:.1f}). We propose to test it on {EXPOSED_PCT}% of traffic in one city for {design['days']} days.

## 2. Problem and evidence

- **Money per order is thin.** In the model, an average order of Rs {_r(p['aov'])} leaves Rs {po['contribution']:.1f} of contribution
  ({100 * po['contribution'] / p['aov']:.1f}%), calibrated to Blinkit's reported {100 * p['target_cm_pct']:.1f}%.
- **Most costs do not grow with the basket.** Delivery (Rs {p['delivery_cost']:.0f}) and picking and packing (Rs {p['pickpack_total']:.0f}) are Rs {fixed_per_order:.0f} per order
  ({100 * fixed_per_order / p['aov']:.0f}% of order value) whether the basket is small or large. So each extra rupee of basket brings about {100 * flow:.0f} paise of contribution,
  against an average of {100 * po['contribution'] / p['aov']:.0f} paise per rupee.
- **It is one of the two biggest dials.** Moving basket size 10% moves contribution by Rs {tor.set_index('dial').loc['Order value (basket size)', 'up_10pct']:.1f} per order
  (see `results/fig_tornado.png`); only product margin matters more, and that is mostly category mix.
- **It also raises lifetime value.** A basket 4% larger lifts a new customer's modelled 24-month value by {ltv.set_index('scenario').loc['Basket +4% (order value)', 'ltv_change_vs_base_pct']:.0f}%.
- **What I do not have:** customer research and real cart data. Before building, I would run the checks in section 9.

## 3. Goals and non-goals

**Goals**
1. Raise order value without slowing delivery or hurting checkout.
2. Make adding a forgotten item easier than placing a second order and paying the fee again.

**Non-goals** (for this version): personalised pricing, private-label push, changing delivery-fee rules (that is the separate progress-bar bet, section 8), recommendations anywhere other than the cart.

## 4. Who it is for

A customer who ordered in a hurry and realises at the cart that something is missing (for example, milk with cereal and no sugar).
They want to avoid a second order, a second fee and a second wait.

## 5. Proposed solution

A horizontal row titled "Often bought together" under the cart items, 4 to 8 tiles, each with price and a one-tap add button.

**Which items:** candidates are items often bought together with what is in the cart, taken from past orders in that store.
They are filtered and ranked as follows.

| Rule | Why |
|---|---|
| In stock at this store with at least a day's cover | Never offer what cannot be delivered |
| Not already in the cart, no near-duplicates | Avoid noise |
| Price at most 30% of the cart value | Avoid sticker shock on small carts |
| Rank by chance of being added x margin, with a cap on any one brand | Value for the customer and the business without dumping on one brand |
| Items near expiry get a boost when discounted (P1) | Ties the feature to wastage; links to my inventory project |
| Excluded categories: alcohol, tobacco, medicines | Regulatory and trust |

**Never** add an item without a tap. Silent additions would resemble "basket sneaking" under India's 2023 dark-pattern guidelines, as I understand them; legal should confirm.

## 6. Requirements

| # | Requirement | Priority | Acceptance |
|---|---|---|---|
| 1 | Show 4-8 relevant, in-stock tiles under the cart, one-tap add | P0 | Tile added to the cart in one tap; cart total updates immediately |
| 2 | Recommendations load within the cart page budget | P0 | p95 under 150 ms; if slower, the row is hidden, never blocks checkout |
| 3 | Filters in section 5 enforced | P0 | Automated test: no out-of-stock, duplicate or excluded-category item is ever shown |
| 4 | Kill switch and traffic ramp | P0 | Can be turned off per city in under 5 minutes |
| 5 | Event logging: impression, tap, add, removal, order | P0 | Every metric in section 7 computable from logs |
| 6 | Per-store stock-out and expiry feed | P1 | Updated at least every 15 minutes |
| 7 | Near-expiry boost | P1 | Behind a flag, tested separately |
| 8 | "Why this item" label | P2 | Shown only if user research says it helps |

## 7. Success metrics and guardrails

| Level | Metric | Today (model) | Decision rule |
|---|---|---|---|
| Primary | Contribution per order | Rs {po['contribution']:.1f} | Ship if the 95% interval is above zero and the guardrails hold |
| Supporting | Order value, items per order, add-on attach rate (share of orders with a recommended item) | Rs {_r(p['aov'])} | Must move in the right direction; explains the primary |
| Guardrail | Delivery time p90 | no worse than +20 seconds | Stop if breached |
| Guardrail | Refund and cancellation rate | no worse than +{100 * GUARDRAIL_MARGIN_REFUND:.1f} points | Stop if breached |
| Guardrail | Checkout conversion | no worse than -0.5% relative | Stop if breached |
| Guardrail | 30-day reorder rate | no worse than -0.5 points | Reviewed in the long-term holdout |

Test design is in `AB_TEST_PLAN.md`.

## 8. Alternatives considered (RICE)

All six bets scored with impact taken from the model (`results/rice.csv`). Confidence and effort are my estimates.

| Rank | Bet | Monthly gain, 100-store city | RICE | Comes first in re-scores |
|---|---|---|---|---|
{chr(10).join(f"| {r.rank} | {r.bet} | Rs {_r(r.monthly_gain_rs / 1e6, 1)} M | {_r(r.rice_score / 1e6, 2)} M | {100 * pf[r.key]:.0f}% |" for r in rice.itertuples())}

The add-on row is ranked first but not by a wide margin: the free-delivery progress bar ({second['bet']}) is a close second and much cheaper to build.
Both change basket size on the same screen, so they should not be tested at the same time on the same users. Recommended order: ship the progress bar as a quick first test,
then the add-on row, or run them together as a 2x2 test (see the test plan).

## 9. Before building: what I would check first

1. **Real cart data:** what share of carts already contain a complementary item pair, and what is the median add-on price? If baskets are already complete, the lift is smaller.
2. **Customer research:** five to eight short interviews or an intercept survey on why second orders happen.
3. **Supply side:** can stores stock the offered items reliably? A recommendation for an out-of-stock item is worse than none.
4. **Ads:** does the row compete with sponsored slots? Agree how ad placements and organic recommendations share the row.

## 10. Rollout and timeline

| Phase | Traffic | Gate to move on |
|---|---|---|
| Internal dogfood | employees | No crashes, filters verified |
| Ramp | 5% | Guardrails flat for 3 days |
| Experiment | {EXPOSED_PCT}% (half treatment, half control), one city, {design['days']} days | Decision rules in section 7 |
| Rollout | one more city, then everywhere; 5% long-term holdout kept for retention | Replicates in the second city |

Estimated effort: about {top['effort_person_months']:.0f} person-months (engineering, data science, design).

## 11. Risks

| Risk | Mitigation |
|---|---|
| A busier cart lowers checkout conversion | Conversion is a guardrail; the row collapses on small screens and never covers the pay button |
| More items slow picking and delivery | Delivery time is a guardrail; the model charges Rs {p['pickpack_per_item']:.0f} per extra item |
| Irrelevant tiles train users to ignore the row | Track tap-through by position; retire weak rules |
| The lift is a novelty effect | Compare week 2 with week 1; keep a long-term holdout |
| Recommendations push unwanted items | Never auto-add; allow 'not interested' |

## 12. Open questions

- How should ad placements and organic recommendations share the row?
- Is a store-level cap on add-on units needed for perishable items?
- Does the row change the free-delivery threshold behaviour, and should that bet be tested first?
"""


def ab_plan(p, design, sim):
    return f"""# A/B test plan: "Complete your basket" add-on row

*All baseline numbers (spread of basket value, refund rate, user-level correlation) are assumptions to be replaced with real data. The sample-size formulas are standard and are tested in `tests/`.*

## Hypothesis

Showing relevant one-tap add-ons in the cart raises order value by at least {100 * MDE_AOV_REL:.0f}% and contribution per order by a corresponding amount,
without slowing delivery, raising refunds or lowering checkout conversion.

## Design

| Item | Choice | Reason |
|---|---|---|
| Unit of randomisation | User (hash of user id, fixed for the test) | A user must see one experience; per-order randomisation would mix them |
| Arms | Control (no row) vs Treatment (row) | One change at a time |
| Population | Users in one mature metro city who open the cart | The feature only exists in the cart |
| Traffic | {int(EXPOSED_SHARE * 100)}% of eligible users ({int(EXPOSED_SHARE * 50)}% treatment, {int(EXPOSED_SHARE * 50)}% control) | Limits the blast radius; the sample is still ample (below) |
| Duration | At least {design['days']} days, whole weeks only | Weekday and weekend behave differently; the first days are inflated by novelty |
| Primary metric | Contribution per order | What the business is paid on |
| Supporting | Order value, items per order, add-on attach rate | Explain why the primary moved |
| Guardrails | Delivery time p90, refund and cancellation rate, checkout conversion, 30-day reorder rate | The feature must not harm what the product is built on |
| Pre-checks | Sample ratio mismatch test (chi-square) on user counts; identical pre-test spend in both arms | Catches broken randomisation before reading any result |

## How many orders are needed

| Quantity | Value |
|---|---|
| Baseline order value | Rs {_r(p['aov'])} |
| Spread (std dev) | Rs {_r(design['sd'])} (assumed ratio {p['aov_cv']:.2f}) |
| Smallest lift worth shipping | {100 * MDE_AOV_REL:.0f}% = Rs {design['delta']:.1f} |
| Orders per arm, basic formula (80% power, 5% two-sided) | {_r(design['n_raw'])} |
| Inflated for repeat orders from the same user (design effect {USERS_ORDERS_DEFF}) | {_r(design['n_design'])} |
| After adjusting for each user's earlier spend (removes about {int(100 * CUPED_VARIANCE_REDUCTION)}% of variance) | {_r(design['n_cuped'])} |
| Eligible orders per day in a 100-store city (reference) | {_r(design['eligible_per_day'])} |
| Days to collect that sample | {design['days_needed']}, so the two-week minimum applies |
| Orders per arm after {design['days']} days | {_r(design['n_collected'])} |
| Smallest lift detectable at that size | {100 * design['mde_rel']:.1f}% of order value (Rs {design['mde_abs']:.1f}) |

**The primary metric is not limited by sample size; it is limited by validity.** The two-week minimum, the novelty check and the guardrails matter more than power for the primary metric.

### Guardrails need more orders than the primary metric

Rare events need far more orders. To detect a rise in refunds from {100 * GUARDRAIL_BASELINE_REFUND:.1f}% to {100 * (GUARDRAIL_BASELINE_REFUND + GUARDRAIL_MARGIN_REFUND):.1f}%
(+{100 * GUARDRAIL_MARGIN_REFUND:.1f} points) with 80% power, each arm needs about **{_r(design['n_guard'])} orders**, which takes about {design['days_guard']} days at this traffic, so the two-week minimum still covers it in a 100-store city.
In a smaller test (a few stores) the guardrail, not the primary metric, would set the length. Size the test for the guardrails.

## Does the sample-size formula work? A simulation check

Basket values are skewed, so I simulated {sim['sims']:,} tests with log-normal basket values (mean Rs {_r(p['aov'])}, same spread) and ran Welch t-tests.

| Case | Orders per arm | Share of simulated tests with p < 0.05 |
|---|---|---|
| No real effect (false-positive rate; should be about 5%) | {_r(design['n_raw'])} | {100 * sim['null']:.1f}% |
| A real {100 * MDE_AOV_REL:.0f}% lift (power; should be about 80%) | {_r(design['n_raw'])} | {100 * sim['power']:.1f}% |

## Analysis plan (written before the test starts)

1. **Check randomisation:** sample-ratio test on user counts; compare pre-test spend between arms. If either fails, stop and debug.
2. **Primary:** difference in contribution per order with a 95% interval, using the user-adjusted estimator and standard errors clustered by user.
3. **Guardrails:** one-sided checks against the limits in the PRD. A breach stops the test.
4. **Novelty:** compare the lift in week 2 with week 1. If it decays, report the week-2 number.
5. **Segments** (new vs returning users, small vs large carts, store type): looked at only to explain, never to rescue a failed test. State in advance that they are exploratory.
6. **Decision rule:** ship if the primary interval is above zero and no guardrail is breached; otherwise do not ship, and write up what was learned.

## Things that could invalidate the result

| Threat | What I would do |
|---|---|
| Stock is shared between arms (a recommended item sells out for control users) | Small share of traffic keeps this negligible; check stock-outs by arm |
| Users in both arms share a household or device | Randomise on account; look for shared devices |
| A festival or promotion in the test window | Do not start the test in a sale week; note any events |
| Peeking: stopping when the result looks good | Fixed end date; no early looks at the primary metric |
| Many metrics, one lucky result | One primary metric; everything else is labelled supporting or exploratory |

## If the progress-bar test runs at the same time

Both touch the same screen. Either run them one after the other, or run a 2x2 test: four equal groups (neither, bar only, row only, both).
Each effect is then estimated from half the traffic, so the sample per effect stays about the same, but detecting an interaction between the two needs roughly four times as many orders.
"""
