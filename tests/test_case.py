import math
import numpy as np
import pytest

from src import abtest
from src.economics import (BETS, breakeven_density, calibrate, delta_contribution, density_curve, per_order, tornado,
                           variable_contribution)
from src.inputs import INPUTS, TAGS
from src.retention import funnel_whatif, ltv_table, survival
from src.rice import rank_stability, rice_table


@pytest.fixture(scope="module")
def p():
    return calibrate()


# ---------- model
def test_calibration_hits_reported_margins(p):
    po = per_order(p)
    assert po["contribution"] / p["aov"] == pytest.approx(p["target_cm_pct"], abs=1e-9)
    assert po["adj_ebitda"] / p["aov"] == pytest.approx(p["target_ebitda_pct"], abs=1e-9)


def test_waterfall_adds_up(p):
    po = per_order(p)
    lines = ["gross_margin", "fees", "ads", "discounts", "inventory_loss", "delivery", "pickpack", "payment", "support"]
    assert sum(po[k] for k in lines) == pytest.approx(po["variable_contribution"])
    assert po["variable_contribution"] + po["store_fixed"] == pytest.approx(po["contribution"])
    assert po["contribution"] + po["central"] == pytest.approx(po["adj_ebitda"])


def test_breakeven_is_where_margin_is_zero(p):
    for level in ("contribution", "adj_ebitda"):
        d = breakeven_density(p, level)
        assert per_order(p, density=d)[level] == pytest.approx(0.0, abs=1e-6)


def test_more_density_means_more_margin(p):
    c = density_curve(p)["contribution_pct"].to_numpy()
    assert np.all(np.diff(c) > 0)


def test_breakeven_infinite_when_variable_contribution_not_positive(p):
    q = dict(p, margin_pct=0.0, ads_pct=0.0, fees=0.0)
    assert breakeven_density(q) == float("inf")


def test_tornado_signs_and_order(p):
    t = tornado(p).set_index("dial")
    assert t.loc["Last-mile delivery cost", "up_10pct"] < 0 < t.loc["Product gross margin", "up_10pct"]
    assert list(tornado(p)["swing"]) == sorted(tornado(p)["swing"], reverse=True)


def test_basket_lever_matches_hand_calculation(p):
    # +10% basket: extra margin, ads, discounts, loss, payment and picking of extra items; fees, delivery, support fixed
    extra = 0.1 * p["aov"]
    per_rupee = p["margin_pct"] + p["ads_pct"] - p["discount_pct"] - p["inv_loss_pct"] - p["payment_pct"] - p["pickpack_per_item"] / p["item_price"]
    assert delta_contribution(p, {"aov_mult": 1.10}) == pytest.approx(extra * per_rupee)


def test_inputs_are_tagged_and_sourced():
    assert set(TAGS) <= {"D", "C", "A"}
    from src.inputs import ITEMS
    for i in ITEMS:
        assert i.tag in {"D", "C", "A"}
        if i.tag == "D":
            assert i.source, f"disclosed input {i.key} needs a source"


# ---------- RICE
def test_rice_formula_and_order(p):
    t = rice_table(p)
    r = t.iloc[0]
    assert r["rice_score"] == pytest.approx(r["reach_orders_per_month"] * r["impact_rs_per_order"] * r["confidence"] / r["effort_person_months"])
    assert list(t["rice_score"]) == sorted(t["rice_score"], reverse=True)
    assert len(t) == len(BETS)


def test_rank_stability_is_a_distribution(p):
    s = rank_stability(p, n=500)
    assert s["p_first"].sum() == pytest.approx(1.0)
    assert s["p_top_two"].sum() == pytest.approx(2.0)


# ---------- retention
def test_survival_starts_at_one_and_floors(p):
    s = survival(p)
    assert s[0] == pytest.approx(1.0)
    assert np.all(np.diff(s) < 0) and s[-1] > p["ret_floor"]


def test_ltv_levers_raise_value(p):
    t = ltv_table(p)
    assert (t["ltv_change_vs_base_pct"].iloc[1:] > 0).all()


def test_funnel_whatif_orders_by_relative_lift(p):
    w = funnel_whatif(p)
    assert list(w["relative_lift"]) == sorted(w["relative_lift"], reverse=True)
    assert w["gain_per_order_rs"].iloc[0] > w["gain_per_order_rs"].iloc[-1] > 0


# ---------- A/B test maths
def test_sample_size_matches_textbook():
    assert abtest.n_per_arm_mean(1.0, 0.5) == 63          # sd 1, effect 0.5 sd, 5% / 80%: 63 per arm
    assert abtest.n_per_arm_proportion(0.10, 0.05) == 686  # 10% -> 15%, 5% / 80%: 686 per arm (standard table value)


def test_mde_inverts_sample_size():
    n = abtest.n_per_arm_mean(10, 1)
    assert abtest.mde_mean(10, n) <= 1.0 + 1e-9
    assert abtest.mde_mean(10, n - 5) > 1.0 - 0.02


def test_variance_reduction_cuts_sample():
    base = abtest.n_per_arm_mean(10, 1)
    assert abtest.n_per_arm_mean(10, 1, variance_reduction=0.5) == pytest.approx(base / 2, rel=0.01)


def test_duration_has_two_week_floor():
    assert abtest.duration_days(100, 10_000) == 14
    assert abtest.duration_days(1_000_000, 1_000) > 14


def test_lognormal_hits_target_mean_and_cv():
    mu, s = abtest.lognormal_params(520, 0.83)
    x = np.random.default_rng(0).lognormal(mu, s, 400_000)
    assert x.mean() == pytest.approx(520, rel=0.01)
    assert x.std() / x.mean() == pytest.approx(0.83, rel=0.03)


def test_simulation_agrees_with_formula():
    n = abtest.n_per_arm_mean(520 * 0.83, 520 * 0.02)
    fp = abtest.simulate_power(520, 0.83, 0.0, n, sims=1500)
    pw = abtest.simulate_power(520, 0.83, 0.02, n, sims=1500)
    assert 0.03 < fp < 0.07
    assert 0.74 < pw < 0.86
