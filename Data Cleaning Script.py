"""
PROJECT SIPHON — Block 2: Data Cleaning
=========================================
Reads from: raw_data/
Writes to:  cleaned_data/
Also writes: outputs/cleaning_audit.md
"""

import json
import numpy as np
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

# #region agent log
_DEBUG_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug-fd0241.log')
def _dbg(location, message, data, hypothesis_id, run_id='baseline'):
    import time
    payload = {'sessionId': 'fd0241', 'runId': run_id, 'hypothesisId': hypothesis_id,
               'location': location, 'message': message, 'data': data, 'timestamp': int(time.time() * 1000)}
    with open(_DEBUG_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(payload) + '\n')
# #endregion

# Constants needed for cleaning (must match block1)
CITY_MESSY = {
    'T1': ['T1', 'Tier 1', 'tier_1', 'TIER 1'],
    'T2': ['T2', 'Tier 2', 'tier_2', 'TIER 2'],
    'T3': ['T3', 'Tier 3', 'tier_3', 'TIER 3'],
}

os.makedirs('cleaned_data', exist_ok=True)
os.makedirs('outputs',      exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK 2 — DATA CLEANING
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "═"*70)
print("BLOCK 2 — DATA CLEANING")
print("═"*70)

df_cust   = pd.read_csv('raw_data/customers.csv')
df_sess   = pd.read_csv('raw_data/daily_sessions.csv')
df_sc     = pd.read_csv('raw_data/scratch_cards.csv')
df_txn    = pd.read_csv('raw_data/transactions.csv')

issues_found = []

# ── 2a. City tier normalisation ───────────────────────────────────────────────
city_map = {v: k for k, variants in CITY_MESSY.items() for v in variants}
before_null = df_cust['city_tier'].isna().sum()
df_cust['city_tier'] = df_cust['city_tier'].map(city_map)
# Remaining NaN → mode impute (not Tier 1 hardcode — that's a silent bug)
mode_tier = df_cust['city_tier'].mode()[0]
df_cust['city_tier'].fillna(mode_tier, inplace=True)
issues_found.append(f"city_tier: {before_null} nulls fixed, {df_cust['city_tier'].nunique()} distinct values remain")

# ── 2b. Gender nulls ─────────────────────────────────────────────────────────
before_null = df_cust['gender'].isna().sum()
df_cust['gender'].fillna('Unknown', inplace=True)
issues_found.append(f"gender: {before_null} nulls → 'Unknown'")

# ── 2c. Scratch cards: distinguish intentional expiry vs true missing ─────────
# scratched=0 + card_amount_rs=NaN → card not issued (correct sparse, DO NOT impute)
# scratched=1 + deliberately_expired=1 → Hunter skip (valid, keep as-is)
# scratched=1 + card_amount_rs=NaN → API timeout injection (impute with archetype median)
api_timeout_mask = (df_sc['scratched'] == 1) & (df_sc['card_amount_rs'].isna())
n_api = api_timeout_mask.sum()
if n_api > 0:
    arch_median = df_sc[df_sc['card_amount_rs'].notna()].groupby('customer_id')['card_amount_rs'].median()
    df_sc.loc[api_timeout_mask, 'card_amount_rs'] = df_sc.loc[api_timeout_mask, 'customer_id'].map(arch_median)
    df_sc['card_amount_rs'].fillna(df_sc['card_amount_rs'].median(), inplace=True)
issues_found.append(f"scratch_cards: {n_api} API-timeout NaNs imputed")

# ── 2d. Transactions: dedup, cashback > order_value guard ─────────────────────
before = len(df_txn)
df_txn.drop_duplicates(inplace=True)
after = len(df_txn)
issues_found.append(f"transactions: {before - after} duplicates removed")

overage = (df_txn['cashback_applied'] > df_txn['order_value_rs']).sum()
if overage > 0:
    df_txn.loc[df_txn['cashback_applied'] > df_txn['order_value_rs'], 'cashback_applied'] = \
        df_txn['order_value_rs']
    df_txn['net_revenue_rs'] = df_txn['order_value_rs'] - df_txn['cashback_applied']
issues_found.append(f"transactions: {overage} cashback > order_value overages capped")

# ── 2e. Sessions: ghost sessions (0 sessions but positive duration) ───────────
ghost = (df_sess['sessions'] == 0) & (df_sess['session_dur_min'] > 0)
n_ghost = ghost.sum()
if n_ghost > 0:
    # Estimate sessions from duration using non-ghost median minutes/session
    valid = df_sess[~ghost & (df_sess['sessions'] > 0)]
    med_dur_per_sess = (valid['session_dur_min'] / valid['sessions']).median()
    df_sess.loc[ghost, 'sessions'] = np.maximum(
        1, np.round(df_sess.loc[ghost, 'session_dur_min'] / med_dur_per_sess)
    )
issues_found.append(f"sessions: {n_ghost} ghost sessions fixed")

