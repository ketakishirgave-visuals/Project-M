import streamlit as st
from ui_helpers import (
    question_answer, receipts_expander, how_this_was_built,
    sim_footer, continue_to, action_tag_color, ACCENT, evidence_used
)

ACTION_TAG_COLORS = {
    "Invest": "#3FA66B",
    "Reduce": "#D4A24C",
    "Exclude": "#C4573F",
    "Maintain": "#7C8CA6",
}

SEGMENT_CONFIDENCE = {
    0: "strong", 1: "strong", 2: "strong",
    3: "strong", 4: "strong", 5: "exploratory",
}

BADGE_LABELS = {
    "strong": ("✅", "#3FA66B"),
    "exploratory": ("🔴", "#C4573F"),
}


def render(data, skim_mode):
    st.markdown("## Chapter 7 — Segmentation: Six Behavioral Profiles")

    question_answer(
        question="When you group customers by behavior alone, what natural patterns emerge?",
        answer="Six distinct, statistically stable segments — from highly organic buyers to a segment actively costing the business money.",
        badge_level="strong",
    )

    evidence_used(["SQL Block 4", "SQL Block 0"], key="ch07_top")

    pop_conf = data["pop_confidence"]
    profiles = data["cluster_profiles"]
    persona_names = data["persona_names"]
    persona_action = data["persona_action_tag"]
    persona_one_liner = data["persona_one_liner"]

    # Compact strip — always visible
    st.markdown("#### Six segments at a glance")
    cols = st.columns(6)
    for seg_id in range(6):
        conf_row = pop_conf[pop_conf["segment_id"] == seg_id].iloc[0]
        action = persona_action[seg_id]
        action_color = ACTION_TAG_COLORS[action]
        conf_level = SEGMENT_CONFIDENCE[seg_id]
        conf_icon, conf_color = BADGE_LABELS[conf_level]
        with cols[seg_id]:
            st.markdown(
                f"""<div class="pm-card-dark" style="text-align:center; padding:0.8rem 0.5rem;">
                <div style="font-size:0.72rem; color:#9A9CA3; margin-bottom:4px;">Segment {seg_id}</div>
                <div style="font-size:0.78rem; font-weight:700; color:#EDEBE6; min-height:48px;">{persona_names[seg_id]}</div>
                <div style="margin:6px 0;">
                    <span style="background:{action_color}22; color:{action_color};
                    border:1px solid {action_color}; border-radius:10px;
                    padding:2px 8px; font-size:0.7rem; font-weight:700;">{action}</span>
                </div>
                <div style="font-size:0.8rem; color:{ACCENT}; font-weight:600;">
                    {conf_row['population_share']*100:.1f}%
                </div>
                <div style="font-size:0.7rem; color:#9A9CA3;">{int(conf_row['population_count'])} users</div>
                <div style="font-size:0.75rem; margin-top:4px;">{conf_icon}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    if not skim_mode:
        st.markdown("---")
        st.markdown("#### Full segment profiles")
        st.caption("Expand any segment for behavioral signature, validation status, and evidence.")
        for seg_id in range(6):
            conf_row = pop_conf[pop_conf["segment_id"] == seg_id].iloc[0]
            action = persona_action[seg_id]
            action_color = ACTION_TAG_COLORS[action]
            conf_level = SEGMENT_CONFIDENCE[seg_id]
            conf_icon, conf_color = BADGE_LABELS[conf_level]
            name = persona_names[seg_id]
            profile_key = f"production_segment_{seg_id}"
            profile = profiles.get(profile_key, {})
            signals = profile.get("layer_1_statistical_signature", [])
            behaviors = profile.get("layer_2_behavioral_translation", [])

            with st.expander(
                f"**{name}** — {conf_row['population_share']*100:.1f}% · "
                f"_{action}_ {conf_icon}",
                expanded=False,
            ):
                left, right = st.columns([3, 2])
                with left:
                    st.markdown(f"**One-liner:** {persona_one_liner[seg_id]}")
                    st.markdown("**Behavioral signals:**")
                    for b in behaviors[:5]:
                        st.markdown(f"- {b}")
                with right:
                    st.markdown(
                        f"""<div class="pm-card">
                        <b>Population</b><br>
                        {int(conf_row['population_count'])} users ({conf_row['population_share']*100:.1f}%)<br><br>
                        <b>Validation</b><br>
                        {conf_row['statistical_status']}<br><br>
                        <b>Policy action</b><br>
                        <span style="color:{action_color}; font-weight:700;">{action}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                if seg_id == 5:
                    st.warning(
                        "🔴 **Exploratory only** — 9 users (0.45%). This micro-segment was identified "
                        "and merged from an initial 7-cluster solution. Policy recommendations for this "
                        "cohort carry higher uncertainty than the remaining five stable segments."
                    )

        st.markdown("---")
        # Cluster validation metrics
        val = data["cluster_validation"].iloc[0]
        st.markdown("#### Cluster quality metrics")
        m1, m2, m3 = st.columns(3)
        metrics = [
            (m1, "Silhouette Score", f"{val['silhouette_score']:.4f}", "0.18 — moderate separation. Realistic given the 36% intentional behavioral overlap."),
            (m2, "Davies-Bouldin Index", f"{val['davies_bouldin_index']:.4f}", "Lower is better. 1.63 is within acceptable range for overlapping behavioral data."),
            (m3, "Calinski-Harabasz Score", f"{val['calinski_harabasz_score']:.1f}", "Higher is better. 602 indicates meaningful cluster compactness relative to separation."),
        ]
        for col, name, value, note in metrics:
            with col:
                st.metric(name, value)
                st.caption(note)

        def receipts_output():
            st.dataframe(data["cluster_validation"], use_container_width=True)
            st.markdown("**Stability across 4 random seeds:**")
            stability_pivot = data["cluster_stability"].groupby("segment_id")["recorded_population_count"].agg(["mean", "std"]).round(1).reset_index()
            stability_pivot.columns = ["Segment", "Mean Population", "Std Dev"]
            st.dataframe(stability_pivot, use_container_width=True)

        receipts_expander(
            label_suffix="segmentation validation",
            question="Are the 6 clusters statistically stable or sensitive to random initialization?",
            computation="""-- GMM fit with quality evaluation
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

gmm = GaussianMixture(n_components=7, random_state=42, n_init=5).fit(X_scaled)
labels = gmm.predict(X_scaled)
# Cluster 6 (9 users, 0.45%) merged into Cluster 3 — formal_production_verdict.json
# Stability: re-run across seeds [10, 42, 101, 2026]""",
            output_md=receipts_output,
            insight=f"Silhouette={val['silhouette_score']:.3f}, DB={val['davies_bouldin_index']:.3f}, CH={val['calinski_harabasz_score']:.0f}. Moderate but consistent quality — the overlap is designed in (36% borderline zone), not a modeling failure.",
        )

        def how_built():
            st.markdown("""
**Algorithm:** Gaussian Mixture Model (GMM) with 7 initial components.
GMM was preferred over K-Means because the behavioral feature distributions are not spherical —
GMM's covariance flexibility handles the elongated cluster shapes in j_curve / wallet_slope space.

**Cluster consolidation:** Initial 7-cluster solution found one micro-cluster of 9 users (0.45%)
showing near-complete behavioral overlap with Cluster 3. Merged programmatically with a formal
audit record written to `formal_production_verdict.json`. This is not a silent drop — it's a
documented decision with justification.

**Stability validation:** Re-run across 4 random seeds (10, 42, 101, 2026). Population counts
are stable to within ±15 users per segment, confirming the solution is not initialization-sensitive.

**Code reference:** `Segmentation_Script.py` — Block 4
            """)

        how_this_was_built("GMM segmentation methodology", how_built)

    continue_to("ch7b", "Hunter Intent Classification")
    sim_footer()
