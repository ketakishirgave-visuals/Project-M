import streamlit as st
from ui_helpers import question_answer, receipts_expander, how_this_was_built, sim_footer, continue_to, before_after, evidence_used


CLEANING_ISSUES = [
    {
        "title": "City Tier Normalisation",
        "problem": "city_tier arrived with inconsistent formatting (T1, Tier 1, tier_1, TIER 1) plus ~5% missing values",
        "fix": "Built a canonical mapping to a single format, then applied mode imputation for the remaining nulls — not a hardcoded default, which would have introduced silent bias.",
        "result": "97 nulls resolved · 3 distinct values remain",
        "table": "customers.csv",
    },
    {
        "title": "Gender Null Imputation",
        "problem": "~4% of gender values were missing",
        "fix": "Filled with 'Unknown' — preserves the row without introducing a distributional bias toward any one category",
        "result": "83 nulls → 'Unknown'",
        "table": "customers.csv",
    },
    {
        "title": "Scratch Card Null Taxonomy",
        "problem": "card_amount_rs contains two structurally different null types: a card that was never issued, and a card that was issued but whose value failed to log (an API-timeout pattern)",
        "fix": "Timeout-pattern nulls (scratched=1, amount=NaN) were imputed with a per-customer median. Structural nulls (scratched=0) were left untouched, since a card that was never issued has no value to estimate.",
        "result": "0 timeout-pattern nulls in this run · structural nulls kept intact",
        "table": "scratch_cards.csv",
    },
    {
        "title": "Transaction Deduplication",
        "problem": "Exact duplicate rows can occur from upstream event-stream re-delivery",
        "fix": "drop_duplicates() on the full row, keeping the first occurrence",
        "result": "0 duplicates found in this run",
        "table": "transactions.csv",
    },
    {
        "title": "Cashback Overage Cap",
        "problem": "cashback_applied occasionally exceeded order_value_rs — not possible under the redemption rules",
        "fix": "Capped cashback_applied at order_value_rs and recomputed net_revenue_rs",
        "result": "0 overage rows in this run",
        "table": "transactions.csv",
    },
    {
        "title": "Ghost Session Fix",
        "problem": "Rows where sessions=0 but session_dur_min>0 — a logging inconsistency, since a session with recorded duration must have occurred",
        "fix": "Estimated sessions from duration using the median minutes-per-session ratio from valid rows, with a floor of 1 session",
        "result": "3,880 ghost sessions corrected",
        "table": "daily_sessions.csv",
    },
    {
        "title": "Negative Net Revenue Drop",
        "problem": "net_revenue_rs < 0 is not possible once the overage cap above is applied",
        "fix": "Rows with negative net revenue were dropped",
        "result": "0 rows dropped in this run",
        "table": "transactions.csv",
    },
]


