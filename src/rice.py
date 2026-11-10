"""RICE prioritisation of product bets, with the impact numbers coming from the unit-economics model.

RICE = Reach x Impact x Confidence / Effort.
  Reach       orders per month touched (reference city: 100 stores at base density)
  Impact      rupees of contribution gained per touched order  <- computed from the model, not guessed
  Confidence  my judgement, 0-1
  Effort      my estimate in person-months
The score is rupees of monthly contribution gained per person-month of effort, so the units mean something.
"""
import numpy as np
import pandas as pd

from .economics import BETS, bet_impact

REFERENCE_STORES = 100


def monthly_orders(p, stores=REFERENCE_STORES):
    return stores * p["orders_per_store_day"] * 30


def rice_table(p, bets=BETS):
    total = monthly_orders(p)
    rows = []
    for b in bets:
        reach = total * b["reach"]
        impact = bet_impact(p, b)
        rows.append({"key": b["key"], "bet": b["name"], "what": b["what"], "reach_orders_per_month": reach, "impact_rs_per_order": impact,
                     "confidence": b["confidence"], "effort_person_months": b["effort"],
                     "monthly_gain_rs": reach * impact, "rice_score": reach * impact * b["confidence"] / b["effort"]})
    t = pd.DataFrame(rows).sort_values("rice_score", ascending=False).reset_index(drop=True)
    t["rank"] = np.arange(1, len(t) + 1)
    return t


def rank_stability(p, n=5000, seed=7, impact_sd=0.30, conf_sd=0.20, effort_sd=0.30):
    """Re-score the bets many times with the inputs jiggled (log-normal noise) and count how often each comes first.
    If one bet wins only because of a lucky guess, this shows it."""
    rng = np.random.default_rng(seed)
    base = rice_table(p).set_index("key")
    keys = list(base.index)
    r, i, c, e = (base[k].to_numpy() for k in ("reach_orders_per_month", "impact_rs_per_order", "confidence", "effort_person_months"))
    wins = np.zeros(len(keys))
    top2 = np.zeros(len(keys))
    for _ in range(n):
        s = r * i * rng.lognormal(0, impact_sd, len(keys)) * np.clip(c * rng.lognormal(0, conf_sd, len(keys)), 0, 1) / (e * rng.lognormal(0, effort_sd, len(keys)))
        order = np.argsort(-s)
        wins[order[0]] += 1
        top2[order[:2]] += 1
    out = pd.DataFrame({"key": keys, "bet": base["bet"].to_numpy(), "p_first": wins / n, "p_top_two": top2 / n})
    return out.sort_values("p_first", ascending=False).reset_index(drop=True)
