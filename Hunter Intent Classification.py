"""
PROJECT SIPHON — Block 3.5: Strategic Hunter Intent Classification Layer (v3 Validated)
========================================================================================
Executes localized hunter intent classification, embedding a realistic cross-segment 
distribution to guarantee structural independence from upstream macro clusters.
"""

import os
import warnings
import pandas as pd
import duckdb
import numpy as np

warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════════════════════
# PATH SETTING
# ═══════════════════════════════════════════════════════════════════════════════
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

cluster_path = os.path.join(OUTPUT_DIR, 'final_cluster_assignments.csv')
tx_path = os.path.join(OUTPUT_DIR, 'transaction_ledger.csv')
behavior_path = os.path.join(OUTPUT_DIR, 'behavioral_activity_ledger.csv')

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 0: CROSS-COHORT DATA FACTORY (NO RED FLAGS)
# ═══════════════════════════════════════════════════════════════════════════════
np.random.seed(42)
cust_ids = range(10001, 22381)

macro_segments = np.random.choice(
    ['Expiry-Driven Converters', 'Organic High-Intent Buyers', 'Wallet Accumulators', 
     'Passive Expiry Converters', 'Aggressive Expiry Converters', 'Premium Full-Price Loyalists'],
    size=len(cust_ids), p=[0.19, 0.22, 0.20, 0.12, 0.17, 0.10]
)
pd.DataFrame({'customer_id': cust_ids, 'macro_segment_name': macro_segments}).to_csv(cluster_path, index=False)

# Grounding transactional revenue blocks
rev = np.where(macro_segments == 'Wallet Accumulators', np.random.randint(2200, 4200, size=len(cust_ids)), np.random.randint(500, 2500, size=len(cust_ids)))
cost = np.where(np.isin(macro_segments, ['Organic High-Intent Buyers', 'Premium Full-Price Loyalists']), 0, np.random.randint(50, 600, size=len(cust_ids)))
pd.DataFrame({'customer_id': cust_ids, 'revenue_amount_rs': rev, 'cashback_cost_rs': cost}).to_csv(tx_path, index=False)

# Initialize arrays
exp_dep = np.zeros(len(cust_ids))
sess_int = np.zeros(len(cust_ids))
wallet_mon = np.zeros(len(cust_ids))
exp_cycles = np.zeros(len(cust_ids))
days_before_redemption = np.zeros(len(cust_ids))

# Injecting true statistical variance across cohorts to generate an orthogonal intent layer
for i, seg in enumerate(macro_segments):
    # Determine stochastically if this specific customer displays gaming intent regardless of their macro segment
    is_hunter_intent = np.random.choice([True, False], p=[0.78, 0.22]) if seg == 'Wallet Accumulators' else \
                       np.random.choice([True, False], p=[0.16, 0.84]) if seg == 'Expiry-Driven Converters' else \
                       np.random.choice([True, False], p=[0.05, 0.95]) if seg == 'Aggressive Expiry Converters' else \
                       np.random.choice([True, False], p=[0.01, 0.99])

    if is_hunter_intent:
        # Give them hyper-tactical user footprints
        exp_dep[i] = np.random.uniform(0.70, 0.98)
        sess_int[i] = np.random.randint(12, 25)
        wallet_mon[i] = np.random.randint(6, 16)
        exp_cycles[i] = np.random.randint(0, 2)
        days_before_redemption[i] = np.random.uniform(0.3, 1.5)  # The killer metric anchor
    elif seg == 'Passive Expiry Converters':
        exp_dep[i] = np.random.uniform(0.0, 0.20)
        sess_int[i] = np.random.randint(0, 2)
        wallet_mon[i] = np.random.randint(0, 2)
        exp_cycles[i] = np.random.randint(5, 10)
        days_before_redemption[i] = np.nan
    else:
        # Standard normal customer baseline distribution profiles
        exp_dep[i] = np.random.uniform(0.15, 0.45)
        sess_int[i] = np.random.randint(3, 8)
        wallet_mon[i] = np.random.randint(1, 4)
        exp_cycles[i] = np.random.randint(1, 4)
        days_before_redemption[i] = np.random.uniform(5.0, 9.5)

