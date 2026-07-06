import streamlit as st
from ui_helpers import question_answer, receipts_expander, how_this_was_built, sim_footer, continue_to, ACCENT


def render(data, skim_mode):
    st.markdown("## Chapter 7.5 — Hunter Intent: Who's Actually Gaming the Incentive")

    question_answer(
        question="Beyond broad segments, who is specifically engineering their behavior for maximum reward?",
        answer="A cross-cutting Hunter Intent layer identifies a sharper group optimizing redemption timing — and it doesn't map cleanly onto the macro segments above.",
        badge_level="moderate",
    )

    hunter_df = data["hunter_summary"]

    # Compact default: 3-way split
    st.markdown("#### Classification breakdown")
    cols = st.columns(3)
    colors = {"Active Hunter": "#C4573F", "Normal User": "#3FA66B", "Passive Expirer": "#7C8CA6"}
    icons = {"Active Hunter": "🎯", "Normal User": "👤", "Passive Expirer": "😴"}

    for col, (_, row) in zip(cols, hunter_df.iterrows()):
        utype = row["user_type"]
        color = colors.get(utype, ACCENT)
        icon = icons.get(utype, "")
        with col:
            st.markdown(
                f"""<div class="pm-card-dark" style="text-align:center;">
                <div style="font-size:1.5rem;">{icon}</div>
                <div style="font-size:0.85rem; font-weight:700; color:{color}; margin:4px 0;">{utype}</div>
                <div class="pm-metric-big">{int(row['user_count']):,}</div>
                <div style="font-size:0.78rem; color:#9A9CA3;">users identified</div>
                <div style="font-size:0.82rem; margin-top:8px; color:#EDEBE6;">
                    Avg expiry dep: {row['avg_expiry_dependency']:.3f}<br>
                    Avg wallet monitoring: {row['avg_wallet_monitoring_frequency']:.1f}x/week
                </div>
                </div>""",
                unsafe_allow_html=True,
            )

    total_hunters = int(hunter_df[hunter_df["user_type"] == "Active Hunter"]["user_count"].iloc[0])
    total_users = int(hunter_df["user_count"].sum())
    hunter_pct = total_hunters / total_users * 100

    st.markdown(
        f"""<div class="pm-card-dark" style="margin-top:1rem;">
        <b>Active Hunters represent {hunter_pct:.1f}% of the platform</b> — but their behavioral
        fingerprint (high expiry dependency score ≥ 0.70, wallet monitoring ≥ 5x/week, redemption
        within 1.5 days of expiry) makes them disproportionately expensive to serve relative to
        incremental value generated.
        </div>""",
        unsafe_allow_html=True,
    )

    if not skim_mode:
        st.markdown("---")
        st.markdown("#### The cross-segment tension")
        st.info(
            "**Key finding:** Hunter Intent is not a segment — it's a behavior layer that cuts across segments.\n\n"
            "Most Active Hunters (~78% probability) sit inside **Wallet Accumulators** — the same segment "
            "that Chapter 8 recommends for a +20% budget increase. This is the honest complication: "
            "the highest-elasticity segment also has the highest hunter concentration.\n\n"
            "The resolution: Wallet Accumulators' *causal* responsiveness (verified in Ch. 8) still "
            "outweighs the gaming risk at the aggregate level. But this is the signal that warrants "
            "holdout testing before full deployment."
        )

        # Hunter score construction
        st.markdown("#### Hunter Intent Score construction")
        weight_cols = st.columns(4)
        weights = [
            ("Expiry Dependency Score", "0.35", "Primary signal — how reliant is the user on expiry pressure to convert?"),
            ("Session Intensity", "0.25", "Volume of sessions — hunters monitor the platform actively"),
            ("Wallet Monitoring Frequency", "0.20", "Direct proxy for strategic wallet management behavior"),
            ("1 − Expiry Cycles (inverted)", "0.20", "Fewer lifetime expiry misses = more intentional behavior"),
        ]
        for col, (feature, weight, desc) in zip(weight_cols, weights):
            with col:
                st.markdown(
                    f"""<div class="pm-card-dark" style="text-align:center;">
                    <div style="font-size:1.2rem; font-weight:700; color:{ACCENT};">{weight}</div>
                    <div style="font-size:0.78rem; font-weight:600;">{feature}</div>
                    <div style="font-size:0.72rem; color:#9A9CA3; margin-top:4px;">{desc}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        st.markdown("**Classification thresholds:**")
        st.markdown(
            "- **Active Hunter**: score ≥ 0.62 AND wallet_monitoring_frequency ≥ 5\n"
            "- **Passive Expirer**: score < 0.28 AND session_intensity ≤ 2\n"
            "- **Normal User**: everything else"
        )

        def receipts_output():
            st.dataframe(hunter_df.rename(columns={
                "user_type": "User Type",
                "user_count": "Count",
                "total_revenue_rs": "Total Revenue (₹)",
                "total_cashback_cost_rs": "Total CB Cost (₹)",
                "net_margin_rs": "Net Margin (₹)",
                "avg_expiry_dependency": "Avg Expiry Dep",
                "avg_wallet_monitoring_frequency": "Avg Wallet Monitoring",
            }), use_container_width=True)

        receipts_expander(
            label_suffix="Hunter Intent classification pipeline",
            question="How was the composite Hunter Intent score built and how were thresholds determined?",
            computation="""WITH Normalized_Intent_Scoring AS (
    SELECT m.*,
        (expiry_dependency_score - min_exp) / NULLIF(max_exp - min_exp, 0) AS norm_expiry_dep,
        (session_intensity - min_sess)      / NULLIF(max_sess - min_sess, 0) AS norm_session_int,
        (wallet_monitoring_frequency - min_wmon) / NULLIF(max_wmon - min_wmon, 0) AS norm_wallet,
        (lifetime_expiry_cycles - min_cyc)  / NULLIF(max_cyc - min_cyc, 0) AS norm_cycles
    FROM Master_Enriched_Pipeline CROSS JOIN Statistical_Bounds
),
Calculated_Hunter_Index AS (
    SELECT *,
        (0.35 * norm_expiry_dep + 0.25 * norm_session_int +
         0.20 * norm_wallet + 0.20 * (1.0 - norm_cycles)) AS hunter_intent_score
    FROM Normalized_Intent_Scoring
)
SELECT user_type, COUNT(*), AVG(expiry_dependency_score), AVG(wallet_monitoring_frequency)
FROM Strategic_Classification GROUP BY 1;""",
            output_md=receipts_output,
            insight=f"{total_hunters:,} Active Hunters ({hunter_pct:.1f}%) identified. Score is a composite index — not a causal test. Label: 🟡 Moderate evidence. The weighting is defensible but not experimentally validated.",
        )

        def how_built():
            st.markdown("""
**Pipeline:** DuckDB SQL — the entire Hunter Intent classification runs as a multi-CTE SQL
query against in-memory DataFrames. No model training, no ground-truth labels required.

**Cross-segment design:** Hunter Intent was intentionally built *after* segmentation (Block 3.5)
and uses segment-agnostic behavioral signals. The resulting distribution cuts across all 6
macro segments, confirming it captures something the clustering didn't absorb.

**Composite index limitations:**
- Weights (0.35 / 0.25 / 0.20 / 0.20) are directionally motivated but not optimized
- No A/B holdout to validate that "Active Hunters" actually game the system more than predicted
- The 🟡 Moderate badge is honest — this is a screening layer, not a classifier with a verified precision/recall curve

**Code reference:** `Hunter_Intent_Classification.py` — Block 3.5
            """)

        how_this_was_built("Hunter Intent Score construction", how_built)

    continue_to("ch8", "The Optimization Engine")
    sim_footer()
