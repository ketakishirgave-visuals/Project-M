import streamlit as st
from ui_helpers import question_answer, receipts_expander, how_this_was_built, sim_footer, continue_to

FEATURES = {
    "Timing & Urgency": [
        ("j_curve_ratio", "Late-to-early session ratio within the 7-day window", "Whether a customer's activity spikes near expiry — the behavioral fingerprint of urgency-driven conversion"),
        ("j_curve_std", "Week-over-week variability in the j-curve ratio", "Stable vs. erratic urgency patterns, High values indicate inconsistent urgency behaviour across weeks, while low values suggest stable purchasing habits"),
        ("time_to_expiry_at_conversion", "Days remaining in the window when the purchase was made", "Low = last-minute converter; high = organic, non-pressured buyer"),
        ("scratch_velocity", "Fraction of scratches that happened on days 1–3 of the window", "Measures how quickly customers interact with newly issued rewards after receiving them.; Higher values suggest immediate engagement, whereas lower values indicate delayed interaction."),
    ],
    "Engagement & Value": [
        ("spend_per_session", "Total spend divided by total sessions", "Proxy for basket quality — high-spend-per-session users are high-intent buyers, not browsers"),
        ("conversion_rate", "Transactions divided by total sessions", "Session-to-purchase efficiency — Measures session efficiency by estimating how frequently browsing sessions result in purchases."),
        ("session_density", "Sessions per active day", "Compressed, intense engagement vs. spread-out sporadic use"),
        ("late_session_intensity", "Mean sessions on days 6–7 of the window", "Captures increases in engagement during the final days of each cashback window."),
    ],
    "Wallet Behavior": [
        ("cashback_intensity", "Total cashback applied / total spend", "The cashback dependency ratio — high means the user is discount-gated"),
        ("expired_cashback_fraction", "Fraction of scratched cashback that was deliberately not redeemed", "Quantifies how frequently earned cashback expires unused despite being scratched, reflecting potential differences in redemption behaviour."),
        ("wallet_balance_slope", "Linear slope of running wallet balance over weeks", "Rising slope = accumulator; flat = steady spender; falling = depleter"),
        ("full_price_rate", "Fraction of transactions with < ₹5 cashback applied", "Measures how frequently purchases occur with minimal cashback support, providing a proxy for incentive independence."),
    ],
}


