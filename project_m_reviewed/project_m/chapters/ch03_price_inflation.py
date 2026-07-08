import os
import pandas as pd
import streamlit as st
from ui_helpers import question_answer, receipts_expander, sim_footer, continue_to, confidence_badge

def find_data_file(filename):
    """
    Advanced path lookup that scans current script tree, working directory,
    and handles specific absolute windows structures for Myntra_PriceParityProof.
    """
    # 1. Direct environment lookup
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    
    # List of immediate search candidates
    search_paths = [
        os.path.join(script_dir, filename),
        os.path.join(os.getcwd(), filename),
    ]
    
    # 2. Add structural cross-folder pathways
    base_check = os.getcwd()
    for _ in range(4):
        search_paths.extend([
            os.path.join(base_check, "Myntra_PriceParityProof", filename),
            os.path.join(base_check, "price parity", filename),
            os.path.join(base_check, "price_parity", filename),
            os.path.join(base_check, "..", "Myntra_PriceParityProof", filename)
        ])
        base_check = os.path.dirname(base_check)
        
    # 3. Hardcoded user environment absolute fallback tracking (Windows specific)
    win_fallback = os.path.join(
        r"C:\Users\shirg\OneDrive\Desktop\Myntra Incentive Bleed Project\Myntra_PriceParityProof", 
        filename
    )
    search_paths.append(win_fallback)

    # Return the first path option that genuinely exists on the system
    for target_path in search_paths:
        if os.path.exists(target_path):
            return target_path
            
    # Final default fallback if everything is completely missing
    return os.path.join(os.getcwd(), filename)


def render(data, skim_mode):
    st.markdown("## Chapter 3 — Is the Platform Inflating Prices to Fund It?")

    question_answer(
        question="Is the cost of cashback secretly passed back through inflated prices?",
        answer="No statistically significant price inflation was detected. The evidence suggests cashback is not systematically funded through observable retail price inflation.",
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
                    <td>Myntra prices are in strict parity with competitor prices (Median Delta = 0%)</td>
                </tr>
                <tr>
                    <td style="color:#9A9CA3; padding:4px 0;">p-value (Valid Tier)</td>
                    <td style="font-weight:700; color:#3FA66B;">0.1273 &nbsp;(> 0.05 threshold)</td>
                </tr>
                <tr>
                    <td style="color:#9A9CA3; padding:4px 0;">Conclusion</td>
                    <td style="font-weight:700; color:#3FA66B;">✅ Fail to reject H₀ — Broad price parity holds across clean matches</td>
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
            Before evaluating cashback efficiency, it is necessary to rule out the alternative explanation that cashback costs are systematically recovered through higher retail prices. The statistical evidence does not support that explanation within the matched sample, allowing the subsequent optimization analysis to treat cashback as a genuine promotional cost.

            **Test choice rationale:**  
            Wilcoxon Signed-Rank Test was selected over the paired t-test because the paired price differences could not safely be assumed to follow a normal distribution, making a non-parametric paired test the more defensible choice.
            
            **Scope:**
            Scope: This analysis evaluates matched retail prices only. It does not assess supplier agreements, procurement costs, platform-funded promotions, or other internal pricing mechanisms that are not publicly observable.
            """
        )

    # Dynamic Receipts Table Output Function
    def receipts_output():
        try:
            # Dynamically resolve file location
            csv_path = find_data_file("platform_parity_summary.csv")
            df_summary = pd.read_csv(csv_path)
            
            markdown_rows = []
            for _, row in df_summary.iterrows():
                platform = row['competitor_platform']
                delta = row['median_delta_pct']
                
                if delta < 0:
                    status = "🟢 Myntra is slightly cheaper"
                elif delta == 0:
                    status = "🤝 Strict Parity"
                else:
                    status = "🔺 Myntra has a premium pricing delta"
                    
                markdown_rows.append(f"| **{platform}** | {delta:+.2f}% | {status} |")
            
            table_header = (
                "| Competitor Platform | Median Price Delta vs. Myntra (%) | Parity Status |\n"
                "| :--- | :--- | :--- |\n"
            )
            table_body = "\n".join(markdown_rows)
            footer = f"\n\n_Data pulled directly from valid samples in `{os.path.basename(csv_path)}`._"
            
            st.markdown(table_header + table_body + footer)
            
        except Exception as e:
            # Safe UI fallback block
            st.warning(f"Could not load automated summary file: {e}")
            st.markdown("""
| Competitor Platform | Median Price Delta vs. Myntra (%) | Parity Status |
| :--- | :--- | :--- |
| **Puma** | -4.00% | 🟢 Myntra is slightly cheaper |
| **Mamaearth** | -2.06% | 🟢 Myntra is slightly cheaper |
| **Max Fashion** | +0.00% | 🤝 Strict Parity |
| **Amazon** | +0.00% | 🤝 Strict Parity |
| **Off Duty** | +2.30% | 🔺 Myntra has a premium pricing delta |
| **LA Girl** | +5.50% | 🔺 Myntra has a premium pricing delta |
            """)

    # Render Receipts Expander Card Component
    receipts_expander(
        label_suffix="price inflation hypothesis test",
        question="Is the Platform charging more than the competitors?",
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
        insight="p=0.1273, no statistically significant price inflation against major platforms.",
    )

    # Dynamic Category Matrix Breakdown Widget with Heatmap Optional Rendering
    if st.checkbox("Show breakdown by Category Matrix"):
        try:
            matrix_path = find_data_file("category_vs_platform_parity_matrix.xlsx")
            df_matrix = pd.read_excel(matrix_path)
            st.dataframe(df_matrix.set_index('category').style.format("{:+.2f}%", na_rep="-"))
            
            # Render the heatmap visualization inline if available
            heatmap_path = find_data_file("category_parity_heatmap.png")
            if os.path.exists(heatmap_path):
                st.image(heatmap_path, caption="Price Parity Heatmap: Myntra vs Competitors by Category", use_container_width=True)
        except Exception as matrix_err:
            st.error(f"Error loading matrix: {matrix_err}")

    # Navigation Actions
    continue_to("ch4", "Why Is Cashback Still Expensive?")
    sim_footer()