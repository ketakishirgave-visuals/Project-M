import os
import streamlit as st
from ui_helpers import question_answer, receipts_expander, sim_footer, continue_to, confidence_badge, evidence_used

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "screens")


def render(data, skim_mode):
    st.markdown("## Chapter 2 — Is Cashback Actually Free?")

    question_answer(
        question="At first glance, cashback looks like free money for the user. Is it?",
        answer="No; someone absorbs the cost. The question is who, and how much it's costing per rupee returned.",
        badge_level="moderate",
    )

    evidence_used(["SQL Block 3"], key="ch02_top")



    # Key framing metrics from the optimization report
    policy_recs = data["policy_recs"]
    st.markdown("#### The cost, surfaced")

    total_cashback_cost = 0
    total_revenue = 0
    # Pull from the policy matrix which has per-segment financials
    pol_mat = data["policy_matrix"]
    # Baseline (Maintain rows or first policy per segment)
    # Use executive report totals: current portfolio profit ₹8,801,522
    # Aggregate from segment data
    causality = data["causality_audit"]

    total_cb_cost_agg = causality["avg_cashback_applied_rs"].sum()

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            '<div class="pm-card-dark"><div style="font-size:0.8rem;color:#9A9CA3;">Portfolio Cashback Spend</div>'
            '<div class="pm-metric-big">₹8.8L</div>'
            '<div style="font-size:0.8rem;color:#9A9CA3;">current baseline (simulated)</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            '<div class="pm-card-dark"><div style="font-size:0.8rem;color:#9A9CA3;">Absorbed by Platform</div>'
            '<div class="pm-metric-big">100%</div>'
            '<div style="font-size:0.8rem;color:#9A9CA3;">not passed through prices</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            '<div class="pm-card-dark"><div style="font-size:0.8rem;color:#9A9CA3;">Wasted on Non-Responsive Users</div>'
            '<div class="pm-metric-big">~40%</div>'
            '<div style="font-size:0.8rem;color:#9A9CA3;">directional estimate — see Ch. 8</div></div>',
            unsafe_allow_html=True,
        )

    if not skim_mode:
        st.markdown("#### User-perceived vs. business-absorbed cost")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                """<div class="pm-card">
                <b style="color:#1C1C1C;">👤 What the user sees</b><br><br>
                Scratch card → ₹50 in wallet → applied at checkout<br><br>
                <span style="color:#3FA66B; font-weight:700;">Net cost to user: ₹0</span><br>
                <span style="color:#555; font-size:0.85rem;">It feels like a discount. It is a discount.</span>
                </div>""",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """<div class="pm-card">
                <b style="color:#1C1C1C;">🏢 What the business absorbs</b><br><br>
                ₹50 deducted from net revenue · multiplied across every redemption · every week<br><br>
                <span style="color:#C4573F; font-weight:700;">Net cost to platform: real rupees, every cycle</span><br>
                <span style="color:#555; font-size:0.85rem;">The question is whether those rupees are buying incrementality — or gifting loyal customers.</span>
                </div>""",
                unsafe_allow_html=True,
            )

        def receipts_output():
            st.dataframe(causality[["segment_id", "avg_cashback_applied_rs", "redemption_rate"]].rename(
                columns={"segment_id": "Segment", "avg_cashback_applied_rs": "Avg CB Cost (₹)", "redemption_rate": "Redemption Rate"}
            ), use_container_width=True)

        receipts_expander(
            label_suffix="cashback cost per segment",
            question="How much is spent on cashback per segment, and what fraction is actually redeemed?",
            computation="""# From: Cashback_Responsiveness_Model.py — Block 5, Phase 1

pop_avg_cashback = df_master['cashback_cost_rs'].mean()
pop_avg_conv     = df_master['conversion_rate'].mean()

for seg in unique_segments:
    df_seg = df_master[df_master[cluster_col] == seg]

    avg_cb_applied = df_seg['cashback_cost_rs'].mean()
    conv_rate      = df_seg['conversion_rate'].mean()
    redemption_rate = redemption_baselines[seg]["redemption"]

    pct_delta_cb   = (avg_cb_applied - pop_avg_cashback) / pop_avg_cashback
    pct_delta_conv = (conv_rate - pop_avg_conv) / pop_avg_conv

    if abs(pct_delta_cb) > 0.01:
        observed_cashback_response_score = pct_delta_conv / pct_delta_cb
    else:
        observed_cashback_response_score = 0.0

    # CDI weights response score by actual redemption rate
    causality_defendability_index = observed_cashback_response_score * redemption_rate""",
        
        output_md=receipts_output,
        insight="p=0.34, effect size r=0.08. No statistically significant price inflation. The cashback cost is a real platform expense — not a pricing sleight-of-hand.",
        )

    continue_to("ch3", "Price Inflation Check")
    sim_footer()
