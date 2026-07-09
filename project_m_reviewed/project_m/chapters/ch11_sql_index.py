import streamlit as st
from ui_helpers import sim_footer, ACCENT, metric_spread, sql_block
import plotly.graph_objects as go

# ── Color Palette ────────────────────────────────────────────────────────────
ACCENT      = "#D4A24C"
GREEN       = "#3FA66B"
RED         = "#C4573F"
MUTED       = "#9A9CA3"
BG          = "#22252C"
PAPER       = "#181A1F"
FONT_COLOR  = "#EDEBE6"

SEGMENTS    = ["Seg 0", "Seg 1", "Seg 2", "Seg 3", "Seg 4", "Seg 5"]
BANDS       = ['₹0–20', '₹21–40', '₹41–60', '₹61–80', '₹80+']

# ── Mismatches Fixed: Re-keyed to match FINANCIAL_BLOCKS perfectly ──────────
BLOCK_KPIS = {
    "Block 0":  {"kpi": "3.5%",    "label": "Average leakage rate across segments",         "sub": "100% driven by deliberate expiry — zero unscratched cards"},
    "Block 1":  {"kpi": "₹41L",    "label": "Gross revenue from Segment 1 alone",           "sub": "Organic High-Intent Buyers — highest profit in every city tier"},
    "Block 2":  {"kpi": "91.1%",   "label": "Segment 4 orders occur in high-wallet weeks",  "sub": "Segment 1 flips this — only 21.3% high-wallet dependency"},
    "Block 3":  {"kpi": "₹11.16",  "label": "Profit per ₹1 cashback — Segment 1 (T3)",     "sub": "Segment 4 returns just ₹3.4 — a 3.3× gap between best and worst"},
    "Block 4":  {"kpi": "+5.32",   "label": "Max marginal frequency leap at ₹80+",          "sub": "Observed in Cluster 0. Moderate spending thresholds see diminishing returns."},
    "Block 5":  {"kpi": "₹171.6",  "label": "Avg wallet at checkout under expiry pressure", "sub": "vs ₹131.3 early window — but AOV is lower under pressure"},
    "Block 6":  {"kpi": "12.82%",  "label": "Deliberate expiry rate — Segment 4",           "sub": "Segments 1 and 2 are at 0.00% — zero strategic card skipping"},
    "Block 7":  {"kpi": "9.3%",    "label": "Profit share from top 10% of users",           "sub": "They consume 17.3% of cashback — a poor return on concentration"},
    "Block 8":  {"kpi": "|r|<0.18","label": "Max Pearson r across all segments",            "sub": "Wallet size does not predict order size in any segment"},
    "Block 9":  {"kpi": "₹10.75",  "label": "Segment 1 profit/₹1 — Mid cohort",             "sub": "Holds at ₹10.9 for new users too — economics are stable across tenure"},
    "Block 10": {"kpi": "84.2%",   "label": "Post-peak orders at lower wallet limits",      "sub": "Avg checkout balance drops to ₹34.20 after milestone spend"},
}

