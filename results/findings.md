# Findings (generated from the model; every number traces to `results/inputs.csv`)

**Read this first:** the cost lines per order are my assumptions, calibrated so the total matches the margins Blinkit reports. Only the totals are public. The model shows how levers *compare*, not what any company's true cost per order is.

## 1. Money per order
An order of Rs 520 earns Rs 42.4 before store costs, Rs 27.6 of contribution (5.3%) after the store's rent and staff, and Rs 4.7 (0.9%) after central costs.

## 2. Density is the master variable
The store costs Rs 22,200 a day whatever it sells. Contribution breaks even at 524 orders a day and adjusted EBITDA at 1,140 (Redseer's published estimate for mature metro stores: 1,200-1,250; its margin level is not stated, so I compare it with the EBITDA figure). Non-metro stores at about 850 orders a day sit below that line.

## 3. What moves contribution most (10% change in each dial)
- Product gross margin: +8.84 / -8.84 Rs per order
- Order value (basket size): +8.12 / -8.12 Rs per order
- Last-mile delivery cost: -3.60 / +3.60 Rs per order
- Brand ad income: +2.08 / -2.08 Rs per order
- Picking and packing cost: -2.00 / +2.00 Rs per order

Product margin and basket size dominate. Product margin is mostly category mix and sourcing, which a product team moves slowly; basket size is the one a product team can test.

## 4. Which bet first
By RICE, **Cart add-on recommendations** ranks first (1.75 M Rs of monthly contribution per person-month). It comes first in 54% of 5,000 re-scores with the inputs jiggled; the free-delivery progress bar comes first in 38%. The two are close and share a screen, so the plan suggests testing them together. Confidence and effort are my judgement.

## 5. Customer value (assumed retention curve)
A new customer is worth about Rs 627 over 24 months against an acquisition cost of Rs 250 (ratio 2.5). A 4% bigger basket adds 12%; three more points of long-run regulars add 10%. These curves are assumptions; there is no public cohort data.

## 6. Test sizing
To see a 2% basket lift you need about 24,332 orders per arm; a city collects that in 3 days, so the two-week minimum decides the length. The guardrail (refund rate) needs 36,693 orders per arm. See `docs/AB_TEST_PLAN.md`.

## Limits
- AOV and orders per store come from secondary sources and are approximate; store fixed cost and central cost are *derived* by calibration, not observed.
- Funnel rates, retention, CAC, bet reach, confidence and effort are assumptions.
- Bet effects (for example '+4% basket on touched orders') are hypotheses the A/B test is meant to measure.
- No company-internal data was used.
