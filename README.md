# Project M: Customer Segmentation & Cashback Optimization

An end-to-end behavioral analytics pipeline investigating whether cashback incentives drive genuine customer loyalty or train users to delay purchases for discounts.

**Result:** A data-driven reallocation policy projecting **17.7% portfolio margin uplift** by shifting incentive spend from non-responsive segments toward verified responsive cohorts.

---

## 📋 What This Project Does

### Core Question
Do blanket cashback policies maximize margin, or do they subsidize price-sensitive "hunters" while overspending on organic high-intent buyers?

### Approach
1. **Simulate realistic customer behavior** across 2,000 users over 56 days, spanning three distinct archetypes (Sure Thing, Accidental Saver, Hunter)
2. **Clean and validate** operational inconsistencies with full audit trail
3. **Engineer 12 behavioral features** from transaction, session, and wallet data
4. **Segment customers** into 6 statistically stable cohorts via Gaussian Mixture Modeling
5. **Classify Hunter Intent** across segments using a composite gaming-behavior index
6. **Audit causality** using a response-score × redemption-rate framework to distinguish true incentive responsiveness from correlation
7. **Optimize policy** with a constrained elasticity engine projecting margin impact
8. **Measure confidence** via Monte Carlo simulation across 1,000 policy perturbations
9. **Visualize findings** in an interactive Streamlit investigation complementing Power BI dashboards

---

## 🏗️ Pipeline Architecture

```
Data Simulation (Block 1)
    ↓ [2,000 customers × 56-day event loop]
Data Cleaning (Block 2)
    ↓ [3,880 ghost sessions corrected, null taxonomy applied]
Feature Engineering (Block 3)
    ↓ [12 label-blind behavioral metrics extracted]
Segmentation via GMM (Block 4)
    ↓ [6 clusters, validated across 4 random seeds]
Hunter Intent Classification (Block 3.5)
    ↓ [Composite gaming-behavior index, cross-segment]
Causality Audit (Block 5)
    ↓ [Response score × redemption rate → defendability index]
Policy Optimization (Block 6)
    ↓ [Constrained elasticity ladder, margin-maximizing]
Monte Carlo Confidence (Ch. 9)
    ↓ [Range-of-outcomes bands, 1,000 perturbations]
Executive Recommendations (Ch. 12)
    ↓ [8 recommendations, each traced to SQL block]
```

---

## 🔑 Key Findings

### Customer Segments (6 Stable Cohorts)

| Segment | Size | Profit/CB Rupee | Elasticity | Policy | Rationale |
|---------|------|-----------------|-----------|--------|-----------|
| **Organic High-Intent Buyers** | 30.8% | ₹10.54–11.16 | 0.12 (inelastic) | **Reduce −20%** | Highest margin without cashback; spend is redundant |
| **Wallet Accumulators** | 25.8% | ₹6.56–6.93 | 1.65 (elastic) | **Increase +20%** | Only segment with verified causal responsiveness |
| **Expiry-Driven Converters** | 12.1% | ₹4.21–5.04 | 0.85 | **Maintain** | Moderate responsiveness; directional improvement limited |
| **Aggressive Expiry Converters** | 12.6% | ₹3.19–3.40 | 0.55 | **Reduce −20%** | Lowest margin; 12.8% deliberate-expiry leakage |
| **Passive Expiry Converters** | 18.3% | ₹3.84–4.07 | −0.25 (negative) | **Exclude** | Collects cashback, rarely converts; incentive drain |
| **Premium Full-Price Loyalists** | 0.45% | ₹13.34–14.22 | 0.00 | **Exclude** | Micro-segment; near-zero cashback dependence |

### Business Impact

- **Portfolio Margin Uplift:** 17.7% simulated improvement (₹15.6L profit recovery)
- **Cashback Leakage by Segment:** 2.5% (Organic) → 12.8% (Aggressive Expiry)
- **Concentration Risk:** Top 10% of users consume 17.3% of cashback but generate only 9.3% of profit
- **Post-Peak Behavior:** 84.2% of post-peak purchases occur at lower wallet balances, contradicting a "reward threshold" narrative