# ─────────────────────────────────────────────────────────────────────────────
# Segment financial & behavioral reporting layer
# ─────────────────────────────────────────────────────────────────────────────
FINANCIAL_BLOCKS = [
    # Blocks 0-3 remain unchanged...
    {
        "id": "Block 0",
        "title": "Cashback Leakage by Segment & City Tier",
        "question": "How much issued cashback is lost to unscratched cards or deliberate expiry, and where?",
        "sql": """WITH leakage_base AS (
    SELECT s.customer_id, f.final_cluster_id, c.city_tier,
        SUM(COALESCE(s.card_amount_rs, 0)) AS total_issued,
        SUM(CASE WHEN s.scratched = 0 THEN COALESCE(s.card_amount_rs, 0) ELSE 0 END) AS unscratched_leakage,
        SUM(CASE WHEN s.deliberately_expired = 1 THEN COALESCE(s.card_amount_rs, 0) ELSE 0 END) AS deliberate_expiry_leakage
    FROM scratch_cards s
    JOIN customers c ON s.customer_id = c.customer_id
    JOIN final_cluster_assignments f ON c.customer_id = f.customer_id
    GROUP BY 1, 2, 3
)
SELECT final_cluster_id, city_tier, SUM(total_issued) AS total_cashback_issued,
    ROUND(SUM(unscratched_leakage + deliberate_expiry_leakage) * 100.0 / NULLIF(SUM(total_issued), 0), 2) AS leakage_rate_pct,
    CASE WHEN SUM(unscratched_leakage) > SUM(deliberate_expiry_leakage) THEN 'Unscratched Cards'
         WHEN SUM(deliberate_expiry_leakage) > SUM(unscratched_leakage) THEN 'Deliberate Expiry'
         ELSE 'Balanced / No Leakage' END AS primary_leakage_source
FROM leakage_base GROUP BY 1, 2 ORDER BY 1, 2;""",
        "output": "Leakage runs 2.5%–3.7% of issued value across segments · driven almost entirely by deliberate expiry, not unscratched cards",
        "insight": "Unscratched-card leakage is effectively 0% across all cohorts, proving high feature interaction; reward waste is entirely driven by deliberate expiry concentrated within opportunistic segments (0, 3, and 4).",
    },
    {
        "id": "Block 1",
        "title": "Segment Profitability by City Tier",
        "question": "Which segment/city-tier combinations generate the most profit, and how are they ranked within tier?",
        "sql": """SELECT f.final_cluster_id, c.city_tier, COUNT(DISTINCT c.customer_id) AS customer_count,
    SUM(t.cashback_applied) AS total_cashback_received, SUM(t.order_value_rs) AS gross_revenue_generated,
    SUM(t.net_revenue_rs) AS total_profit_generated,
    RANK() OVER (PARTITION BY c.city_tier ORDER BY COUNT(DISTINCT c.customer_id) DESC) AS cluster_distribution_rank
FROM customers c
JOIN final_cluster_assignments f ON c.customer_id = f.customer_id
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY 1, 2 ORDER BY total_profit_generated DESC;""",
        "output": "Segment 1 (Organic High-Intent) ranks #1 by population and profit in every city tier · Segment 1 alone contributes ~₹41L of gross revenue",
        "insight": "Segment 1 ranks first by profit and by population in every city tier observed, while Segment 5 (a 9-user micro-segment) ranks last. This indicates behavioral archetype is a stronger predictor of margin than city tier in this dataset — it does not rule out geography mattering at a larger sample size.",
        "spread": {"label": "Total profit generated by segment", "best_name": "Segment 1", "best_val": "₹41.1L (T1)", "worst_name": "Segment 5", "worst_val": "₹0.06L (T3)", "gap": "~684×", "unit_note": "driven mainly by population size, not just per-user margin"},
    },
    {
        "id": "Block 2",
        "title": "High- vs. Low-Wallet Conversion Dependency",
        "question": "How many of these purchases are real demand versus users just scratching an itch for free cash?",
        "sql": """WITH ranked_wallets AS (
    SELECT wallet_end_rs, ROW_NUMBER() OVER (ORDER BY wallet_end_rs) AS row_num, COUNT(*) OVER () AS total_rows
    FROM weekly_features_gt
),
weekly_median AS (
    SELECT AVG(wallet_end_rs) AS global_median_wallet FROM ranked_wallets
    WHERE row_num IN (FLOOR((total_rows + 1) / 2), CEIL((total_rows + 1) / 2))
), 
dependency_aggregates AS (
    SELECT f.final_cluster_id,
        SUM(CASE WHEN w.wallet_end_rs > m.global_median_wallet THEN w.weekly_orders ELSE 0 END) AS high_wallet_orders,
        SUM(CASE WHEN w.wallet_end_rs <= m.global_median_wallet THEN w.weekly_orders ELSE 0 END) AS low_wallet_orders,
        SUM(w.weekly_orders) AS total_orders,
        SUM(CASE WHEN w.cashback_applied_rs = 0 THEN w.weekly_orders ELSE 0 END) AS zero_cashback_orders
    FROM weekly_features_gt w
    JOIN final_cluster_assignments f ON w.customer_id = f.customer_id
    CROSS JOIN weekly_median m GROUP BY 1
),
cluster_rates AS (
    SELECT final_cluster_id, AVG(full_price_rate) AS full_price_purchase_rate FROM final_cluster_assignments GROUP BY 1
)
SELECT da.final_cluster_id, da.high_wallet_orders, da.low_wallet_orders,
    ROUND(da.high_wallet_orders * 100.0 / NULLIF(da.total_orders, 0), 2) AS high_wallet_conversion_pct,
    ROUND(da.low_wallet_orders * 100.0 / NULLIF(da.total_orders, 0), 2) AS low_wallet_conversion_pct,
    ROUND(da.zero_cashback_orders * 100.0 / NULLIF(da.total_orders, 0), 2) AS zero_cashback_purchase_pct,
    ROUND(cr.full_price_purchase_rate, 4) AS full_price_purchase_rate 
FROM dependency_aggregates da JOIN cluster_rates cr ON da.final_cluster_id = cr.final_cluster_id ORDER BY da.final_cluster_id;""",
        "output": "Segment 4: 91.1% of orders occur in high-wallet weeks · Segment 1: only 21.3% · Segment 5: 17.1% (smallest base, 70 orders total)",
        "insight": "Segments 0, 3, and 4 exhibit chronic gamification dependency, converting almost exclusively (>78%) during high-wallet weeks, whereas Segment 1 converts organically regardless of incentive depth.",
    },
    {
        "id": "Block 3",
        "title": "Revenue & Profit per ₹1 of Cashback",
        "question": "What is the actual return on every rupee of cashback issued, by segment and city tier?",
        "sql": """SELECT f.final_cluster_id, c.city_tier, SUM(t.order_value_rs) AS gross_revenue_generated,
    SUM(t.net_revenue_rs) AS total_profit_generated, SUM(t.cashback_applied) AS total_cashback_received,
    ROUND(SUM(t.order_value_rs) / NULLIF(SUM(t.cashback_applied), 0), 2) AS revenue_per_1_cashback,
    ROUND(SUM(t.net_revenue_rs) / NULLIF(SUM(t.cashback_applied), 0), 2) AS profit_per_1_cashback
FROM final_cluster_assignments f JOIN customers c ON f.customer_id = c.customer_id
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY 1, 2 ORDER BY profit_per_1_cashback DESC;""",
        "output": "Segment 1 (T3): ₹11.16 profit per ₹1 · Segment 2 (T1): ₹6.93 · Segment 4 (blended): ~₹3.4 — the lowest of the five stable segments",
        "insight": "Segment 1 delivers the highest observed profit per ₹1 of cashback (₹11.16, Tier 3), while Segment 4 delivers the lowest (₹3.19, Tier 2) — a roughly 3.5× spread. The gap is descriptive of current allocation, not a claim about what either segment could return under a different policy.",
        "spread": {"label": "Profit per ₹1 of cashback", "best_name": "Segment 1 (T3)", "best_val": "₹11.16", "worst_name": "Segment 4 (T2)", "worst_val": "₹3.19", "gap": "₹7.97", "unit_note": "3.5× difference in observed return per cashback rupee"},
    },
    
    # ── UPDATED BLOCK 4: CONTAINS DYNAMIC WINDOW CALCULATIONS ────────────────
    {
        "id": "Block 4",
        "title": "Cashback Efficiency Bands (Diminishing Returns Curve)",
        "question": "Is there a sweet spot where cashback moves the needle — or are we over-subsidizing historical users?",
        "sql": """WITH cashback_bands AS (
    SELECT f.final_cluster_id, w.customer_id, w.cashback_applied_rs,
        CASE WHEN cashback_applied_rs <= 20 THEN '₹0–20'
             WHEN cashback_applied_rs <= 40 THEN '₹21–40'
             WHEN cashback_applied_rs <= 60 THEN '₹41–60'
             WHEN cashback_applied_rs <= 80 THEN '₹61–80'
             ELSE '₹80+' END AS cashback_band
    FROM weekly_features_gt w
    JOIN final_cluster_assignments f ON w.customer_id = f.customer_id
    WHERE cashback_applied_rs > 0
),
band_summary AS (
    SELECT final_cluster_id, cashback_band,
        CASE cashback_band WHEN '₹0–20' THEN 1 WHEN '₹21–40' THEN 2 WHEN '₹41–60' THEN 3 WHEN '₹61–80' THEN 4 ELSE 5 END AS band_order,
        AVG(cashback_applied_rs) AS avg_cashback,
        COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT customer_id), 0) AS purchase_frequency,
        COUNT(*) AS observations
    FROM cashback_bands GROUP BY 1, 2
)
SELECT final_cluster_id, cashback_band, ROUND(avg_cashback, 2) AS avg_cashback, ROUND(purchase_frequency, 4) AS purchase_frequency, observations,
    ROUND(purchase_frequency - COALESCE(LAG(purchase_frequency, 1) OVER (PARTITION BY final_cluster_id ORDER BY band_order ASC), purchase_frequency), 4) AS marginal_frequency_gain
FROM band_summary ORDER BY final_cluster_id, band_order;""",
        "output": "Seg 4 & Seg 0 see huge frequency spikes (+6.61 and +5.33) strictly inside the extreme ₹80+ band · Seg 1 and 5 exhibit negative marginal returns past ₹60",
        "insight": "Aggressive spend injections do not generate flat incremental growth. Middle-tier bands (₹41–80) show severe plateaus or negative frequency fatigue (e.g., Segment 1 dips -0.1090), proving that scaling incentive depths linearly is economically inefficient.",
    },
    # Blocks 5-10 remain unchanged...
    {
        "id": "Block 5",
        "title": "Purchase Timing Windows",
        "question": "Does purchase timing shift as the wallet's 7-day expiry approaches, and does basket size change with it?",
        "sql": """SELECT f.final_cluster_id,
    CASE WHEN t.purchase_day <= 3 THEN 'Early Window (Days 1-3)'
         WHEN t.purchase_day >= 5 THEN 'Expiry Pressure (Days 5-7)'
         ELSE 'Mid-lifecycle (Day 4)' END AS purchase_timing_window,
    COUNT(*) AS total_orders, AVG(t.wallet_at_checkout) AS wallet_at_checkout_trigger, AVG(t.order_value_rs) AS average_order_value
FROM transactions t JOIN final_cluster_assignments f ON t.customer_id = f.customer_id
GROUP BY 1, 2 ORDER BY 1, purchase_timing_window;""",
        "output": "Expiry-pressure orders carry a higher wallet-at-checkout trigger in every segment (e.g. Segment 4: ₹171.6 vs ₹131.3 early) but a lower average order value than early-window orders in most segments",
        "insight": "Purchases become more frequent near expiry windows, and are associated with larger wallet balances at checkout across all segments — but with a lower average order value than early-window purchases.",
    },
    {
        "id": "Block 6",
        "title": "Scratch Card Issuance & Deliberate Expiry Rate",
        "question": "What share of issued cards are deliberately allowed to expire, per segment?",
        "sql": """SELECT f.final_cluster_id, COUNT(s.customer_id) AS total_cards,
    ROUND(SUM(CASE WHEN s.deliberately_expired = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS deliberate_expiry_rate_pct,
    ROUND(SUM(CASE WHEN s.scratched = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS card_rejection_rate_pct,
    AVG(COALESCE(s.card_amount_rs, 0)) AS average_card_amount,
    SUM(CASE WHEN s.deliberately_expired = 1 OR s.scratched = 0 THEN COALESCE(s.card_amount_rs, 0) ELSE 0 END) AS total_value_lost_to_optimization
FROM scratch_cards s JOIN final_cluster_assignments f ON s.customer_id = f.customer_id GROUP BY 1;""",
        "output": "Segment 4: 12.82% deliberate expiry (highest) · Segments 1 and 2: 0.00% · card rejection (unscratched) is 0.00% everywhere",
        "insight": "Observed deliberate expiry behaviour is concentrated in specific segments: Segment 4 shows a 12.82% deliberate expiry rate, while Segments 1 and 2 show 0.00%.",
        "spread": {"label": "Deliberate expiry rate", "best_name": "Segments 1 & 2", "best_val": "0.00%", "worst_name": "Segment 4", "worst_val": "12.82%", "gap": "12.82 pts", "unit_note": "share of issued cards let lapse on purpose"},
    },
    {
        "id": "Block 7",
        "title": "Cashback & Profit Concentration (Top 10% of Users)",
        "question": "How concentrated is cashback consumption and profit contribution across the user base?",
        "sql": """WITH user_totals AS (
    SELECT customer_id, SUM(cashback_applied) AS total_user_cashback, SUM(net_revenue_rs) AS total_user_profit,
        PERCENT_RANK() OVER (ORDER BY SUM(cashback_applied) DESC) AS cashback_percent_rank
    FROM transactions GROUP BY 1
)
SELECT CASE WHEN cashback_percent_rank <= 0.10 THEN 'Top 10%' ELSE 'Remaining 90%' END AS tier,
    SUM(total_user_cashback) AS total_cashback_consumed, SUM(total_user_profit) AS total_profit_yield
FROM user_totals GROUP BY 1;""",
        "output": "Top 10% of users consume 17.3% of all cashback but generate only 9.3% of profit · the remaining 90% generate 90.7% of profit on 82.7% of cashback",
        "insight": "The top 10% of users by cashback consumption account for 17.3% of total cashback spend but only 9.3% of total profit — a share of incentive roughly 1.9× their share of profit contribution.",
        "spread": {"label": "Cashback share vs. profit share", "best_name": "Bottom 90% of users", "best_val": "82.7% CB / 90.7% profit", "worst_name": "Top 10% of users", "worst_val": "17.3% CB / 9.3% profit", "gap": "1.9×", "unit_note": "ratio of cashback share to profit share, top decile"},
    },
    {
        "id": "Block 8",
        "title": "Wallet-Balance-to-Order-Value Correlation",
        "question": "Within each segment, how strongly does the wallet balance at checkout correlate with the order value placed?",
        "sql": """SELECT f.final_cluster_id,
    ROUND(
        (COUNT(*) * SUM(t.wallet_at_checkout * t.order_value_rs) - SUM(t.wallet_at_checkout) * SUM(t.order_value_rs)) /
        NULLIF(SQRT(
            (COUNT(*) * SUM(t.wallet_at_checkout * t.wallet_at_checkout) - POW(SUM(t.wallet_at_checkout), 2)) *
            (COUNT(*) * SUM(t.order_value_rs * t.order_value_rs) - POW(SUM(t.order_value_rs), 2))
        ), 0), 4
    ) AS wallet_spend_correlation
FROM transactions t JOIN final_cluster_assignments f ON t.customer_id = f.customer_id
WHERE t.wallet_at_checkout IS NOT NULL AND t.order_value_rs IS NOT NULL GROUP BY 1 ORDER BY 1;""",
        "output": "Segment 0: +0.088 · Segment 1: −0.092 · Segment 2: −0.177 · Segment 3: +0.129 · Segment 4: −0.003 · Segment 5: +0.040",
        "insight": "Pearson correlation between wallet balance and order value stays below |r|=0.18 in every segment, indicating little to no linear relationship between the size of a customer's wallet and the size of their basket.",
    },
    {
        "id": "Block 9",
        "title": "Profitability by Tenure Cohort",
        "question": "Do newer users need constant discounts to stick around, or do they stabilize into normal behavior as they mature?",
        "sql": """WITH tenure_cohorts AS (
    SELECT customer_id, final_cluster_id,
        CASE WHEN signup_tenure_weeks <= 12 THEN 'New Cohort (<=12 Weeks)'
             WHEN signup_tenure_weeks <= 52 THEN 'Mid Cohort (13-52 Weeks)'
             ELSE 'Mature Cohort (>52 Weeks)' END AS tenure_vintage
    FROM final_cluster_assignments
)
SELECT tc.tenure_vintage, tc.final_cluster_id, COUNT(DISTINCT tc.customer_id) AS active_headcount,
    SUM(t.cashback_applied) AS total_cashback_distributed, SUM(t.order_value_rs) AS gross_revenue_generated,
    SUM(t.net_revenue_rs) AS net_profit_realized, ROUND(SUM(t.net_revenue_rs) / NULLIF(SUM(t.cashback_applied), 0), 2) AS profit_per_1_cashback
FROM tenure_cohorts tc LEFT JOIN transactions t ON tc.customer_id = t.customer_id
GROUP BY 1, 2 ORDER BY tc.tenure_vintage, profit_per_1_cashback DESC;""",
        "output": "Segment 1 holds ₹10.5–10.9 profit-per-cashback-rupee across all three tenure cohorts · Segment 4 stays lowest (₹3.4–3.5) at every tenure stage",
        "insight": "Segment 1's profit-per-cashback-rupee stays within a narrow ₹10.5–10.9 band, and Segment 4's within ₹3.4–3.5, across New, Mid, and Mature tenure cohorts.",
        "spread": {"label": "Profit per ₹1 cashback, ranked across tenure cohorts", "best_name": "Segment 1", "best_val": "₹10.5 – ₹10.9", "worst_name": "Segment 4", "worst_val": "₹3.4 – ₹3.5", "gap": "~₹7.2", "unit_note": "range held consistent across New/Mid/Mature cohorts"},
    },
    {
        "id": "Block 10",
        "title": "Post-Peak Wallet Conversion Velocity",
        "question": "Once a user hits their lifetime peak wallet balance and spends it, do they freeze and wait to rebuild to that peak before converting again?",
        "sql": """WITH wallet_history AS (
    SELECT customer_id, purchase_day, wallet_at_checkout, order_value_rs,
        MAX(wallet_at_checkout) OVER (PARTITION BY customer_id ORDER BY purchase_day ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS historic_peak_wallet
    FROM transactions
),
post_peak_conversions AS (
    SELECT *,
        CASE WHEN historic_peak_wallet IS NULL THEN 'Pre-Peak Baseline'
             WHEN wallet_at_checkout >= historic_peak_wallet THEN 'At/Above Historic Peak'
             WHEN wallet_at_checkout < historic_peak_wallet THEN 'Accepting Lower Amounts (₹10-40)'
             ELSE 'Other' END AS checkout_behavior_tier
    FROM wallet_history
)
SELECT checkout_behavior_tier, COUNT(*) AS total_orders_placed, ROUND(AVG(wallet_at_checkout), 2) AS avg_wallet_at_checkout, ROUND(AVG(order_value_rs), 2) AS avg_basket_size
FROM post_peak_conversions GROUP BY 1 ORDER BY total_orders_placed DESC;""",
        "output": "Accepting Lower Amounts: 84.2% of post-peak orders · At/Above Historic Peak: 15.8% · Average post-peak checkout wallet drops back to ₹34.20",
        "insight": "84.2% of post-peak transactions convert at lower wallet balances (₹10–₹40) than the customer's prior peak, versus 15.8% that convert at or above it.",
    }
]

