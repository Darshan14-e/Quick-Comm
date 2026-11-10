# Metrics tree and funnel

*Structure is the point here. The funnel and retention rates are my assumptions, not data.*

## What the business is trying to grow

```
Monthly contribution (Rs)                                   <- the number the business cares about
|
+-- Orders per month
|   +-- Stores x orders per store per day                   <- density: the master variable (see fig_breakeven)
|       +-- Active users near each store
|       |   +-- New users (acquisition, cost per user Rs 250)
|       |   +-- Returning users (retention: about 20% become long-run regulars)
|       +-- Orders per user per month (about 4.0)   <- frequency
|       +-- Conversion: open -> browse -> cart -> checkout -> paid -> delivered   <- funnel below
|
+-- Contribution per order (Rs 27.6 now, 5.3% of order value)
    +-- Order value (about Rs 520)                 <- basket size: items per order x price per item
    +-- Product margin (17%), brand ad income (4%), customer fees (Rs 14)
    +-- Costs per order: delivery Rs 36, picking and packing Rs 20, discounts, inventory loss, payments, support
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
| Opens the app | 100.0% | 100.0% |
| Browses or searches | 88.0% | 88.0% |
| Adds to cart | 42.0% | 37.0% |
| Starts checkout | 78.0% | 28.8% |
| Pays successfully | 94.0% | 27.1% |
| Order delivered | 98.5% | 26.7% |

## Where one extra percentage point of conversion is worth most

A point is worth more where a step converts poorly, because it is a larger relative gain. The 'orders per store' column is at 1,500 orders a day now.

| Step | Converts today | Extra orders per store per day | Gain in contribution per order |
|---|---|---|---|
| Adds to cart | 42.0% | +36 | Rs 0.34 |
| Starts checkout | 78.0% | +19 | Rs 0.19 |
| Browses or searches | 88.0% | +17 | Rs 0.17 |
| Pays successfully | 94.0% | +16 | Rs 0.16 |
| Order delivered | 98.5% | +15 | Rs 0.15 |