# ── 2f. Negative net_revenue guard ────────────────────────────────────────────
neg_rev = (df_txn['net_revenue_rs'] < 0).sum()
if neg_rev > 0:
    df_txn = df_txn[df_txn['net_revenue_rs'] >= 0]
issues_found.append(f"transactions: {neg_rev} negative net_revenue rows dropped")

df_cust.to_csv('cleaned_data/customers.csv', index=False)
df_sess.to_csv('cleaned_data/daily_sessions.csv', index=False)
df_sc.to_csv('cleaned_data/scratch_cards.csv', index=False)
df_txn.to_csv('cleaned_data/transactions.csv', index=False)

print("  Cleaning log:")
for issue in issues_found:
    print(f"    • {issue}")
print("  ✅ Cleaned data written.")


# ═══════════════════════════════════════════════════════════════════════════════
# DATA AUDIT DOCUMENT — Markdown
# ═══════════════════════════════════════════════════════════════════════════════

import datetime

def build_audit_doc(issues_found, df_cust_raw, df_cust_clean,
                    df_sess_raw, df_sess_clean,
                    df_sc_raw, df_sc_clean,
                    df_txn_raw, df_txn_clean):
    """
    Generate a markdown cleaning audit document recording every transformation
    applied in Block 2, with before/after row counts and null counts.
    """
    now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    lines = [
        "# Project Siphon — Data Cleaning Audit",
        "",
        f"**Generated:** {now}  ",
        f"**Pipeline block:** Block 2 — Data Cleaning  ",
        f"**Input directory:** `raw_data/`  ",
        f"**Output directory:** `cleaned_data/`  ",
        "",
        "---",
        "",
        "## 1. Scope",
        "",
        "Four raw tables are cleaned in this block:",
        "",
        "| Table | Raw rows | Clean rows | Δ |",
        "|-------|----------|------------|---|",
        f"| `customers.csv` | {len(df_cust_raw):,} | {len(df_cust_clean):,} | {len(df_cust_clean)-len(df_cust_raw):+,} |",
        f"| `daily_sessions.csv` | {len(df_sess_raw):,} | {len(df_sess_clean):,} | {len(df_sess_clean)-len(df_sess_raw):+,} |",
        f"| `scratch_cards.csv` | {len(df_sc_raw):,} | {len(df_sc_clean):,} | {len(df_sc_clean)-len(df_sc_raw):+,} |",
        f"| `transactions.csv` | {len(df_txn_raw):,} | {len(df_txn_clean):,} | {len(df_txn_clean)-len(df_txn_raw):+,} |",
        "",
        "---",
        "",
        "## 2. Cleaning Steps",
        "",
        "### 2a. City Tier Normalisation (`customers.csv`)",
        "",
        "**Problem:** `city_tier` was injected with deliberate format variants to simulate",
        "real-world ETL inconsistencies. Values included mixed cases, spacing, and underscore",
        "variants (e.g. `T1`, `Tier 1`, `tier_1`, `TIER 1`). Additionally ~5% of rows had",
        "a null `city_tier`.",
        "",
        "**Fix applied:**",
        "- Built a canonical mapping dict from all known variants to their clean key (`T1`, `T2`, `T3`).",
        "- Applied `map()` to normalise all non-null values.",
        "- Remaining nulls (unmapped) imputed with **mode** of the cleaned column — not hardcoded",
        "  to `T1`, which would introduce silent distributional bias.",
        "",
        f"**Result:** {df_cust_raw['city_tier'].isna().sum()} nulls resolved.",
        f"Distinct values after: df_cust_clean['city_tier'].unique()",
        "",
        "---",
        "",
        "### 2b. Gender Null Imputation (`customers.csv`)",
        "",
        "**Problem:** ~4% of `gender` values were null (simulated missing demographic data).",
        "",
        "**Fix applied:** Nulls filled with string `'Unknown'` — preserves the row for",
        "downstream modelling without introducing gender distribution bias.",
        "",
        f"**Result:** {df_cust_raw['gender'].isna().sum()} nulls → `'Unknown'`.",
        "",
        "---",
        "",
        "### 2c. Scratch Card NaN Taxonomy (`scratch_cards.csv`)",
        "",
        "**Problem:** `card_amount_rs` contains two structurally distinct null types:",
        "",
        "| Null type | Condition | Meaning | Action |",
        "|-----------|-----------|---------|--------|",
        "| Structural null | `scratched=0` + `card_amount_rs=NaN` | Card not issued | **Do NOT impute** — correct sparse |",
        "| Injected mess | `scratched=1` + `card_amount_rs=NaN` | API timeout simulation | Impute |",
        "| Hunter skip | `scratched=1` + `deliberately_expired=1` | Strategic card skip | Keep as-is |",
        "",
        "**Fix applied for injected mess only:**",
        "- Identified rows where `scratched=1` AND `card_amount_rs=NaN`.",
        "- Imputed with per-customer median of non-null `card_amount_rs`.",
        "- Fallback to global column median for customers with no non-null history.",
        "",
        f"**Result:** {(df_sc_raw['scratched']==1).sum() - df_sc_raw[df_sc_raw['scratched']==1]['card_amount_rs'].notna().sum()} API-timeout NaNs imputed.",
        "",
        "---",
        "",
        "### 2d. Transaction Deduplication and Cashback Overage Cap (`transactions.csv`)",
        "",
        "**Problem 1 — Duplicates:** Exact duplicate rows can appear from upstream event",
        "stream re-delivery.",
        "",
        "**Fix:** `drop_duplicates()` on full row — keeps first occurrence.",
        "",
        f"**Result:** {len(df_txn_raw) - len(df_txn_raw.drop_duplicates()):,} duplicates removed.",
        "",
        "**Problem 2 — Cashback > Order Value:** Wallet balance applied at checkout",
        "occasionally exceeded the order value due to a simulation edge case.",
        "",
        "**Fix:** Capped `cashback_applied` at `order_value_rs`, then recomputed",
        "`net_revenue_rs = order_value_rs - cashback_applied`.",
        "",
        f"**Result:** {(df_txn_raw['cashback_applied'] > df_txn_raw['order_value_rs']).sum()} overage rows corrected.",
        "",
        "---",
        "",
        "### 2e. Ghost Session Fix (`daily_sessions.csv`)",
        "",
        "**Problem:** Rows where `sessions=0` but `session_dur_min > 0` — a physical",
        "impossibility. These are ghost records from logging failures.",
        "",
        "**Fix:** Estimated `sessions` from `session_dur_min` using the median",
        "minutes-per-session ratio computed from all valid (non-ghost) rows.",
        "Applied `max(1, round(...))` to ensure at least 1 session.",
        "",
        f"**Result:** {n_ghost} ghost sessions corrected.",
        "",
        "---",
        "",
        "### 2f. Negative Net Revenue Drop (`transactions.csv`)",
        "",
        "**Problem:** `net_revenue_rs < 0` is economically impossible — would mean",
        "cashback exceeded order value after the overage cap in step 2d.",
        "",
        "**Fix:** Rows with `net_revenue_rs < 0` are dropped entirely.",
        "",
        f"**Result:** {neg_rev} rows dropped.",
        "",
        "---",
        "",
        "## 3. What Was NOT Cleaned (Intentional Structure)",
        "",
        "| Column | Condition | Reason preserved |",
        "|--------|-----------|-----------------|",
        "| `card_amount_rs` | `scratched=0`, NaN | Card not issued — correct sparse representation |",
        "| `deliberately_expired` | `= 1` | Hunter strategic skip — valid behavioral signal |",
        "| `week_ite` | varies per week | Hunter ITE degrades 0.468→0.559 by design |",
        "| `borderline` customers | mixed behavior | 36% overlap zone required for realistic ML |",
        "",
        "---",
        "",
        "## 4. Cleaning Issue Log",
        "",
        "Summary of all issues detected and resolved:",
        "",
    ]

    for i, issue in enumerate(issues_found, 1):
        lines.append(f"{i}. {issue}")

    lines += [
        "",
        "---",
        "",
        "## 5. Column Null Counts After Cleaning",
        "",
        "### customers.csv",
        "```",
    ]
    for col in df_cust_clean.columns:
        n = df_cust_clean[col].isna().sum()
        lines.append(f"  {col:<30s}  nulls: {n}")
    lines += [
        "```",
        "",
        "### daily_sessions.csv",
        "```",
    ]
    for col in df_sess_clean.columns:
        n = df_sess_clean[col].isna().sum()
        lines.append(f"  {col:<30s}  nulls: {n}")
    lines += [
        "```",
        "",
        "### scratch_cards.csv",
        "```",
    ]
    for col in df_sc_clean.columns:
        n = df_sc_clean[col].isna().sum()
        lines.append(f"  {col:<30s}  nulls: {n}")
    lines += [
        "```",
        "",
        "### transactions.csv",
        "```",
    ]
    for col in df_txn_clean.columns:
        n = df_txn_clean[col].isna().sum()
        lines.append(f"  {col:<30s}  nulls: {n}")
    lines += [
        "```",
        "",
        "---",
        "",
        "_End of cleaning audit._",
    ]

    return "\n".join(lines)


# Re-load raw for before/after comparison in the doc
df_cust_raw_snap = pd.read_csv('raw_data/customers.csv')
df_sess_raw_snap = pd.read_csv('raw_data/daily_sessions.csv')
df_sc_raw_snap   = pd.read_csv('raw_data/scratch_cards.csv')
df_txn_raw_snap  = pd.read_csv('raw_data/transactions.csv')

audit_md = build_audit_doc(
    issues_found,
    df_cust_raw_snap, df_cust,
    df_sess_raw_snap, df_sess,
    df_sc_raw_snap,   df_sc,
    df_txn_raw_snap,  df_txn,
)

audit_path = 'outputs/cleaning_audit.md'
with open(audit_path, 'w', encoding='utf-8') as f:
    f.write(audit_md)

print(f"  ✅ Cleaning audit document written → {audit_path}")