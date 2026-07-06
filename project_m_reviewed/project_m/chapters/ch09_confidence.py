import numpy as np
import streamlit as st
import plotly.graph_objects as go
from ui_helpers import question_answer, receipts_expander, sim_footer, continue_to, ACCENT


def run_monte_carlo(n_simulations=2000, seed=42):
    rng = np.random.default_rng(seed)

    # Base optimal margin from the policy engine: ₹10,363,154
    # Per-segment contributions and uncertainty parameterisation
    segments = [
        {"name": "Expiry-Driven Converters",    "base": 908_849,    "sigma_pct": 0.08},
        {"name": "Organic High-Intent Buyers",   "base": 3_226_450,  "sigma_pct": 0.05},
        {"name": "Wallet Accumulators",          "base": 3_098_298,  "sigma_pct": 0.12},
        {"name": "Passive Expiry Converters",    "base": 2_150_197,  "sigma_pct": 0.03},
        {"name": "Aggressive Expiry Converters", "base": 930_728,    "sigma_pct": 0.09},
        {"name": "Premium Full-Price Loyalists", "base": 48_633,     "sigma_pct": 0.25},
    ]

    total_samples = np.zeros(n_simulations)
    seg_samples = {}
    for seg in segments:
        draws = seg["base"] + rng.normal(0, seg["base"] * seg["sigma_pct"], n_simulations)
        seg_samples[seg["name"]] = draws
        total_samples += draws

    return total_samples, seg_samples, segments


def render(data, skim_mode):
    st.markdown("## Chapter 9 — Portfolio Impact & Confidence")

    question_answer(
        question="This looks good on paper — how sure are we, and what could go wrong?",
        answer="The optimized policy holds up across a range of simulated futures, with a defined confidence band — not just a single point estimate.",
        badge_level="moderate",
    )

    st.info(
        "**Chapter 8 showed the expected outcome. This chapter shows the range of outcomes.**\n\n"
        "⚠️ Explicit note: this is a Monte Carlo simulation run over simulated data, a simulation of a simulation. "
        "The confidence bands reflect modeling uncertainty, not observed real-world variance. "
        
    )

    total_samples, seg_samples, segments = run_monte_carlo()
    p5, p25, p50, p75, p95 = np.percentile(total_samples, [5, 25, 50, 75, 95])
    baseline = 8_801_522

    # Compact default: confidence band + one risk callout
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("P5 (Downside)", f"₹{p5/1e5:.1f}L", delta=f"{(p5-baseline)/baseline*100:+.1f}% vs baseline")
    with m2:
        st.metric("P50 (Median)", f"₹{p50/1e5:.1f}L", delta=f"{(p50-baseline)/baseline*100:+.1f}% vs baseline")
    with m3:
        st.metric("P95 (Upside)", f"₹{p95/1e5:.1f}L", delta=f"{(p95-baseline)/baseline*100:+.1f}% vs baseline")
    with m4:
        certainty_pct = (total_samples > baseline).mean() * 100
        st.metric("Pr(beats baseline)", f"{certainty_pct:.0f}%")

    # Risk callout — always visible
    most_uncertain = max(segments, key=lambda s: s["sigma_pct"])
    most_certain = min(segments, key=lambda s: s["sigma_pct"])
    st.warning(
        f"**Highest uncertainty:** {most_uncertain['name']} (σ = {most_uncertain['sigma_pct']*100:.0f}% of base) — "
        f"micro-segment size makes the Exclude recommendation sensitive to small population shifts.\n\n"
        f"**Most stable:** {most_certain['name']} (σ = {most_certain['sigma_pct']*100:.0f}%) — "
        "organic buyers' behavior is predictable regardless of cashback changes."
    )

    if not skim_mode:
        st.markdown("---")
        # Distribution chart
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=total_samples / 1e5,
            nbinsx=60,
            marker_color=ACCENT,
            opacity=0.7,
            name="Simulated portfolio margin",
        ))
        fig.add_vline(x=baseline / 1e5, line_dash="dash", line_color="#C4573F",
                      annotation_text="Baseline (current policy)", annotation_position="top right")
        fig.add_vline(x=p50 / 1e5, line_dash="dot", line_color="#3FA66B",
                      annotation_text="P50 (optimized)", annotation_position="top left")
        fig.add_vrect(x0=p25 / 1e5, x1=p75 / 1e5, fillcolor=ACCENT, opacity=0.1,
                      annotation_text="50% confidence band")
        fig.update_layout(
            title="Distribution of optimized portfolio margin across 2,000 simulations",
            xaxis_title="Portfolio Margin (₹ Lakhs)",
            yaxis_title="Frequency",
            paper_bgcolor="#181A1F",
            plot_bgcolor="#22252C",
            font_color="#EDEBE6",
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Per-segment uncertainty
        st.markdown("#### Per-segment uncertainty contribution")
        seg_cols = st.columns(3)
        for i, seg in enumerate(segments):
            seg_draws = seg_samples[seg["name"]]
            sp5, sp95 = np.percentile(seg_draws, [5, 95])
            with seg_cols[i % 3]:
                st.markdown(
                    f"""<div class="pm-card-dark">
                    <div style="font-size:0.75rem; color:#9A9CA3;">{seg['name']}</div>
                    <div style="font-size:0.9rem; font-weight:600; color:#EDEBE6;">
                        P5–P95: ₹{sp5/1e5:.1f}L – ₹{sp95/1e5:.1f}L
                    </div>
                    <div style="font-size:0.75rem; color:#9A9CA3;">
                        σ = {seg['sigma_pct']*100:.0f}% of base margin
                    </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        def receipts_output():
            st.markdown(f"""
| Parameter | Value |
|---|---|
| Simulations | 2,000 |
| Distribution | Normal, per-segment |
| Uncertainty parameterization | σ = segment-specific % of base margin |
| P5 | ₹{p5:,.0f} |
| P25 | ₹{p25:,.0f} |
| P50 (median) | ₹{p50:,.0f} |
| P75 | ₹{p75:,.0f} |
| P95 | ₹{p95:,.0f} |
| Pr(margin > current baseline) | {certainty_pct:.0f}% |
            """)

        receipts_expander(
            label_suffix="Monte Carlo simulation parameters",
            question="What distributional assumptions drive the confidence bands?",
            computation="""import numpy as np
rng = np.random.default_rng(42)
# Per-segment base margins from Block 6 optimal policy
# Uncertainty: normal(0, base * sigma_pct) — sigma_pct varies by segment
# Premium Loyalists: 25% (micro-segment, high uncertainty)
# Organic High-Intent: 5% (stable, predictable organic behavior)
# n_simulations = 2000
total_samples = sum(
    base + rng.normal(0, base * sigma_pct, 2000)
    for base, sigma_pct in segment_params
)""",
            output_md=receipts_output,
            insight=f"P50 margin of ₹{p50:,.0f} beats the current baseline with {certainty_pct:.0f}% probability across simulations. The policy is robust — but the Wallet Accumulators number (12% σ) drives most of the spread.",
        )

    continue_to("ch10", "The Decision")
    sim_footer()
