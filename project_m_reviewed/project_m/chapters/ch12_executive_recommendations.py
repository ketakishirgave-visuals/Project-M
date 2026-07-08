import streamlit as st
from ui_helpers import sim_footer, ACCENT, confidence_badge

RECOMMENDATIONS = [
    {
        "title": "Prioritize Wallet Accumulators for incremental cashback budget",
        "body": "This is the only segment with a verified causal responsiveness signal (high response score × high redemption rate — Ch. 8) and the highest observed elasticity of the six segments. The optimization engine's +20% allocation is the segment-specific policy this evidence supports.",
        "evidence": "SQL Block 4 (efficiency bands) · Ch. 8 causality audit",
        "badge": "strong",
    },
    {
        "title": "Reduce cashback allocation to Organic High-Intent Buyers",
        "body": "This segment shows the highest profit per ₹1 of cashback (₹11.16, Block 3) and holds that lead across every tenure cohort (Block 9) without cashback support — its low elasticity (Ch. 8, ε=0.12) indicates cashback here is largely redundant spend rather than a driver of the observed profit.",
        "evidence": "SQL Block 3, Block 9 · Ch. 8 elasticity",
        "badge": "strong",
    },
    {
        "title": "Do not increase cashback beyond the first efficiency band for any segment",
        "body": "Marginal purchase frequency shows no measurable increase past the first cashback band in any of the six segments (Block 4). Additional cashback above this threshold has no observed frequency return in this dataset.",
        "evidence": "SQL Block 4",
        "badge": "strong",
    },
    {
        "title": "Exclude Passive Expiry Converters from active cashback distribution",
        "body": "This segment combines negative measured causal lift (Ch. 8) with cashback collection that is not converted to purchases. Continuing allocation here funds redemption behavior with no observed offsetting revenue.",
        "evidence": "SQL Block 0, Block 6 · Ch. 8 causality audit",
        "badge": "strong",
    },
    {
        "title": "Reduce allocation to Aggressive Expiry Converters by −20%",
        "body": "This segment shows the highest deliberate-expiry rate of the six segments (12.82%, Block 6) and the lowest profit per ₹1 of cashback (₹3.19–3.4 depending on tier, Blocks 3 and 9). Deliberate expiry behavior here indicates cashback is being actively managed by the customer rather than driving incremental purchases.",
        "evidence": "SQL Block 3, Block 6, Block 9",
        "badge": "moderate",
    },
    {
        "title": "Treat the Premium Full-Price Loyalists exclusion as provisional, pending a larger sample",
        "body": "This segment (9 users, 0.45% of the base) shows near-zero cashback dependence, which supports exclusion directionally. Because of the small sample, the specific magnitude of this recommendation should be re-validated once more users are observed in this cohort rather than treated as a fixed policy.",
        "evidence": "SQL Block 1, Block 3 · segment population confidence report",
        "badge": "exploratory",
    },
    {
        "title": "Segment the top 10% cashback consumers and apply divergent policies",
        "body": "The top 10% of cashback consumers (17.3% of total spend, 9.3% of profit) breaks into two distinct groups: 85.5% are Expiry-Driven Converters (elasticity 0.85, ₹5.04 profit/₹1): These users ARE responsive to cashback and drive repeat purchases through timing sensitivity. Policy: MAINTAIN or INCREASE by +10%. 14.0% are Aggressive Expiry Converters (elasticity 0.55, 12.82% leakage, ₹3.19 profit/₹1): These are hunters with low responsiveness and high deliberate-expiry behavior. Policy: REDUCE by −20%. Do not apply a blanket reduction to the top 10%.",
        "evidence": "SQL Block 7",
        "badge": "moderate",
    },
    {
        "title": "Investigate purchase timing before adjusting reward size further",
        "body": "Wallet balance shows little linear relationship with basket size in any segment (|r| < 0.18, Block 8), while purchase timing does shift measurably near the expiry window (Block 5) and after a wallet peak (Block 10). This indicates timing, not reward size, is the lever most supported by the data — retention or messaging experiments aimed at timing are better supported by current evidence than further reward-size changes.",
        "evidence": "SQL Block 5, Block 8, Block 10",
        "badge": "moderate",
    },
]


def render(data, skim_mode):
    st.markdown("## Chapter 12 — Executive Recommendations")

    st.markdown(
        f"""
        <div class="pm-card-dark" style="border-left: 4px solid {ACCENT}; padding-left: 1.2rem;">
            <div style="font-size:0.8rem; color:#9A9CA3; margin-bottom:0.3rem;">SUMMARY</div>
            <div style="font-size:1.05rem; color:#EDEBE6;">
            Eight recommendations below, each traced to a specific SQL block or causality-audit result
            covered in Chapters 8–11. None extend beyond what those results measure — where evidence
            is directional rather than causally verified, the confidence badge reflects that.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    for i, rec in enumerate(RECOMMENDATIONS, start=1):
        badge_html = confidence_badge(rec["badge"])
        st.markdown(
            f"""
            <div class="pm-card-dark" style="margin-bottom:0.8rem;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px; flex-wrap:wrap;">
                    <div style="font-size:1rem; font-weight:700; color:#EDEBE6;">{i}. {rec['title']}</div>
                    {badge_html}
                </div>
                <div style="font-size:0.9rem; color:#B9BBC2; margin-top:6px;">{rec['body']}</div>
                <div style="font-size:0.74rem; color:{ACCENT}; margin-top:8px;">🧾 Evidence: {rec['evidence']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not skim_mode:
        st.markdown("---")
        st.info(
            "**On scope:** these recommendations are drawn entirely from the simulated dataset's SQL outputs "
            "and the causality audit in Chapter 8. They describe what the pipeline found in this synthetic run, "
            "and are a template for the analysis a production deployment would need to repeat on real data — "
            "not a standalone business decision."
        )

    st.markdown("---")
    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("← Back to SQL Investigation", use_container_width=True):
            st.session_state.chapter = "ch11"
            st.rerun()
    with b2:
        if st.button("↩ Back to the beginning", use_container_width=True):
            st.session_state.chapter = "ch0"
            st.rerun()

    sim_footer()
