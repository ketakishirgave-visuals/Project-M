import numpy as np
import streamlit as st
from ui_helpers import (
    question_answer, receipts_expander, how_this_was_built,
    sim_footer, continue_to, confidence_badge, ACCENT, evidence_used
)

# Cohort metadata mirrors Block 6 exactly
COHORT_META = {
    0: {"name": "Expiry-Driven Converters",    "elasticity": 0.85,  "saturation": 0.12, "actions": ["Reduce -20%", "Reduce -10%", "Maintain"], "optimal": "Maintain",     "causal": "moderate"},
    1: {"name": "Organic High-Intent Buyers",   "elasticity": 0.12,  "saturation": 0.04, "actions": ["Reduce -20%", "Reduce -10%", "Maintain"], "optimal": "Reduce -20%",  "causal": "moderate"},
    2: {"name": "Wallet Accumulators",          "elasticity": 1.65,  "saturation": 0.28, "actions": ["Maintain", "Increase +10%", "Increase +20%"], "optimal": "Increase +20%","causal": "strong"},
    3: {"name": "Passive Expiry Converters",    "elasticity": -0.25, "saturation": 0.02, "actions": ["Exclude"],                                "optimal": "Exclude",      "causal": "strong"},
    4: {"name": "Aggressive Expiry Converters", "elasticity": 0.55,  "saturation": 0.08, "actions": ["Reduce -20%", "Reduce -10%", "Maintain"], "optimal": "Reduce -20%",  "causal": "moderate"},
    5: {"name": "Premium Full-Price Loyalists", "elasticity": 0.00,  "saturation": 0.00, "actions": ["Exclude"],                                "optimal": "Exclude",      "causal": "exploratory"},
}

POLICY_DELTAS = {
    "Exclude": -1.0, "Reduce -20%": -0.2, "Reduce -10%": -0.1,
    "Maintain": 0.0, "Increase +10%": 0.1, "Increase +20%": 0.2,
}

BADGE_HTML = {
    "strong":      '<span style="background:#3FA66B22; color:#3FA66B; border:1px solid #3FA66B; padding:2px 8px; border-radius:10px; font-size:0.7rem; font-weight:600;">✅ Causally verified</span>',
    "moderate":    '<span style="background:#D4A24C22; color:#D4A24C; border:1px solid #D4A24C; padding:2px 8px; border-radius:10px; font-size:0.7rem; font-weight:600;">🟡 Moderate evidence</span>',
    "exploratory": '<span style="background:#C4573F22; color:#C4573F; border:1px solid #C4573F; padding:2px 8px; border-radius:10px; font-size:0.7rem; font-weight:600;">🔴 Exploratory only</span>',
}

def compute_margin(seg_id, action, base_rev, base_cost, base_margin):
    meta = COHORT_META[seg_id]
    di = POLICY_DELTAS[action]
    if action == "Exclude":
        rev = base_rev if seg_id == 5 else base_rev * 0.94
        cost = 0.0
    else:
        epsilon = meta["elasticity"]
        ceiling = meta["saturation"]
        revenue_shock = np.sign(di) * min(ceiling, abs(np.log1p(di * epsilon)))
        rev = base_rev * (1.0 + revenue_shock)
        cost = base_cost * (1.0 + di)
    margin = rev - cost
    delta = margin - base_margin
    return rev, cost, margin, delta