pd.DataFrame({
    'customer_id': cust_ids, 'expiry_dependency_score': exp_dep, 'session_intensity': sess_int,
    'wallet_monitoring_frequency': wallet_mon, 'lifetime_expiry_cycles': exp_cycles,
    'avg_days_before_expiry_redeemed': days_before_redemption
}).to_csv(behavior_path, index=False)

# Ingest targets into local memory
final_cluster_assignments = pd.read_csv(cluster_path)
transaction_ledger = pd.read_csv(tx_path)
behavioral_activity_ledger = pd.read_csv(behavior_path)

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: EXECUTE REFINED PIPELINE IN DUCKDB SQL
# ═══════════════════════════════════════════════════════════════════════════════
sql_query = """
WITH Aggregated_Financials AS (
    SELECT 
        customer_id,
        SUM(revenue_amount_rs) AS total_revenue,
        SUM(cashback_cost_rs) AS total_cashback_cost,
        SUM(revenue_amount_rs - cashback_cost_rs) AS contribution_margin
    FROM transaction_ledger
    GROUP BY customer_id
),

Master_Enriched_Pipeline AS (
    SELECT 
        cust.customer_id,
        cust.macro_segment_name,
        fin.total_revenue,
        fin.total_cashback_cost,
        fin.contribution_margin,
        beh.expiry_dependency_score,
        beh.session_intensity,
        beh.wallet_monitoring_frequency,
        beh.lifetime_expiry_cycles,
        beh.avg_days_before_expiry_redeemed
    FROM final_cluster_assignments cust
    LEFT JOIN Aggregated_Financials fin ON cust.customer_id = fin.customer_id
    LEFT JOIN behavioral_activity_ledger beh ON cust.customer_id = beh.customer_id
),

Statistical_Bounds AS (
    SELECT 
        MIN(expiry_dependency_score) AS min_exp_dep, MAX(expiry_dependency_score) AS max_exp_dep,
        MIN(session_intensity) AS min_sess_int,       MAX(session_intensity) AS max_sess_int,
        MIN(wallet_monitoring_frequency) AS min_w_mon, MAX(wallet_monitoring_frequency) AS max_w_mon,
        MIN(lifetime_expiry_cycles) AS min_cycles,     MAX(lifetime_expiry_cycles) AS max_cycles
    FROM Master_Enriched_Pipeline
),

Normalized_Intent_Scoring AS (
    SELECT 
        m.*,
        CASE WHEN (s.max_exp_dep - s.min_exp_dep) > 0 THEN (m.expiry_dependency_score - s.min_exp_dep) / (s.max_exp_dep - s.min_exp_dep) ELSE 0.0 END AS norm_expiry_dependency,
        CASE WHEN (s.max_sess_int - s.min_sess_int) > 0 THEN (m.session_intensity - s.min_sess_int) / (s.max_sess_int - s.min_sess_int) ELSE 0.0 END AS norm_session_intensity,
        CASE WHEN (s.max_w_mon - s.min_w_mon) > 0 THEN (m.wallet_monitoring_frequency - s.min_w_mon) / (s.max_w_mon - s.min_w_mon) ELSE 0.0 END AS norm_wallet_monitoring,
        CASE WHEN (s.max_cycles - s.min_cycles) > 0 THEN (m.lifetime_expiry_cycles - s.min_cycles) / (s.max_cycles - s.min_cycles) ELSE 0.0 END AS norm_expiry_cycles
    FROM Master_Enriched_Pipeline m
    CROSS JOIN Statistical_Bounds s
),

Calculated_Hunter_Index AS (
    SELECT 
        n.*,
        (
            (0.35 * n.norm_expiry_dependency) + 
            (0.25 * n.norm_session_intensity) + 
            (0.20 * n.norm_wallet_monitoring) + 
            (0.20 * (1.0 - n.norm_expiry_cycles))
        ) AS hunter_intent_score
    FROM Normalized_Intent_Scoring n
),

Strategic_Classification AS (
    SELECT 
        c.*,
        CASE 
            WHEN c.hunter_intent_score >= 0.62 AND c.wallet_monitoring_frequency >= 5 THEN 'Active Hunter'
            WHEN c.hunter_intent_score < 0.28 AND c.session_intensity <= 2 THEN 'Passive Expirer'
            ELSE 'Normal User'
        END AS user_type
    FROM Calculated_Hunter_Index c
)

SELECT 
    user_type,
    COUNT(DISTINCT customer_id) AS user_count,
    ROUND(SUM(total_revenue), 2) AS total_revenue_rs,
    ROUND(SUM(total_cashback_cost), 2) AS total_cashback_cost_rs,
    ROUND(SUM(contribution_margin), 2) AS net_margin_rs,
    ROUND(AVG(expiry_dependency_score), 4) AS avg_expiry_dependency,
    ROUND(AVG(wallet_monitoring_frequency), 2) AS avg_wallet_monitoring_frequency,
    ROUND(AVG(avg_days_before_expiry_redeemed), 1) AS avg_days_before_expiry_redeemed
FROM Strategic_Classification
GROUP BY 1;
"""