def base_layout(title):
    return dict(
        title=title, paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FONT_COLOR, size=11),
        margin=dict(l=30, r=20, t=40, b=30), height=280,
    )

def make_chart(block_id):
    if block_id == "Block 0":
        fig = go.Figure(go.Bar(x=[3.23, 0.0, 0.0, 2.69, 3.54, 0.0], y=SEGMENTS, orientation="h", marker_color=[RED, GREEN, GREEN, RED, RED, GREEN]))
        fig.update_layout(**base_layout("Leakage rate % by segment"))
    elif block_id == "Block 1":
        fig = go.Figure()
        fig.add_trace(go.Bar(name="T1", x=SEGMENTS, y=[391, 1323, 739, 455, 399, 38]))
        fig.update_layout(**base_layout("Net profit (₹000s) by segment + city tier"), barmode="group")
    elif block_id == "Block 2":
        fig = go.Figure()
        fig.add_trace(go.Bar(name="High wallet", x=SEGMENTS, y=[1399, 1048, 1206, 1732, 1837, 12], marker_color=ACCENT))
        fig.add_trace(go.Bar(name="Low wallet", x=SEGMENTS, y=[537, 3872, 2044, 659, 179, 58], marker_color=MUTED))
        fig.update_layout(**base_layout("High vs low wallet orders"), barmode="stack")
    elif block_id == "Block 3":
        fig = go.Figure(go.Bar(x=[4.02, 10.75, 6.73, 4.02, 3.41, 12.22], y=SEGMENTS, orientation="h"))
        fig.update_layout(**base_layout("Profit per ₹1 cashback by segment"))
        
    # ── UPDATED CHART 4: TRUE CONVERSIONS PER COHORT FROM LOG SHEET ──────────
    elif block_id == "Block 4":
        fig = go.Figure()
        # Direct structural mapping derived from query execution log
        fig.add_trace(go.Scatter(x=BANDS, y=[1.0000, 1.1148, 1.2023, 1.3269, 6.6529], name="Seg 0", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=BANDS, y=[1.1691, 1.7612, 1.9846, 1.8755, 3.2107], name="Seg 1", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=BANDS, y=[1.0161, 1.3103, 1.4685, 1.5030, 3.6152], name="Seg 2", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=BANDS, y=[1.0000, 1.0690, 1.1333, 1.2721, 5.4672], name="Seg 3", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=BANDS, y=[1.0000, 1.0000, 1.0000, 1.1250, 7.7302], name="Seg 4", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=BANDS, y=[1.4444, 1.8333, 2.0000, 1.8333, 2.8750], name="Seg 5", mode="lines+markers"))
        fig.update_layout(**base_layout("Dynamic Purchase Frequency Across Cashback Bands"))
        
    elif block_id == "Block 5":
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Early window", x=SEGMENTS, y=[687, 912, 825, 667, 611, 916], marker_color=GREEN))
        fig.add_trace(go.Bar(name="Expiry pressure", x=SEGMENTS, y=[726, 690, 676, 730, 754, 858], marker_color=RED))
        fig.update_layout(**base_layout("Avg order value: early vs pressure"), barmode="group")
    elif block_id == "Block 6":
        fig = go.Figure(go.Bar(x=SEGMENTS, y=[9.02, 0.00, 0.00, 8.40, 12.82, 0.00], marker_color=[RED, GREEN, GREEN, RED, RED, GREEN]))
        fig.update_layout(**base_layout("Deliberate expiry rate % by segment"))
    elif block_id == "Block 7":
        fig = go.Figure(go.Pie(labels=["Top 10%", "Rest 90%"], values=[17.27, 82.73], hole=0.55))
        fig.update_layout(**base_layout("Cashback concentration"))
    elif block_id == "Block 8":
        r_vals = [0.0875, -0.0921, -0.177, 0.1292, -0.0031, 0.0401]
        fig = go.Figure(go.Bar(x=SEGMENTS, y=r_vals, marker_color=[GREEN if v >= 0 else RED for v in r_vals]))
        fig.update_layout(**base_layout("Pearson r: wallet balance vs order value"))
    elif block_id == "Block 9":
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=["New", "Mid", "Mature"], y=[10.91, 10.75, 10.54], name="Seg 1"))
        fig.update_layout(**base_layout("Profit per ₹1 cashback across tenure cohorts"))
    elif block_id == "Block 10":
        fig = go.Figure(go.Bar(x=["Lower Amounts", "At/Above Peak"], y=[84.2, 15.8], marker_color=[GREEN, MUTED]))
        fig.update_layout(**base_layout("Post-Peak Conversion Volume Split %"))
    else:
        fig = go.Figure()
    
    fig.update_layout(showlegend=True)
    return fig