def render(data, skim_mode):
    st.markdown("## Chapter 8 — The Optimization Engine")

    question_answer(
        question="Given everything we know, what's the actual policy — and can we trust it?",
        answer="Concentrate budget on Wallet Accumulators, trim moderate segments, cut two entirely — a 17.7% portfolio margin uplift.",
        badge_level="strong",
    )

    evidence_used(["SQL Block 4", "SQL Block 8"], key="ch08_top")

    # ── Portfolio summary card — always visible ──────────────────────────────
    st.markdown("#### Portfolio impact: current → optimized")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f'<div class="pm-card-dark"><div style="font-size:0.8rem; color:#9A9CA3;">Current Portfolio Profit</div>'
            f'<div class="pm-metric-big">₹88L</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="pm-card-dark"><div style="font-size:0.8rem; color:#9A9CA3;">Optimized Portfolio Profit</div>'
            f'<div class="pm-metric-big" style="color:#3FA66B;">₹103.6L</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="pm-card-dark"><div style="font-size:0.8rem; color:#9A9CA3;">Simulated Uplift</div>'
            f'<div class="pm-metric-big" style="color:{ACCENT};">+17.7%</div>'
            f'<div style="font-size:0.75rem; color:#9A9CA3;">₹15.6L incremental margin</div></div>',
            unsafe_allow_html=True,
        )

    # Per-segment causal badges — always visible
    st.markdown("#### Policy action per segment + causal evidence")
    seg_cols = st.columns(6)
    action_colors = {"Increase": "#3FA66B", "Maintain": "#7C8CA6", "Reduce": "#D4A24C", "Exclude": "#C4573F"}
    for seg_id, col in enumerate(seg_cols):
        meta = COHORT_META[seg_id]
        action_word = meta["optimal"].split(" ")[0]
        acolor = action_colors.get(action_word, "#7C8CA6")
        with col:
            st.markdown(
                f"""<div class="pm-card-dark" style="text-align:center; padding:0.6rem 0.4rem;">
                <div style="font-size:0.72rem; color:#9A9CA3;">{meta['name'].split()[0]} {meta['name'].split()[1] if len(meta['name'].split()) > 1 else ''}</div>
                <div style="font-size:0.78rem; font-weight:700; color:{acolor}; margin:4px 0;">{meta['optimal']}</div>
                {BADGE_HTML[meta['causal']]}
                </div>""",
                unsafe_allow_html=True,
            )

    if not skim_mode:
        st.markdown("---")
        # ── Live Policy Simulator ────────────────────────────────────────────
        with st.expander("🎛 Try it yourself — Policy Simulator", expanded=False):
            st.markdown(
                "**Adjust the policy for each segment and see the margin impact cascade in real time.**  \n"
                "Defaults are set to the engine's optimal recommendations. Change any to see what you'd lose or gain."
            )
            st.caption("🔬 Simulation only — directional estimates based on observed elasticity and saturation ceilings.")

            pol_mat = data["policy_matrix"]
            base_rows = {}
            for seg_id in range(6):
                seg_rows = pol_mat[pol_mat["segment_id"] == seg_id]
                maintain_rows = seg_rows[seg_rows["policy"] == "Maintain"]
                if not maintain_rows.empty:
                    r = maintain_rows.iloc[0]
                else:
                    r = seg_rows.iloc[0]
                base_rows[seg_id] = {
                    "base_rev": r["expected_revenue"],
                    "base_cost": r["expected_cashback_cost"],
                    "base_margin": r["expected_margin"],
                }

            total_base = sum(b["base_margin"] for b in base_rows.values())
            selected_policies = {}

            sim_cols = st.columns(2)
            for i, seg_id in enumerate(range(6)):
                meta = COHORT_META[seg_id]
                with sim_cols[i % 2]:
                    selected = st.selectbox(
                        f"**{meta['name']}**",
                        options=meta["actions"],
                        index=meta["actions"].index(meta["optimal"]),
                        key=f"sim_policy_{seg_id}",
                    )
                    selected_policies[seg_id] = selected

            # Compute cascaded results
            st.markdown("---")
            st.markdown("##### Margin cascade")
            total_sim_margin = 0
            for seg_id in range(6):
                base = base_rows[seg_id]
                action = selected_policies[seg_id]
                _, _, sim_margin, delta = compute_margin(
                    seg_id, action, base["base_rev"], base["base_cost"], base["base_margin"]
                )
                total_sim_margin += sim_margin
                is_optimal = action == COHORT_META[seg_id]["optimal"]
                status = "✅ Matches optimal" if is_optimal else "⚠️ Deviates from optimal"
                delta_color = "#3FA66B" if delta >= 0 else "#C4573F"
                st.markdown(
                    f"**{COHORT_META[seg_id]['name']}** — _{action}_ | "
                    f"Margin Δ: <span style='color:{delta_color};font-weight:700;'>₹{delta:+,.0f}</span> | {status}",
                    unsafe_allow_html=True,
                )

            uplift = (total_sim_margin - total_base) / total_base * 100
            uplift_color = "#3FA66B" if uplift >= 0 else "#C4573F"
            st.markdown("---")
            st.markdown(
                f"**Simulated portfolio margin:** ₹{total_sim_margin:,.0f}  |  "
                f"Uplift vs. baseline: <span style='color:{uplift_color}; font-size:1.1rem; font-weight:700;'>{uplift:+.1f}%</span>",
                unsafe_allow_html=True,
            )
            if uplift < 15:
                st.warning("Below the engine's optimal 17.7%. Try restoring the recommended actions above.")
            elif uplift >= 17:
                st.success("Matches or exceeds the engine's optimal policy. Ready to take forward for A/B validation.")

        # ── Receipts ────────────────────────────────────────────────────────
        def receipts_output():
            st.dataframe(data["strategy_matrix"][[
                "cohort_persona_name", "mathematical_quadrant",
                "recommended_budget_trajectory", "observed_cashback_response_score", "margin_efficiency_ratio"
            ]].rename(columns={
                "cohort_persona_name": "Segment",
                "mathematical_quadrant": "Quadrant",
                "recommended_budget_trajectory": "Budget Action",
                "observed_cashback_response_score": "Response Score",
                "margin_efficiency_ratio": "MER",
            }), use_container_width=True)

        receipts_expander(
            label_suffix="segment strategy matrix & policy ladder math",
            question="What are the full elasticity inputs, response scores, and margin efficiency ratios behind each policy recommendation?",
            computation="""# From: Cashback_Optimization.py — Block 6, Phase 1

# Revenue shock model — concave function prevents infinite budget recommendations
for p in policy_ladder:
    if p["action_tag"] not in meta["allowed_actions"]:
        continue

    di = p["delta_i"]

    if p["action_tag"] == "Exclude":
        rev  = base_rev * 0.94   # 6% GMV loss modeled on exclusion
        cost = 0.0
    else:
        epsilon  = meta["elasticity"]
        ceiling  = meta["saturation_ceiling"]
        # log1p gives diminishing returns — spending 2x doesn't buy 2x conversion
        revenue_shock = np.sign(di) * min(ceiling, abs(np.log1p(di * epsilon)))
        rev  = base_rev  * (1.0 + revenue_shock)
        cost = base_cost * (1.0 + di)

    margin       = rev - cost
    delta_margin = margin - base_margin

# Optimal policy: strictly maximum contribution margin across all allowed actions
optimal_scenario = max(segment_scenarios, key=lambda x: x["margin"])""",
            output_md=receipts_output,
            insight="Wallet Accumulators are the only segment with verified causal responsiveness (high response score + high redemption rate). All other Increase/Reduce calls are directionally supported but not causally proven — hence mixed confidence badges.",
        )

        def how_built():
            st.markdown("""
**Elasticity model:**  
Each segment has a hardened elasticity coefficient (ε) and saturation ceiling. Revenue shock
is computed as: `sign(Δi) × min(ceiling, |log1p(Δi × ε)|)`.
This is a concave function — it diminishes returns as investment increases, preventing the optimizer
from recommending infinite budget increases.

**Margin Efficiency Ratio (MER):**  
Net margin / cashback cost. The median MER of the active core pool (segments 0–4) serves as the
hurdle rate. Segments below the 50th percentile MER get reduction/exclusion signals.

**Constrained action space:**  
Each segment has an allowed action set — a segment can't be "increased" if it has negative
responsiveness. The optimizer picks the action with the highest resulting margin from within
the allowed set.

**Code reference:** `Cashback_Optimization.py` — Block 6
            """)

        how_this_was_built("constrained elasticity optimizer", how_built)

    continue_to("ch9", "Confidence & Range")
    sim_footer()