def render(data, skim_mode):
    st.markdown("## Chapter 6 — Feature Engineering: What Actually Describes a Customer?")

    question_answer(
        question="What behavioral signals actually separate a bargain-hunter from a loyal buyer?",
        answer="Twelve label-independent behavioural features were engineered using only observed customer interactions, without incorporating any downstream cluster assignments or target labels.",
        badge_level="strong",
    )

    # Compact default: three group one-liners
    st.markdown("#### Feature groups (12 features across 3 behavioral axes)")
    for group, features in FEATURES.items():
        st.markdown(
            f"""<div class="pm-card-dark">
            <b>{group}</b> — {len(features)} features: {', '.join(f[0] for f in features)}
            </div>""",
            unsafe_allow_html=True,
        )

    if not skim_mode:
        st.markdown("---")
        expand_all = st.checkbox("Show all 12 features →", value=False)
        if expand_all:
            for group, features in FEATURES.items():
                st.markdown(f"#### {group}")
                cols = st.columns(2)
                for i, (name, what, why) in enumerate(features):
                    with cols[i % 2]:
                        st.markdown(
                            f"""<div class="pm-card">
                            <code style="font-size:0.8rem;">{name}</code><br>
                            <b>What it measures:</b> {what}<br>
                            <span style="color:#555; font-size:0.85rem;"><b>Why it matters:</b> {why}</span>
                            </div>""",
                            unsafe_allow_html=True,
                        )

        def receipts_output():
            st.markdown("""
| Feature | Construction method | Key signal |
|---|---|---|
| j_curve_ratio | median(late_sess / early_sess) per week | Expiry urgency |
| scratch_velocity | mean(is_early_scratch) per customer | Discovery timing |
| expired_cashback_fraction | expired / scratched total | Hunter deliberate skip |
| wallet_balance_slope | linear regression slope of running balance | Accumulation intent |
| time_to_expiry_at_conversion | 7 − purchase_day, median | Urgency at checkout |
| cashback_intensity | total_cb / total_spend | Discount dependency |
| full_price_rate | fraction of txns with <₹5 CB applied | Organic purchase rate |
| spend_per_session | total_spend / total_sessions | Basket quality |
| conversion_rate | tx_count / total_sessions | Purchase efficiency |
| session_density | sessions / active_days | Engagement compression |
| j_curve_std | std(jc_week) across weeks | Behavioral consistency |
| late_session_intensity | mean sessions on days 6–7 | Expiry-surge intensity |
            """)

        receipts_expander(
            label_suffix="feature construction",
            question="How was each of the 12 features computed from raw event data?",
            computation="""# From: Feature_Engineering_Script.py — Block 3

# j_curve_ratio: late-window sessions / early-window sessions
# Captures urgency fingerprint — hunters spike late, organic buyers are flat
sess_early = (df_sess[df_sess['day_in_window'].isin([1, 2, 3])]
              .groupby(['customer_id', 'week'])['sessions']
              .mean().reset_index(name='early_sess'))
sess_late  = (df_sess[df_sess['day_in_window'].isin([6, 7])]
              .groupby(['customer_id', 'week'])['sessions']
              .mean().reset_index(name='late_sess'))

jc_df = sess_early.merge(sess_late, on=['customer_id', 'week'], how='inner')
jc_df['jc_week'] = jc_df['late_sess'] / jc_df['early_sess'].clip(lower=0.5)

jc_feat = jc_df.groupby('customer_id')['jc_week'].agg(
    j_curve_ratio='median',
    j_curve_std='std'
).reset_index()

# expired_cashback_fraction: how much scratched value was deliberately not redeemed
# This is the hunter signal — letting small cards expire to save wallet cap
sc_scratched = (df_sc[df_sc['scratched'] == 1]
                .groupby('customer_id')['card_amount_rs']
                .sum().reset_index(name='scratched_total'))
sc_expired   = (df_sc[df_sc['deliberately_expired'] == 1]
                .groupby('customer_id')['card_amount_rs']
                .sum().reset_index(name='expired_total'))

exp_feat['expired_cashback_fraction'] = (
    exp_feat['expired_total'] / exp_feat['scratched_total'].clip(lower=1e-6)
)""",
            output_md=receipts_output,
            insight="All 12 features built from raw behavioral logs, never touching cluster labels. Label-blindness is the integrity guarantee — the signal structure is emergent, not engineered toward a known answer.",
        )

        def how_built():
            st.markdown("""
**Label-blind construction:**  
No cluster labels, no archetype ground truth, no segment metadata was available during feature
engineering (Block 3 reads only from `cleaned_data/`). The features are purely observational —
every signal emerges from raw session, scratch, and transaction logs.

**Imputation strategy:**  
Population median imputation applied only where a customer has missing weeks (new users with
incomplete history). No forward-fill, no model-based imputation — median is the defensible
choice for right-skewed behavioral distributions.

**Scaling:**  
Features are written to `features_raw.csv` *unscaled*. Standardisation happens inside Block 4
(Segmentation) immediately before fitting, ensuring the feature audit reflects true behavioral
distributions, not scaled artifacts.
                        
**All engineered features were standardized prior to clustering to eliminate scale bias between ratio, count, and monetary variables.**

**Code reference:** `Feature_Engineering_Script.py` — Block 3
            """)

        how_this_was_built("feature engineering methodology", how_built)

    continue_to("ch7", "Six Segments")
    sim_footer()