def render(data, skim_mode):
    st.markdown("## Chapter 5 — Cleaning the Evidence")

    question_answer(
        question="Can this data be trusted before it's used for segmentation?",
        answer="Yes — every anomaly was identified, classified, and either corrected or intentionally preserved, with a full audit trail.",
        badge_level="strong",
    )

    evidence_used(["SQL Block 1"], key="ch05_top")

    # Compact summary always visible
    st.markdown(
        """
        <div class="pm-card-dark" style="display:flex; gap:2rem; flex-wrap:wrap;">
            <div><span class="pm-metric-big">180</span><div style="color:#9A9CA3; font-size:0.82rem;">nulls resolved</div></div>
            <div><span class="pm-metric-big">3,880</span><div style="color:#9A9CA3; font-size:0.82rem;">sessions corrected</div></div>
            <div><span class="pm-metric-big">0</span><div style="color:#9A9CA3; font-size:0.82rem;">duplicates found</div></div>
            <div><span class="pm-metric-big">4</span><div style="color:#9A9CA3; font-size:0.82rem;">tables audited</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Always-visible callout: what was NOT cleaned, and why
    st.warning(
        "**What was intentionally left as-is:**\n\n"
        "- **Structural nulls** in `card_amount_rs` where `scratched=0` — the card was never issued, so there is no value to estimate\n"
        "- **The `deliberately_expired` flag** — this records a genuine user decision to let a card lapse, not a data error\n"
        "- **The behavioral overlap between archetypes** — customers whose behavior sits between two profiles are a real feature of the population, not a labeling mistake, and removing them would make the segmentation look cleaner than the underlying behavior actually is"
    )

    if not skim_mode:
        st.markdown("#### Before → Python → After")
        st.caption("A visual walkthrough of how three representative issues moved through the cleaning script.")

        before_after(
            title="1. City tier formatting",
            before_lines=["T1", "Tier 1", "tier_1", "TIER 1", "NaN"],
            after_lines=["T1", "T1", "T1", "T1", "T1  (mode-imputed)"],
            transform="city_map = {variant: canonical}; df['city_tier'].map(city_map).fillna(mode)",
            caption="97 rows resolved to one of 3 canonical tiers.",
        )
        st.write("")
        before_after(
            title="2. Ghost sessions (impossible zero-session rows)",
            before_lines=["sessions=0, session_dur_min=14.2", "sessions=0, session_dur_min=8.6"],
            after_lines=["sessions=2, session_dur_min=14.2", "sessions=1, session_dur_min=8.6"],
            transform="sessions = max(1, round(session_dur_min / median_minutes_per_session))",
            caption="3,880 rows corrected using the median minutes-per-session ratio from valid rows.",
        )
        st.write("")
        before_after(
            title="3. Cashback exceeding order value",
            before_lines=["order_value_rs=420, cashback_applied=460"],
            after_lines=["order_value_rs=420, cashback_applied=420, net_revenue_rs=0"],
            transform="cashback_applied = min(cashback_applied, order_value_rs); net_revenue_rs recomputed",
            caption="Guards against an economically impossible negative net revenue downstream.",
        )
        st.write("")

        st.markdown("#### Issue-by-issue breakdown")
        st.markdown("_Click any issue to expand the fix detail._")
        for issue in CLEANING_ISSUES:
            with st.expander(f"**{issue['table']}** — {issue['title']} · _{issue['result']}_"):
                st.markdown(f"**Problem:** {issue['problem']}")
                st.markdown(f"**Fix applied:** {issue['fix']}")
                st.success(f"Result: {issue['result']}")

        def receipts_output():
            st.markdown("""
| Table | Raw rows | Clean rows | Δ |
|---|---|---|---|
| customers.csv | 2,000 | 2,000 | 0 |
| daily_sessions.csv | 112,000 | 112,000 | 0 |
| scratch_cards.csv | 112,000 | 112,000 | 0 |
| transactions.csv | 14,583 | 14,583 | 0 |
            """)
            st.caption("Row counts stable — cleaning fixed quality issues, not row-level drops (except 0 negative-revenue rows).")

        receipts_expander(
            label_suffix="full cleaning audit log",
            question="What was the before/after state of each table across all cleaning operations?",
            computation="""# From: Data_Cleaning_Script.py — Block 2

# Ghost session fix — sessions=0 but duration>0 is physically impossible
ghost = (df_sess['sessions'] == 0) & (df_sess['session_dur_min'] > 0)
if ghost.sum() > 0:
    valid_rows    = df_sess[~ghost & (df_sess['sessions'] > 0)]
    med_dur       = (valid_rows['session_dur_min'] / valid_rows['sessions']).median()
    df_sess.loc[ghost, 'sessions'] = np.maximum(
        1, np.round(df_sess.loc[ghost, 'session_dur_min'] / med_dur)
    )

# Cashback overage cap — cashback cannot exceed the order it was applied to
overage_mask = df_txn['cashback_applied'] > df_txn['order_value_rs']
if overage_mask.sum() > 0:
    df_txn.loc[overage_mask, 'cashback_applied'] = df_txn['order_value_rs']
    df_txn['net_revenue_rs'] = df_txn['order_value_rs'] - df_txn['cashback_applied']

# Scratch card null taxonomy — two structurally different null types
api_timeout_mask = (df_sc['scratched'] == 1) & (df_sc['card_amount_rs'].isna())
if api_timeout_mask.sum() > 0:
    arch_median = (df_sc[df_sc['card_amount_rs'].notna()]
                   .groupby('customer_id')['card_amount_rs'].median())
    df_sc.loc[api_timeout_mask, 'card_amount_rs'] = (
        df_sc.loc[api_timeout_mask, 'customer_id'].map(arch_median)
    )
    df_sc['card_amount_rs'].fillna(df_sc['card_amount_rs'].median(), inplace=True)
# Note: scratched=0 nulls are intentionally NOT touched — card was never issued. Full audit written to: outputs/cleaning_audit.md""",
            output_md=receipts_output,
            insight="All four tables cleaned with documented before/after states. The audit markdown is the permanent record — every transformation is traceable.",
        )

        def how_built():
            st.markdown("""
**Null taxonomy approach:**  
Instead of a blanket `fillna()`, each null was classified by its root cause before treatment:
- *Structural nulls* (card never issued — correctly sparse) → preserved
- *Timeout-pattern nulls* (card issued, value failed to log) → imputed with per-customer median
- *Missing demographics* → flagged as 'Unknown' rather than mode-imputed, to avoid distribution bias

**Ghost session logic:**  
`sessions=0` with `session_dur_min>0` is physically impossible. Estimated from the median
minutes-per-session ratio of valid rows. `max(1, round(...))` ensures at least one session.

**Code reference:** `Data_Cleaning_Script.py` — Block 2
            """)

        how_this_was_built("data cleaning taxonomy", how_built)

    continue_to("ch6", "Feature Engineering")
    sim_footer()