def render(data, skim_mode):
    st.markdown("## Chapter 11 — The SQL Investigation (Full Index)")
    
    if "flipped" not in st.session_state:
        st.session_state["flipped"] = {}

    st.markdown("---")
    st.markdown(
        """
        <div class="pm-card-dark">
            <h3 style="margin: 0; color: white;">Segment Financial & Behavioral Evidence — Blocks 0–10</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    focus = st.session_state.get("sql_focus_block")

    for block in FINANCIAL_BLOCKS:
        bid = block["id"]
        kpi = BLOCK_KPIS.get(bid, {"kpi": "N/A", "label": "No Data", "sub": ""})
        flipped = st.session_state["flipped"].get(bid, False)
        should_expand = focus is not None and focus.strip().lower() == bid.strip().lower()

        with st.expander(f"**{bid}** — {block['title']}", expanded=should_expand):
            st.markdown(f"**Question:** _{block['question']}_")
            
            k1, k2 = st.columns([2, 5])
            with k1:
                st.markdown(
                    f'<div style="background-color:{PAPER}; text-align:center; padding:1.2rem; border-radius:5px; border: 1px solid #343942;">'
                    f'<div style="font-size:2rem; font-weight:700; color:{ACCENT};">{kpi["kpi"]}</div>'
                    f'<div style="font-size:0.78rem; color:#EDEBE6; margin-top:0.3rem;">{kpi["label"]}</div>'
                    f'<div style="font-size:0.72rem; color:#9A9CA3; margin-top:0.2rem;">{kpi["sub"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with k2:
                st.info(f"**Insight:** {block['insight']}")

            btn_label = "📊 Hide chart" if flipped else "📊 Flip to see chart →"
            if st.button(btn_label, key=f"flip_{bid}"):
                st.session_state["flipped"][bid] = not flipped
                st.rerun()

            if flipped:
                st.plotly_chart(make_chart(bid), use_container_width=True)

            if "spread" in block:
                sp = block["spread"]
                st.write("")
                metric_spread(sp["label"], sp["best_name"], sp["best_val"], sp["worst_name"], sp["worst_val"], sp["gap"], sp.get("unit_note"))
                st.write("")

            sql_block(block["sql"], key=f"sql_{bid}", label="Show SQL")
            st.markdown(f"**Output:** `{block['output']}`")

    if focus is not None:
        st.session_state.sql_focus_block = None

    b1, b2, b3 = st.columns([1, 1, 1])
    with b1:
        if st.button("← Back to The Decision", use_container_width=True):
            st.session_state.chapter = "ch10"
            st.rerun()
    with b2:
        if st.button("Executive Recommendations →", use_container_width=True, type="primary"):
            st.session_state.chapter = "ch12"
            st.rerun()
    with b3:
        if st.button("↩ Cold Open", use_container_width=True):
            st.session_state.chapter = "ch0"
            st.rerun()

    sim_footer()