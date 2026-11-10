# A/B test plan: "Complete your basket" add-on row

*All baseline numbers (spread of basket value, refund rate, user-level correlation) are assumptions to be replaced with real data. The sample-size formulas are standard and are tested in `tests/`.*

## Hypothesis

Showing relevant one-tap add-ons in the cart raises order value by at least 2% and contribution per order by a corresponding amount,
without slowing delivery, raising refunds or lowering checkout conversion.

## Design

| Item | Choice | Reason |
|---|---|---|
| Unit of randomisation | User (hash of user id, fixed for the test) | A user must see one experience; per-order randomisation would mix them |
| Arms | Control (no row) vs Treatment (row) | One change at a time |
| Population | Users in one mature metro city who open the cart | The feature only exists in the cart |
| Traffic | 20% of eligible users (10% treatment, 10% control) | Limits the blast radius; the sample is still ample (below) |
| Duration | At least 14 days, whole weeks only | Weekday and weekend behave differently; the first days are inflated by novelty |
| Primary metric | Contribution per order | What the business is paid on |
| Supporting | Order value, items per order, add-on attach rate | Explain why the primary moved |
| Guardrails | Delivery time p90, refund and cancellation rate, checkout conversion, 30-day reorder rate | The feature must not harm what the product is built on |
| Pre-checks | Sample ratio mismatch test (chi-square) on user counts; identical pre-test spend in both arms | Catches broken randomisation before reading any result |

## How many orders are needed

| Quantity | Value |
|---|---|
| Baseline order value | Rs 520 |
| Spread (std dev) | Rs 432 (assumed ratio 0.83) |
| Smallest lift worth shipping | 2% = Rs 10.4 |
| Orders per arm, basic formula (80% power, 5% two-sided) | 27,036 |
| Inflated for repeat orders from the same user (design effect 1.2) | 32,443 |
| After adjusting for each user's earlier spend (removes about 25% of variance) | 24,332 |
| Eligible orders per day in a 100-store city (reference) | 90,000 |
| Days to collect that sample | 3, so the two-week minimum applies |
| Orders per arm after 14 days | 126,000 |
| Smallest lift detectable at that size | 0.9% of order value (Rs 4.6) |

**The primary metric is not limited by sample size; it is limited by validity.** The two-week minimum, the novelty check and the guardrails matter more than power for the primary metric.

### Guardrails need more orders than the primary metric

Rare events need far more orders. To detect a rise in refunds from 2.0% to 2.3%
(+0.3 points) with 80% power, each arm needs about **36,693 orders**, which takes about 5 days at this traffic, so the two-week minimum still covers it in a 100-store city.
In a smaller test (a few stores) the guardrail, not the primary metric, would set the length. Size the test for the guardrails.

## Does the sample-size formula work? A simulation check

Basket values are skewed, so I simulated 3,000 tests with log-normal basket values (mean Rs 520, same spread) and ran Welch t-tests.

| Case | Orders per arm | Share of simulated tests with p < 0.05 |
|---|---|---|
| No real effect (false-positive rate; should be about 5%) | 27,036 | 4.9% |
| A real 2% lift (power; should be about 80%) | 27,036 | 78.9% |

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
