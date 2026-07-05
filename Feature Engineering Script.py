"""
PROJECT SIPHON — Block 3: Behavioral Feature Engineering (PURE UNSUPERVISED)
==========================================================================
Reads from: cleaned_data/
Writes to:   outputs/features_raw.csv, outputs/features_full_metadata.csv, outputs/feature_audit.txt
Note: Completely blind to ground truth. Built for un-biased clustering.
"""

import json
import numpy as np
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

os.makedirs('outputs', exist_ok=True)

print("\n" + "═"*70)
print("BLOCK 3 — BEHAVIORAL FEATURE ENGINEERING (LABEL-BLIND)")
print("═"*70)

# Load pipeline dependencies (Strictly behavioral records only)
df_cust = pd.read_csv('cleaned_data/customers.csv')
df_sess = pd.read_csv('cleaned_data/daily_sessions.csv')
df_sc   = pd.read_csv('cleaned_data/scratch_cards.csv')
df_txn  = pd.read_csv('cleaned_data/transactions.csv')

early_days = [1, 2, 3]
late_days  = [6, 7]

audit_log = []

# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 1: j_curve_ratio & j_curve_std
# ═══════════════════════════════════════════════════════════════════════════════
sess_early = df_sess[df_sess['day_in_window'].isin(early_days)]\
    .groupby(['customer_id', 'week'])['sessions'].mean().reset_index(name='early_sess')
sess_late  = df_sess[df_sess['day_in_window'].isin(late_days)]\
    .groupby(['customer_id', 'week'])['sessions'].mean().reset_index(name='late_sess')

jc_df = sess_early.merge(sess_late, on=['customer_id', 'week'], how='inner')
jc_df['jc_week'] = jc_df['late_sess'] / jc_df['early_sess'].clip(lower=0.5)

jc_feat = jc_df.groupby('customer_id')['jc_week'].agg(
    j_curve_ratio='median',
    j_curve_std='std'
).reset_index()

audit_log.append(f"j_curve_ratio: {jc_feat['j_curve_ratio'].describe().to_dict()}")

# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 2: scratch_velocity
# ═══════════════════════════════════════════════════════════════════════════════
sc_scratched = df_sc[df_sc['scratched'] == 1].copy()
sc_scratched['is_early'] = sc_scratched['day_in_window'].isin(early_days).astype(int)

sv_feat = sc_scratched.groupby('customer_id').agg(
    scratch_velocity=('is_early', 'mean')
).reset_index()

audit_log.append(f"scratch_velocity: {sv_feat['scratch_velocity'].describe().to_dict()}")

# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 3: expired_cashback_fraction
# ═══════════════════════════════════════════════════════════════════════════════
sc_scratched_sum = df_sc[df_sc['scratched'] == 1]\
    .groupby('customer_id')['card_amount_rs'].sum().reset_index(name='scratched_total')
sc_expired_sum = df_sc[df_sc['deliberately_expired'] == 1]\
    .groupby('customer_id')['card_amount_rs'].sum().reset_index(name='expired_total')

exp_feat = df_cust[['customer_id']].merge(sc_scratched_sum, on='customer_id', how='left')\
                                   .merge(sc_expired_sum, on='customer_id', how='left')
exp_feat.fillna(0, inplace=True)
exp_feat['expired_cashback_fraction'] = exp_feat['expired_total'] / exp_feat['scratched_total'].clip(lower=1e-6)
exp_feat = exp_feat[['customer_id', 'expired_cashback_fraction']]

audit_log.append(f"expired_cashback_fraction: {exp_feat['expired_cashback_fraction'].describe().to_dict()}")

# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 4: wallet_balance_slope
# ═══════════════════════════════════════════════════════════════════════════════
def compute_wallet_balance_slope(customer_id, df_sc, df_txn):
    cust_sc = df_sc[(df_sc['customer_id'] == customer_id) & (df_sc['added_to_wallet'] > 0)]
    weekly_earned = cust_sc.groupby('week')['added_to_wallet'].sum()
    
    cust_txn = df_txn[(df_txn['customer_id'] == customer_id) & (df_txn['cashback_applied'] > 0)]
    weekly_spent = cust_txn.groupby('week')['cashback_applied'].sum()
    
    all_weeks = sorted(list(set(weekly_earned.index).union(set(weekly_spent.index))))
    if len(all_weeks) < 2:
        return 0.0
        
    net_balances = []
    running_balance = 0.0
    
    for w in all_weeks:
        earned = weekly_earned.get(w, 0.0)
        spent = weekly_spent.get(w, 0.0)
        running_balance += (earned - spent)
        net_balances.append(running_balance)
        
    coeffs = np.polyfit(range(len(net_balances)), net_balances, 1)
    return float(coeffs[0])

wallet_slopes = []
for cid in df_cust['customer_id']:
    slope = compute_wallet_balance_slope(cid, df_sc, df_txn)
    wallet_slopes.append({'customer_id': cid, 'wallet_balance_slope': slope})

wallet_feat = pd.DataFrame(wallet_slopes)
audit_log.append(f"wallet_balance_slope: {wallet_feat['wallet_balance_slope'].describe().to_dict()}")

# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 5: time_to_expiry_at_conversion
# ═══════════════════════════════════════════════════════════════════════════════
tte_feat = df_txn.groupby('customer_id').agg(
    time_to_expiry_at_conversion=('purchase_day', lambda x: float((7 - x).median()))
).reset_index()

audit_log.append(f"time_to_expiry_at_conversion: {tte_feat['time_to_expiry_at_conversion'].describe().to_dict()}")

# ═══════════════════════════════════════════════════════════════════════════════
# FEATURES 6-9: Transaction & Engagement Densities
# ═══════════════════════════════════════════════════════════════════════════════
txn_agg = df_txn.groupby('customer_id').agg(
    total_spend=('order_value_rs', 'sum'),
    total_cashback=('cashback_applied', 'sum'),
    tx_count=('week', 'count'),
).reset_index()

txn_agg['cashback_intensity'] = txn_agg['total_cashback'] / txn_agg['total_spend'].clip(lower=1.0)

sess_agg = df_sess.groupby('customer_id').agg(
    total_sessions=('sessions', 'sum'),
    active_days=('day_in_window', 'count')
).reset_index()

behavioral_metrics = df_cust[['customer_id']].merge(txn_agg, on='customer_id', how='left')\
                                             .merge(sess_agg, on='customer_id', how='left')
behavioral_metrics.fillna(0, inplace=True)

behavioral_metrics['spend_per_session'] = behavioral_metrics['total_spend'] / behavioral_metrics['total_sessions'].clip(lower=1.0)
behavioral_metrics['conversion_rate'] = behavioral_metrics['tx_count'] / behavioral_metrics['total_sessions'].clip(lower=1.0)
behavioral_metrics['session_density'] = behavioral_metrics['total_sessions'] / behavioral_metrics['active_days'].clip(lower=1.0)

audit_log.append(f"spend_per_session: {behavioral_metrics['spend_per_session'].describe().to_dict()}")
audit_log.append(f"conversion_rate: {behavioral_metrics['conversion_rate'].describe().to_dict()}")
audit_log.append(f"session_density: {behavioral_metrics['session_density'].describe().to_dict()}")

# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 10: full_price_rate
# ═══════════════════════════════════════════════════════════════════════════════
df_txn['is_full_price'] = (df_txn['cashback_applied'] < 5).astype(int)
fp_feat = df_txn.groupby('customer_id').agg(
    full_price_rate=('is_full_price', 'mean')
).reset_index()

audit_log.append(f"full_price_rate: {fp_feat['full_price_rate'].describe().to_dict()}")

# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 11: late_session_intensity
# ═══════════════════════════════════════════════════════════════════════════════
late_sess_feat = df_sess[df_sess['day_in_window'].isin(late_days)]\
    .groupby('customer_id')['sessions'].mean().reset_index(name='late_session_intensity')

audit_log.append(f"late_session_intensity: {late_sess_feat['late_session_intensity'].describe().to_dict()}")

# ═══════════════════════════════════════════════════════════════════════════════
# CONSOLIDATION & RAW MATRICES GENERATION
# ═══════════════════════════════════════════════════════════════════════════════
feat = df_cust[['customer_id', 'age', 'signup_tenure_weeks']].copy()

feature_dfs = [
    jc_feat, sv_feat, exp_feat, wallet_feat, tte_feat, 
    behavioral_metrics[['customer_id', 'cashback_intensity', 'spend_per_session', 'conversion_rate', 'session_density']], 
    fp_feat, late_sess_feat
]

for df_f in feature_dfs:
    feat = feat.merge(df_f, on='customer_id', how='left')

# Impute behavioral records missing updates using population median
numeric_cols = feat.select_dtypes(include=[np.number]).columns.tolist()
for col in numeric_cols:
    feat[col].fillna(feat[col].median(), inplace=True)

# Select all 12 surviving clustering features
CLUSTERING_FEATURES = [
    'j_curve_ratio', 'j_curve_std', 'scratch_velocity', 'expired_cashback_fraction',
    'time_to_expiry_at_conversion', 'cashback_intensity', 'full_price_rate',
    'wallet_balance_slope', 'late_session_intensity', 'spend_per_session',
    'conversion_rate', 'session_density'
]

X_raw = feat[CLUSTERING_FEATURES].copy()

print(f"\n  Feature matrix shape: {X_raw.shape}")
print(f"  Surviving features extracted: {len(CLUSTERING_FEATURES)}")

# Save outputs — NO SCALING. Pure, un-adulterated raw metrics.
X_raw.to_csv('outputs/features_raw.csv', index=False)
feat.to_csv('outputs/features_full_metadata.csv', index=False)

print(f"\n  ✅ Pure, Unscaled Raw Features written → outputs/features_raw.csv")
print(f"  ✅ Metadata Master Frame written → outputs/features_full_metadata.csv")

# Save Audit Log
audit_txt = "\n".join(["FEATURE ENGINEERING AUDIT — Unscaled Behavioral Distributions", "="*70, ""] + audit_log)
with open('outputs/feature_audit.txt', 'w') as f:
    f.write(audit_txt)
print(f"  ✅ Feature audit log generated → outputs/feature_audit.txt")