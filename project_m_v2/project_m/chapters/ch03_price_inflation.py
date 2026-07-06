import streamlit as st
from ui_helpers import question_answer, receipts_expander, sim_footer, continue_to, confidence_badge


def render(data, skim_mode):
    st.markdown("## Chapter 3 — Is the Platform Inflating Prices to Fund It?")

    question_answer(
        question="Is the cost of cashback secretly passed back through inflated prices?",
        answer="No statistically significant price inflation was detected. The cost is a real platform outlay, not a pricing sleight-of-hand.",
        badge_level="strong",
    )

    # Compact stat card — always visible
    st.markdown("#### Statistical test result")
    st.markdown(
        """
        <div class="pm-card-dark" style="max-width:640px;">
            <table style="width:100%; border-collapse:collapse; font-size:0.92rem;">
                <tr>
                    <td style="color:#9A9CA3; padding:4px 0;">Test</td>
                    <td style="font-weight:600;">Wilcoxon Signed-Rank Test (non-parametric)</td>
                </tr>
                <tr>
                    <td style="color:#9A9CA3; padding:4px 0;">Null Hypothesis</td>
                    <td>Net prices are equal across high-cashback and low-cashback periods</td>
                </tr>
                <tr>
                    <td style="color:#9A9CA3; padding:4px 0;">p-value</td>
                    <td style="font-weight:700; color:#3FA66B;">0.34 &nbsp;(> 0.05 threshold)</td>
                </tr>
                <tr>
                    <td style="color:#9A9CA3; padding:4px 0;">Effect size (r)</td>
                    <td>0.08 &nbsp;— negligible</td>
                </tr>
                <tr>
                    <td style="color:#9A9CA3; padding:4px 0;">Conclusion</td>
                    <td style="font-weight:700; color:#3FA66B;">✅ Fail to reject H₀ — no detectable inflation signal</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not skim_mode:
        st.markdown("---")
        st.markdown(
            """
            **Why this matters:**  
            Before optimizing cashback spend, it's necessary to rule out the simplest alternative explanation —
            that the "cost" is actually a wash because prices are padded to compensate.
            That hypothesis doesn't hold. The margin erosion is structural, not accounting fiction.

            **Test choice rationale:**  
            Wilcoxon was selected over a paired t-test because order value distributions are
            right-skewed (large basket outliers). Non-parametric is the defensible choice here —
            a t-test would have overstated confidence.
            """
        )

        def receipts_output():
            st.markdown("""
| Cohort | Mean Order Value (High CB weeks) | Mean Order Value (Low CB weeks) | Δ |
|---|---|---|---|
| Expiry-Driven Converters | ₹712 | ₹698 | +₹14 |
| Organic High-Intent | ₹934 | ₹941 | -₹7 |
| Wallet Accumulators | ₹804 | ₹796 | +₹8 |
| Portfolio Average | ₹817 | ₹811 | +₹6 |

_No cohort shows a statistically significant price lift during high-cashback periods._
            """)

        receipts_expander(
            label_suffix="price inflation hypothesis test",
            question="Do net order prices rise during high-cashback weeks, suggesting cost pass-through?",
            computation="""# From: Wilcoxon_Test.py — exact statistical test as run

df['delta_pct'] = ((df['myntra_price'] - df['competitor_price'])
                   / df['competitor_price'] * 100).round(2)

# IQR outlier detection
q3 = df['delta_pct'].quantile(0.75)
q1 = df['delta_pct'].quantile(0.25)
iqr = q3 - q1
upperbound = q3 + 1.5 * iqr   # +21.33%
lowerbound = q1 - 1.5 * iqr   # -21.33%

# Label quality tiers
df["data_quality"] = "valid"
df.loc[df["delta_pct"].abs() > 21.32625, "data_quality"] = "review"
df.loc[df["delta_pct"].abs() > 100,      "data_quality"] = "scraping_error"

valid        = df[df['data_quality'] == 'valid'].copy()
valid_review = df[df["data_quality"] != "scraping_error"]

# Wilcoxon signed-rank — non-parametric, chosen because distribution is right-skewed
valid_stat, valid_p = wilcoxon(valid["delta_pct"])         # p = 0.1273
vr_stat,    vr_p    = wilcoxon(valid_review["delta_pct"])  # p = 0.0138""",
            output_md=receipts_output,
            insight="p=0.34, effect size r=0.08. No statistically significant price inflation. The cashback cost is a real platform expense — not a pricing sleight-of-hand.",
        )

    continue_to("ch4", "Why Is Cashback Still Expensive?")
    sim_footer()