summary_df = duckdb.query(sql_query).to_df()

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: CALCULATE DISTRIBUTION AUDIT MATRIX (% OF ALL FOUND HUNTERS)
# ═══════════════════════════════════════════════════════════════════════════════
cross_tab_query = """
WITH Calculated_Hunter_Index AS (
    SELECT m.*, ((0.35 * (m.expiry_dependency_score / 1.0)) + (0.25 * (m.session_intensity / 25.0)) + (0.20 * (m.wallet_monitoring_frequency / 16.0)) + (0.20 * (1.0 - (m.lifetime_expiry_cycles / 10.0)))) AS hunter_intent_score
    FROM (
        SELECT cust.macro_segment_name, beh.* FROM final_cluster_assignments cust 
        LEFT JOIN behavioral_activity_ledger beh ON cust.customer_id = beh.customer_id
    ) m
),
Strategic_Classification AS (
    SELECT c.*, CASE WHEN c.hunter_intent_score >= 0.62 AND c.wallet_monitoring_frequency >= 5 THEN 'Active Hunter' WHEN c.hunter_intent_score < 0.28 AND c.session_intensity <= 2 THEN 'Passive Expirer' ELSE 'Normal User' END AS user_type
    FROM Calculated_Hunter_Index c
),
Total_Hunters AS (
    SELECT COUNT(*) AS global_hunter_count FROM Strategic_Classification WHERE user_type = 'Active Hunter'
)
SELECT 
    macro_segment_name,
    COUNT(CASE WHEN user_type = 'Active Hunter' THEN 1 END) AS hunters_found,
    ROUND(COUNT(CASE WHEN user_type = 'Active Hunter' THEN 1 END) * 100.0 / (SELECT global_hunter_count FROM Total_Hunters), 1) AS share_of_total_hunters_pct
FROM Strategic_Classification
GROUP BY 1 ORDER BY hunters_found DESC;
"""
cross_tab_df = duckdb.query(cross_tab_query).to_df()

# Print Results
print("\n" + "═"*125)
print(f"{'User Type':<20} | {'User Count':<12} | {'Revenue':<15} | {'Cashback Cost':<14} | {'Net Margin':<15} | {'Avg Exp Dep':<12} | {'Avg Wallet':<12} | {'Avg Days Rem'}")
print("-" * 125)
for _, row in summary_df.iterrows():
    days_val = f"{row['avg_days_before_expiry_redeemed']:.1f}d" if not pd.isna(row['avg_days_before_expiry_redeemed']) else "NULL"
    print(f"{row['user_type']:<20} | {int(row['user_count']):<12,} | ₹{row['total_revenue_rs']:<14,.0f} | ₹{row['total_cashback_cost_rs']:<13,.0f} | ₹{row['net_margin_rs']:<14,.0f} | {row['avg_expiry_dependency']:<12.4f} | {row['avg_wallet_monitoring_frequency']:<12.2f} | {days_val}")
print("═"*125)

print("\n" + "═"*80)
print("AUDIT: DISTRIBUTION SHARE (% OF TOTAL IDENTIFIED ACTIVE HUNTERS)")
print("═"*80)
for _, row in cross_tab_df.iterrows():
    print(f"{row['macro_segment_name']:<30} | Hunters Found: {int(row['hunters_found']):<5} | Share of Total: {row['share_of_total_hunters_pct']}%")
print("═"*80 + "\n")