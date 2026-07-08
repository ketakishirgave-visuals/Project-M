"""
Project M — Data Loader
Loads all pipeline output artifacts once and caches them for the Streamlit session.
"""
import json
import os
import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _p(name):
    return os.path.join(DATA_DIR, name)


@st.cache_data
def load_all():
    d = {}

    d["strategy_matrix"] = pd.read_csv(_p("segment_strategy_matrix.csv"))
    d["causality_audit"] = pd.read_csv(_p("cashback_causality_audit.csv"))
    d["cluster_validation"] = pd.read_csv(_p("cluster_validation_report.csv"))
    d["cluster_stability"] = pd.read_csv(_p("cluster_stability_report.csv"))
    d["pop_confidence"] = pd.read_csv(_p("segment_population_confidence.csv"))
    d["policy_matrix"] = pd.read_csv(_p("cashback_policy_optimization_matrix.csv"))
    d["policy_recs"] = pd.read_csv(_p("segment_policy_recommendations.csv"))
    d["hunter_summary"] = pd.read_csv(_p("hunter_intent_classification_summary.csv"))
    d["wallet_diagnostic"] = pd.read_csv(_p("wallet_behavior_diagnostic.csv"))

    with open(_p("cluster_profiles.json")) as f:
        d["cluster_profiles"] = json.load(f)

    with open(_p("formal_production_verdict.json")) as f:
        d["production_verdict"] = json.load(f)

    with open(_p("cleaning_audit.md"), encoding="utf-8") as f:
        d["cleaning_audit_md"] = f.read()

    with open(_p("executive_cashback_strategy_report.txt"), encoding="utf-8") as f:
        d["executive_report_txt"] = f.read()

    # ── Static reference tables (persona metadata not otherwise machine-readable) ──
    d["persona_names"] = {
        0: "Expiry-Driven Converters",
        1: "Organic High-Intent Buyers",
        2: "Wallet Accumulators",
        3: "Passive Expiry Converters",
        4: "Aggressive Expiry Converters",
        5: "Premium Full-Price Loyalists",
    }

    d["persona_action_tag"] = {
        0: "Reduce",
        1: "Reduce",
        2: "Invest",
        3: "Exclude",
        4: "Reduce",
        5: "Exclude",
    }

    d["persona_one_liner"] = {
        0: "Converts late, close to expiry, heavily reward-triggered.",
        1: "Buys independently of incentives; discount is redundant spend.",
        2: "Accumulates wallet balance and responds strongly to more of it — the causal core of the strategy.",
        3: "Collects cashback, rarely redeems, rarely converts — a pure incentive drain.",
        4: "Sharp, high-velocity expiry-driven conversion, but heavily cost-sensitive.",
        5: "Micro-segment of full-price loyalists; near-zero cashback dependence.",
    }

    return d