### Statistical Insights

- **Wallet-to-Basket Correlation:** Near-zero across all segments (|r| < 0.18) — wallet size relates to *timing*, not *basket size*
- **Profitability Stability:** High-margin segments hold their return profile across New/Mid/Mature tenure cohorts
- **Cluster Stability:** 6-cluster GMM validates consistently across 4 random seeds; no spurious fragmentation

---

## 📁 Directory Structure

```
project_m/
├── app.py                              # Streamlit entrypoint
├── data_loader.py                      # Session-state caching for pipeline outputs
├── ui_helpers.py                       # Reusable card, badge, and visualization primitives
├── requirements.txt
├── data/                               # All pipeline outputs (read-only, 11 CSV/JSON files)
│   ├── segment_strategy_matrix.csv
│   ├── cashback_causality_audit.csv
│   ├── cashback_policy_optimization_matrix.csv
│   ├── segment_policy_recommendations.csv
│   ├── cluster_profiles.json
│   └── [7 more files: stability, confidence, diagnostics, audit, executive report]
└── chapters/                           # 12-chapter narrative investigation
    ├── ch00_landing.py                 # Cold open — framing the question
    ├── ch01_experience.py              # How the cashback mechanic works
    ├── ch02_is_it_free.py              # Cost framing — customer acquisition lens
    ├── ch03_price_inflation.py         # Ruling out price-adjustment confounds
    ├── ch04_why_expensive.py           # Blanket vs. targeted policy trade-offs
    ├── ch05_cleaning.py                # Data integrity audit with before/after examples
    ├── ch06_features.py                # Behavioral feature extraction rationale
    ├── ch07_segmentation.py            # Six personas and their profiles
    ├── ch07b_hunter_intent.py          # Cross-segment gaming-intent classification
    ├── ch08_optimization.py            # Elasticity engine + live simulator
    ├── ch09_confidence.py              # Monte Carlo confidence bands and ranges
    ├── ch10_recommendation.py          # The decision memo and deployment limitations
    ├── ch11_sql_index.py               # 11 full SQL investigations with Best/Worst/Gap outputs
    └── ch12_executive_recommendations.py # 8 actionable recommendations, each sourced
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Streamlit
- pandas, numpy, scikit-learn, plotly

### Run the Investigation

```bash
streamlit run app.py
```

The Streamlit app will open in your browser at ``. Navigate non-linearly through all 12 chapters using the floating sidebar rail.

---

## 📊 Outputs & Deliverables

### Interactive Streamlit Investigation
- **Non-linear navigation:** Jump to any chapter, any time
- **Skim mode toggle:** Collapse expandables, keep insights visible
- **Architecture modal:** One-click reference to the full pipeline
- **"View the receipts" expanders:** Every claim links to its SQL block and output
- **Best / Worst / Gap cards:** Segment-level comparisons in standardized format
- **Monte Carlo confidence bands:** Range-of-outcomes for each segment under alternative policies
- **Live policy simulator:** Action-framed ("Increase Wallet Accumulators +20%") with cascading Margin → Revenue → Recommended Action logic

### CSV Outputs
- `segment_strategy_matrix.csv` — Strategic quadrant + budget trajectory for each segment
- `cashback_causality_audit.csv` — Response score × redemption rate → defendability index
- `cashback_policy_optimization_matrix.csv` — Scenario comparison table (Exclude, Reduce −20%, Maintain, Increase +20%)
- `cluster_stability_report.csv` — 6-cluster consistency across 4 random seeds
- `segment_population_confidence.csv` — Population size and statistical status (Stable vs. Micro-Segment)
- `hunter_intent_classification_summary.csv` — Cross-segment distribution of identified hunters

### JSON Metadata
- `cluster_profiles.json` — Four-layer persona architecture (statistical signature → behavioral translation → archetype → final name)
- `formal_production_verdict.json` — Cluster 6 consolidation rationale and volumetric audit

---

## 📈 How to Interpret the Findings

### For a Hiring Manager / Executive
- **Start with Ch. 0 (Cold Open)** to understand the business question, then jump to **Ch. 12 (Executive Recommendations)** for the 8 actionable takeaways.
- Each recommendation includes a confidence badge (✅ Strong / 🟡 Moderate / 🔴 Exploratory) and cites the exact SQL block that supports it.

### For a Analytics Engineer
- **Ch. 5 (Cleaning)** shows the data-integrity decisions and their business impact.
- **Ch. 6 (Features)** documents the label-blind feature extraction.
- **Ch. 7 (Segmentation)** explains GMM tuning, cluster stability validation, and the 6 personas.
- **Ch. 8 (Optimization)** covers the elasticity assumptions and constrained policy ladder.
- **Ch. 11 (SQL Investigation)** contains all 11 investigative SQL blocks with full computation trails.

### For a Product Manager / Strategy Lead
- **Ch. 2 (Is Cashback Free?)** frames the true cost structure.
- **Ch. 4 (Why Still Expensive)** compares blanket vs. targeted spend efficiency.
- **Ch. 8 (Optimization Engine)** includes a *live simulator* to test alternative allocation strategies in real-time.

---

## ⚠️ Limitations & Caveats

1. **Synthetic Data:** All findings are based on a simulated 2,000-customer dataset with intentional archetypes (Sure Thing, Accidental Saver, Hunter). Real-world validation on production data is required before deployment.

2. **Causality Audit, Not Proof:** The causality-defendability index (response score × redemption rate) indicates responsiveness but does not establish true causal effect. A/B testing is the gold standard for validation.

3. **No Price Inflation Test:** The current pipeline does not include competitive pricing parity checks. If Myntra adjusts prices in tandem with cashback, a separate pricing-fairness audit is necessary.

4. **Segment-Level, Not User-Level:** Recommendations apply at the behavioral cohort level, not individual user level. Enforcement requires cohort-based rules (e.g., "if `j_curve_ratio > 1.85`, apply policy X").

5. **7-Day Wallet Expiry:** The simulation assumes a hard 7-day expiry window. Real-world behavior may differ under different expiry policies.

---

## 🔍 Methodology Highlights

### Why Gaussian Mixture Modeling (GMM)?
- **Soft clustering:** Users can have fractional assignment to multiple segments, better reflecting real-world behavioral overlap.
- **Stability validation:** Refit across 4 random seeds to ensure clusters aren't artifacts of initialization.
- **No label leakage:** Features are extracted blind to ground-truth archetypes, ensuring the discovered patterns are emergent, not engineered.

### Why Causality Audit Instead of Correlation?
- **Response Score:** (% change in conversion) / (% change in cashback) within each segment.
- **Redemption Rate:** % of allocated cashback actually redeemed (not collected and expired).
- **Defendability Index:** Response Score × Redemption Rate — captures both sensitivity *and* utilization.
- **Guard against overclaims:** Weak response score + high expiry rate (like Passive Expiry Converters) signals a trap, not an opportunity.

### Why Monte Carlo for Confidence Bands?
- **Non-parametric:** No distributional assumptions needed.
- **Perturbation:** 1,000 random walks through policy space to estimate outcome ranges.
- **Decision-support:** Range-of-outcomes view (Best / Worst / Median) informs risk tolerance and experimentation design.

---

## 📚 Reference Outputs

All pipeline outputs are reproducible from the scripts. Key reference tables:

- **`cluster_profiles.json`:** Detailed persona architecture with statistical signatures and behavioral translations.
- **`cashback_causality_audit.csv`:** Response scores and causality indices by segment.
- **`cashback_policy_optimization_matrix.csv`:** Scenario-by-scenario margin projections for every segment.
- **`executive_cashback_strategy_report.txt`:** Full text report with portfolio uplift summary.
- **`cleaning_audit.md`:** Detailed log of every data-quality decision and its impact.

---

## 📄 License

This project is provided as-is for portfolio and research purposes. 

-- 
**Author:** Ketaki Shirgave
**Purpose:** Portfolio case study demonstrating end-to-end behavioral analytics, causal inference, and business strategy recommendation.

---
