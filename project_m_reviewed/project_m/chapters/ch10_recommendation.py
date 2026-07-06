import streamlit as st
from ui_helpers import sim_footer, ACCENT, BADGES


ACTIONS = [
    {
        "verdict": "✅ Confirmed honest",
        "segment": "Pricing integrity",
        "action": "No adjustment needed",
        "rationale": "Wilcoxon test (p=0.34) found no price inflation signal. The cost is real — not a pass-through.",
        "color": "#3FA66B",
        "badge": "strong",
    },
    {
        "verdict": "📈 Increase +20%",
        "segment": "Wallet Accumulators (25.8%)",
        "action": "Concentrate incremental budget here",
        "rationale": "Only segment with verified causal responsiveness. Elasticity ε=1.65, saturation ceiling 28%. Expected margin improvement: +₹7.3L (+30.9%).",
        "color": "#3FA66B",
        "badge": "strong",
    },
    {
        "verdict": "📉 Reduce -20%",
        "segment": "Organic High-Intent Buyers (30.8%)",
        "action": "Trim — they convert without incentives",
        "rationale": "Low elasticity (ε=0.12). Cashback spend here is redundant. Reducing captures ₹42K in margin without measurable conversion impact.",
        "color": "#D4A24C",
        "badge": "moderate",
    },
    {
        "verdict": "🔒 Maintain",
        "segment": "Expiry-Driven Converters (12.1%)",
        "action": "Hold current allocation",
        "rationale": "Reducing risks non-linear GMV drop. Maintaining is the margin-safe choice pending a controlled test of reduction scenarios.",
        "color": "#7C8CA6",
        "badge": "moderate",
    },
    {
        "verdict": "📉 Reduce -20%",
        "segment": "Aggressive Expiry Converters (12.6%)",
        "action": "Cost-optimize — sharp response curve at lower bands",
        "rationale": "High session intensity but heavily cost-sensitive. Pulling back 20% yields the highest positive margin delta without drop-off risk.",
        "color": "#D4A24C",
        "badge": "moderate",
    },
    {
        "verdict": "🚫 Exclude",
        "segment": "Passive Expiry Converters (18.3%)",
        "action": "Stop spend — verified incentive trap",
        "rationale": "Negative causal lift (ε=−0.25). Collects cashback, doesn't convert. Exclusion saves full cashback cost with 94% of revenue retained.",
        "color": "#C4573F",
        "badge": "strong",
    },
    {
        "verdict": "🚫 Exclude",
        "segment": "Premium Full-Price Loyalists (0.45%)",
        "action": "Stop spend — micro-segment, zero dependency",
        "rationale": "4% redemption rate. Any cashback is direct revenue dilution. Exclusion is mathematically required — with 🔴 Exploratory caveat on micro-segment size.",
        "color": "#C4573F",
        "badge": "exploratory",
    },
]


def render(data, skim_mode):
    st.markdown("## Chapter 10 — Recommendations ")

    st.markdown(
        f"""
        <div class="pm-card-dark" style="border-left: 4px solid {ACCENT}; padding-left: 1.2rem;">
            <div style="font-size:0.8rem; color:#9A9CA3; margin-bottom:0.3rem;">THE DECISION</div>
            <div style="font-size:1.4rem; font-weight:700;">
                Stop treating all customers the same.
            </div>
            <div style="font-size:1rem; color:#B9BBC2; margin-top:0.5rem;">
                Expected impact: <span style="color:#3FA66B; font-weight:700;">+17.7% portfolio margin</span>
                · ₹15.6L incremental · validated across 2,000 Monte Carlo simulations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Recommendation memo — always visible ──────────────────────────────────
    st.markdown("### The policy, segment by segment")
    for action in ACTIONS:
        badge_label, badge_color = BADGES[action["badge"]]
        st.markdown(
            f"""<div class="pm-card-dark" style="border-left: 3px solid {action['color']}; padding-left: 1rem; margin-bottom:0.7rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:6px;">
                <div>
                    <span style="color:{action['color']}; font-weight:700; font-size:0.95rem;">{action['verdict']}</span>
                    &nbsp;·&nbsp;
                    <b>{action['segment']}</b>
                </div>
                <span style="background:{badge_color}22; color:{badge_color}; border:1px solid {badge_color};
                padding:2px 8px; border-radius:10px; font-size:0.7rem; font-weight:600;">{badge_label}</span>
            </div>
            <div style="color:#9A9CA3; font-size:0.82rem; margin-top:4px;"><b>Action:</b> {action['action']}</div>
            <div style="font-size:0.82rem; margin-top:2px;">{action['rationale']}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    if not skim_mode:
        st.markdown("---")
        # ── Limitations ───────────────────────────────────────────────────────
        st.markdown("### Limitations — stated plainly")
        limitations = [
            ("Simulated data", "All 2,000 customers are synthetic. The pipeline architecture and decision logic are real; the specific numbers are illustrative. No production inference should be drawn directly."),
            ("Micro-segment caution", "Premium Full-Price Loyalists (9 users, 0.45%) — the Exclude recommendation is directionally correct but statistically fragile. Population confirmation required before actioning."),
            ("Correlation vs. causation", "Only Wallet Accumulators have a defended causal claim (high response score × high redemption rate). All other segment recommendations are directionally supported but lack experimental validation."),
            ("Hunter Intent uncertainty", "The composite Hunter Intent Score is a screening layer, not a validated classifier. The 🟡 badge is honest — precision/recall was not measured against ground truth."),
            ("Elasticity constants", "ε and saturation ceiling values are set from behavioral inference, not from a controlled price experiment. The policy ladder math is defensible; the constants should be re-estimated on real data."),
        ]
        for title, body in limitations:
            with st.expander(f"**{title}**"):
                st.markdown(body)

        st.markdown("### The explicit next step")
        st.markdown(
            """
            > *Before production deployment, this policy needs a controlled A/B test — the same
            > discipline applied throughout this investigation should apply to rolling it out.*

            **Proposed test design:**
            - **Treatment arm:** Wallet Accumulators receive +20% cashback; Passive Expiry and Premium Loyalists excluded
            - **Control arm:** Current blanket policy, unchanged
            - **Primary metric:** Net margin per user over 4 weeks
            - **Secondary metrics:** Conversion rate, wallet redemption rate, session-to-purchase efficiency
            - **Minimum detectable effect:** 10% margin improvement at 80% power
            - **Holdout:** Retain 15% of Wallet Accumulators in control to validate the causal claim
            """
        )

    # ── Simulation disclaimer — final line, quiet ───────────────────────────
    st.markdown("---")
    st.markdown(
        '<div class="pm-footer">🔬 Simulated dataset — 2,000 synthetic customer journeys. '
        'Not real transaction data. All figures are illustrative. '
        'Full investigation in Chapter 11.</div>',
        unsafe_allow_html=True,
    )

    # No "next chapter" — back to beginning or SQL index
    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("← Back to the beginning", use_container_width=True):
            st.session_state.chapter = "ch0"
            st.rerun()
    with b2:
        if st.button("View full SQL investigation →", use_container_width=True):
            st.session_state.chapter = "ch11"
            st.rerun()
