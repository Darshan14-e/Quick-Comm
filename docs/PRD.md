# PRD: "Complete your basket" add-on recommendations in the cart

**Status:** draft for a portfolio case study. **Author:** Darshan. **Numbers:** from `results/` of this repo; every assumption is tagged in `results/inputs.csv`.
No internal company data was used. The company is a generic Blinkit/Instamart/Zepto-style quick-commerce app.

## 1. Summary

At the cart, show a short row of items that go with what the customer has already chosen, each added with one tap.
The model says basket size is the second-biggest lever on contribution per order after product margin, and it is one a
product team can move. A 4% larger basket on the orders that see the feature is worth about Rs 3.2 per order, which is
12% of today's contribution per order (Rs 27.6). We propose to test it on 20% of traffic in one city for 14 days.

## 2. Problem and evidence

- **Money per order is thin.** In the model, an average order of Rs 520 leaves Rs 27.6 of contribution
  (5.3%), calibrated to Blinkit's reported 5.3%.
- **Most costs do not grow with the basket.** Delivery (Rs 36) and picking and packing (Rs 20) are Rs 56 per order
  (11% of order value) whether the basket is small or large. So each extra rupee of basket brings about 16 paise of contribution,
  against an average of 5 paise per rupee.
- **It is one of the two biggest dials.** Moving basket size 10% moves contribution by Rs 8.1 per order
  (see `results/fig_tornado.png`); only product margin matters more, and that is mostly category mix.
- **It also raises lifetime value.** A basket 4% larger lifts a new customer's modelled 24-month value by 12%.
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
| Primary | Contribution per order | Rs 27.6 | Ship if the 95% interval is above zero and the guardrails hold |
| Supporting | Order value, items per order, add-on attach rate (share of orders with a recommended item) | Rs 520 | Must move in the right direction; explains the primary |
| Guardrail | Delivery time p90 | no worse than +20 seconds | Stop if breached |
| Guardrail | Refund and cancellation rate | no worse than +0.3 points | Stop if breached |
| Guardrail | Checkout conversion | no worse than -0.5% relative | Stop if breached |
| Guardrail | 30-day reorder rate | no worse than -0.5 points | Reviewed in the long-term holdout |

Test design is in `AB_TEST_PLAN.md`.

## 8. Alternatives considered (RICE)

All six bets scored with impact taken from the model (`results/rice.csv`). Confidence and effort are my estimates.

| Rank | Bet | Monthly gain, 100-store city | RICE | Comes first in re-scores |
|---|---|---|---|---|
| 1 | Cart add-on recommendations | Rs 8.8 M | 1.75 M | 54% |
| 2 | Free-delivery progress bar | Rs 4.6 M | 1.52 M | 38% |
| 3 | Sponsored-product relevance | Rs 7.5 M | 0.94 M | 9% |
| 4 | Rider batching | Rs 6.1 M | 0.30 M | 0% |
| 5 | Perishable wastage forecasting | Rs 3.4 M | 0.28 M | 0% |
| 6 | Reorder shortcuts | Rs 0.9 M | 0.23 M | 0% |

The add-on row is ranked first but not by a wide margin: the free-delivery progress bar (Free-delivery progress bar) is a close second and much cheaper to build.
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
| Experiment | 20% (half treatment, half control), one city, 14 days | Decision rules in section 7 |
| Rollout | one more city, then everywhere; 5% long-term holdout kept for retention | Replicates in the second city |

Estimated effort: about 3 person-months (engineering, data science, design).

## 11. Risks

| Risk | Mitigation |
|---|---|
| A busier cart lowers checkout conversion | Conversion is a guardrail; the row collapses on small screens and never covers the pay button |
| More items slow picking and delivery | Delivery time is a guardrail; the model charges Rs 1 per extra item |
| Irrelevant tiles train users to ignore the row | Track tap-through by position; retire weak rules |
| The lift is a novelty effect | Compare week 2 with week 1; keep a long-term holdout |
| Recommendations push unwanted items | Never auto-add; allow 'not interested' |

## 12. Open questions

- How should ad placements and organic recommendations share the row?
- Is a store-level cap on add-on units needed for perishable items?
- Does the row change the free-delivery threshold behaviour, and should that bet be tested first?
