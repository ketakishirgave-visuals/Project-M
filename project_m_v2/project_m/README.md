# Project M — Customer Segmentation & Cashback Policy Optimization

**The Investigation** — a Streamlit case-study app walking through the full analytics pipeline.

## Quick start

```bash
# From the project_m/ directory
pip install -r requirements.txt
streamlit run app.py
```

## Structure

```
project_m/
├── app.py                    # Main entrypoint — header, rail, routing
├── data_loader.py            # Loads & caches all pipeline outputs
├── ui_helpers.py             # Shared UI primitives (badges, receipts expanders, CSS)
├── requirements.txt
├── data/                     # All pipeline output artifacts (read-only)
│   ├── cluster_profiles.json
│   ├── cashback_causality_audit.csv
│   ├── cashback_policy_optimization_matrix.csv
│   ├── segment_strategy_matrix.csv
│   └── ...
└── chapters/
    ├── ch00_landing.py       # Cold open
    ├── ch01_experience.py    # Cashback mechanic storyboard
    ├── ch02_is_it_free.py    # Cost framing
    ├── ch03_price_inflation.py  # Wilcoxon test (credibility anchor)
    ├── ch04_why_expensive.py    # Blanket vs. targeted pivot
    ├── ch05_cleaning.py         # Data cleaning audit
    ├── ch06_features.py         # 12 behavioral features
    ├── ch07_segmentation.py     # Six segment profiles
    ├── ch07b_hunter_intent.py   # Hunter Intent cross-layer
    ├── ch08_optimization.py     # Policy engine + live simulator
    ├── ch09_confidence.py       # Monte Carlo confidence bands
    ├── ch10_recommendation.py   # The decision memo
    └── ch11_sql_index.py        # Full SQL investigation index
```

## Global UX rules (frozen v2)

- Every chapter: Question → Answer + confidence badge → compact evidence → opt-in expandables
- `View the receipts →` expander on every data claim
- Floating chapter rail, non-linear navigation always
- `🗺 Architecture` modal in header, one click away
- Skim mode toggle: collapses expandables, preserves Question + Answer + badge
- `🔬 Simulated Data` badge persistent in header
- Confidence badges: ✅ Strong / 🟡 Moderate / 🔴 Exploratory — applied per claim, not per chapter
