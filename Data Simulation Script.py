"""
PROJECT SIPHON — Block 1: Simulation
=====================================
Window-correct, expiry-correct, drift-correct.
Outputs to: raw_data/, ground_truth/
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

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
RNG            = np.random.default_rng(42)
N_CUSTOMERS    = 2_000
N_WEEKS        = 8
DAYS_PER_WEEK  = 7
WALLET_CAP     = 200
STATUS_QUO_CAP = 100

ARCHETYPE_DIST  = {'sure_thing': 0.43, 'accidental_saver': 0.31, 'hunter': 0.26}
CITY_TIERS      = ['T1', 'T2', 'T3']
CITY_PROBS      = [0.35, 0.40, 0.25]
GENDERS         = ['M', 'F', 'NB']
GENDER_PROBS    = [0.48, 0.49, 0.03]

# Deliberate messy variants for city_tier (cleaning exercise)
CITY_MESSY = {
    'T1': ['T1', 'Tier 1', 'tier_1', 'TIER 1'],
    'T2': ['T2', 'Tier 2', 'tier_2', 'TIER 2'],
    'T3': ['T3', 'Tier 3', 'tier_3', 'TIER 3'],
}

# Hunter ITE degrades over 8 weeks (price sensitivity worsens with dependency)
HUNTER_ITE_TRAJ = np.linspace(0.468, 0.559, N_WEEKS)

# ITE distributions — intentional boundary overlap so ML is genuinely needed
ITE_CFG = {
    'sure_thing':       dict(mu=0.035, sigma=0.032, lo=0.001, hi=0.14),
    'accidental_saver': dict(mu=0.13,  sigma=0.085, lo=0.03,  hi=0.36),
    'hunter':           dict(mu=0.42,  sigma=0.09,  lo=0.16,  hi=0.65),
}

# Session base rates by archetype and day position (within 7-day window)
# early = days 1-3, mid = days 4-5, late = days 6-7

SESSION_CFG = {
    'sure_thing':       dict(early=(3.5, 2.5), mid=(2.0, 1.5), late=(1.5, 1.2)),
    'accidental_saver': dict(early=(2.5, 1.8), mid=(2.8, 1.8), late=(2.5, 1.8)),
    'hunter':           dict(early=(2.5, 1.5), mid=(2.4, 1.5), late=(5.0, 3.5)), # Dropped mean, jacked up SD
}

# Cross-archetype session bleed — creates ~15% overlap zone
OVERLAP_BLEED = {
    'sure_thing':       ('late',  4.2, 1.2, 0.12),
    'accidental_saver': ('late',  4.8, 1.25, 0.18),
    'hunter':           ('early', 3.4, 1.0, 0.12),
}

# ~36% borderline: behavior drawn from neighbor archetype 50% of the time
BORDERLINE_FRAC = 0.50
BEHAVIOR_NEIGHBOR = {
    'sure_thing': 'accidental_saver',
    'accidental_saver': 'hunter',
    'hunter': 'accidental_saver',
}
RULE_JCURVE_THRESHOLD = 1.85
FEATURE_OBS_NOISE = 0.25   # 4.5% measurement noise on non-protected features

os.makedirs('raw_data',     exist_ok=True)
os.makedirs('cleaned_data', exist_ok=True)
os.makedirs('ground_truth', exist_ok=True)
os.makedirs('outputs',      exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK 1 — SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "═"*70)
print("BLOCK 1 — SIMULATION")
print("═"*70)

def clipped_normal(mu, sigma, lo, hi, size=1, rng=RNG):
    out = []
    while len(out) < size:
        v = rng.normal(mu, sigma, size * 4)
        v = v[(v >= lo) & (v <= hi)]
        out.extend(v.tolist())
    return np.array(out[:size])

def draw_card(arch, rng=RNG):
    """Card amount draw — slightly better odds for Hunters (more engaged)."""
    means = {'sure_thing': 18, 'accidental_saver': 25, 'hunter': 31}
    return int(np.clip(rng.exponential(means[arch]), 1, 100))

def day_phase(d):
    """d = day within window (1–7). Returns 'early', 'mid', or 'late'."""
    if d <= 3: return 'early'
    if d <= 5: return 'mid'
    return 'late'

# ── 1a. Customer-level ground truth ──────────────────────────────────────────
print("  Generating customer profiles...")

arch_arr = RNG.choice(
    list(ARCHETYPE_DIST.keys()), N_CUSTOMERS,
    p=list(ARCHETYPE_DIST.values())
)

customers_gt   = []   # ground truth (answer key — not available to model)
customers_raw  = []   # raw observable profile

for cid_int, arch in enumerate(arch_arr):
    cid = f'C{cid_int:05d}'
    cfg = ITE_CFG[arch]
    base_ite = float(clipped_normal(cfg['mu'], cfg['sigma'], cfg['lo'], cfg['hi'])[0])

    customers_gt.append({
        'customer_id':   cid,
        'true_archetype': arch,
        'base_ite':      round(base_ite, 4),
        'ltv_rs':        round(float(RNG.uniform(3_000, 40_000)), 2),
    })

    clean_tier = RNG.choice(CITY_TIERS, p=CITY_PROBS)
    customers_raw.append({
        'customer_id':        cid,
        # Messy city tier (5% missing, rest have format variants)
        'city_tier':          RNG.choice(CITY_MESSY[clean_tier]) if RNG.random() > 0.05 else np.nan,
        # 4% missing gender
        'gender':             RNG.choice(GENDERS, p=GENDER_PROBS) if RNG.random() > 0.04 else None,
        'age':                int(RNG.integers(18, 55)),
        'signup_tenure_weeks': int(RNG.integers(1, 104)),
        'historical_ltv_rs':  round(float(RNG.uniform(3_000, 40_000)), 2),
    })

df_gt  = pd.DataFrame(customers_gt)
df_raw = pd.DataFrame(customers_raw)

# Drift candidates: ~6% of accidental_savers migrate to hunter by week 6
drift_set = set(
    df_gt[df_gt['true_archetype'] == 'accidental_saver']
    .sample(frac=0.06, random_state=42)['customer_id']
)

borderline_set = set(
    df_gt.sample(frac=BORDERLINE_FRAC, random_state=7)['customer_id']
)

# ── 1b. Event-level simulation ───────────────────────────────────────────────
print("  Simulating 56-day event loop...")

scratch_rows  = []
session_rows  = []
txn_rows      = []
weekly_rows   = []   # aggregated per customer per week (for feature engineering)
drift_log     = []

gt_lookup = df_gt.set_index('customer_id').to_dict('index')

for cid_int, arch in enumerate(arch_arr):
    cid      = f'C{cid_int:05d}'
    base_ite = gt_lookup[cid]['base_ite']

    for wk in range(1, N_WEEKS + 1):

        # ── Drift ─────────────────────────────────────────────────────────────
        cur_arch = arch
        if cid in drift_set and wk >= 6:
            # Probabilistic drift (not hard switch)
            if RNG.random() < 0.60:
                cur_arch = 'hunter'

        # NO random 1% archetype flip — that was silent label corruption

        # Effective behavior archetype (borderline customers mimic neighbors)
        beh_arch = cur_arch
        if cid in borderline_set and RNG.random() < 0.50:
            beh_arch = BEHAVIOR_NEIGHBOR.get(cur_arch, cur_arch)

        # ── Week ITE ──────────────────────────────────────────────────────────
        if cur_arch == 'hunter':
            wk_ite = float(np.clip(
                HUNTER_ITE_TRAJ[wk - 1] + RNG.normal(0, 0.025), 0.18, 0.70
            ))
        else:
            wk_ite = float(np.clip(
                base_ite + RNG.normal(0, 0.010), 0.001, 0.60
            ))

        drift_log.append({
            'customer_id':        cid,
            'week':               wk,
            'true_archetype':     arch,
            'effective_archetype': cur_arch,
            'week_ite':           round(wk_ite, 4),
            'drifted':            int(cur_arch != arch),
        })

        # ── Wallet for this window (resets each week — 7-day expiry) ──────────
        wallet = 0.0
        expired_amount  = 0.0
        collected_total = 0.0

        # ── Card scratch pattern ───────────────────────────────────────────────
        # Sure Thing: heavy days 1-3
        # Accidental Saver: spread
        # Hunter: every day, but may deliberately skip low-value cards on day 6-7
        if beh_arch == 'sure_thing':
            scratch_days_pool = [1, 2, 3]
            extra = list(RNG.choice([4, 5, 6, 7], size=RNG.integers(0, 3), replace=False))
            scratch_days = sorted(set(scratch_days_pool + extra))
        elif beh_arch == 'accidental_saver':
            n_days = RNG.integers(3, 7)
            scratch_days = sorted(RNG.choice(range(1, 8), size=n_days, replace=False).tolist())
        else:  # hunter behavior
            scratch_days = list(range(1, 8))  # scratches every day

        wk_scratch_events = []
        for d in range(1, 8):  # d = day within window (1–7), NEVER 0
            scratched = d in scratch_days

            if not scratched:
                wk_scratch_events.append({
                    'customer_id': cid, 'week': wk, 'day_in_window': d,
                    'card_amount_rs': np.nan, 'scratched': 0,
                    'deliberately_expired': 0, 'added_to_wallet': 0.0,
                })
                continue

            card_amt = draw_card(beh_arch, RNG)

            # ── Hunter window-reset deliberation ──────────────────────────────
            deliberately_expired = 0
            if beh_arch == 'hunter' and d >= 5:
                ev_next = 31
                skip_threshold = ev_next * 0.62
                if card_amt <= skip_threshold:
                    skip_prob = 0.90 if d == 7 else (0.72 if d == 6 else 0.35)
                    if RNG.random() < skip_prob:
                        deliberately_expired = 1
                        expired_amount += card_amt
                        wk_scratch_events.append({
                            'customer_id': cid, 'week': wk, 'day_in_window': d,
                            'card_amount_rs': card_amt, 'scratched': 1,
                            'deliberately_expired': 1, 'added_to_wallet': 0.0,
                        })
                        continue

            # Normal collection
            before = wallet
            wallet = min(wallet + card_amt, WALLET_CAP)
            added  = wallet - before
            collected_total += added
            wk_scratch_events.append({
                'customer_id': cid, 'week': wk, 'day_in_window': d,
                'card_amount_rs': card_amt, 'scratched': 1,
                'deliberately_expired': 0, 'added_to_wallet': round(added, 2),
            })

        scratch_rows.extend(wk_scratch_events)

        # ── Session simulation (day 1–7 within window) ────────────────────────
        wk_sessions = []
        for d in range(1, 8):
            phase     = day_phase(d)
            mu_s, sd_s = SESSION_CFG[beh_arch][phase]
            bleed = OVERLAP_BLEED.get(beh_arch)
            if bleed and phase == bleed[0] and RNG.random() < bleed[3]:
                mu_s, sd_s = bleed[1], bleed[2]
            if cid in borderline_set:
                mu_s = mu_s * RNG.uniform(0.88, 1.12)
            sessions  = max(0, round(RNG.normal(mu_s, sd_s), 2))
            dur       = max(0, round(sessions * RNG.uniform(3, 7) + RNG.normal(0, 1.5), 1))
            wk_sessions.append({
                'customer_id': cid, 'week': wk, 'day_in_window': d,
                'sessions': sessions, 'session_dur_min': dur,
            })
            session_rows.append(wk_sessions[-1])

        # ── Purchase decision ─────────────────────────────────────────────────
        purchase_day = None
        buys = False

        if beh_arch == 'sure_thing':
            purchase_day = int(RNG.choice([1, 2], p=[0.68, 0.32]))
            buys = True
            if cid in borderline_set and RNG.random() < 0.08:
                purchase_day = int(RNG.choice([3, 4, 5]))

        elif beh_arch == 'accidental_saver':
            purchase_day = int(RNG.choice(range(3, 7)))
            buys = RNG.random() > 0.22
            if cid in borderline_set and RNG.random() < 0.12:
                purchase_day = int(RNG.choice([6, 7], p=[0.4, 0.6]))

        else:  # hunter behavior
            threshold = float(clipped_normal(55, 18, 20, 100)[0])
            if wallet >= threshold:
                purchase_day = int(RNG.choice([6, 7], p=[0.38, 0.62]))
                buys = True
            else:
                purchase_day = 7
                buys = RNG.random() > wk_ite
            if cid in borderline_set and RNG.random() < 0.15:
                purchase_day = int(RNG.choice([4, 5], p=[0.45, 0.55]))
                buys = True

        # ── Transaction ───────────────────────────────────────────────────────
        order_val, cashback_applied, net_rev = 0.0, 0.0, 0.0
        if buys:
            base_aov = {'sure_thing': 920, 'accidental_saver': 680, 'hunter': 750}[beh_arch]
            order_val = round(max(150.0, float(RNG.normal(base_aov, base_aov * 0.25))), 2)
            cashback_applied = round(min(wallet, order_val), 2)
            net_rev = round(order_val - cashback_applied, 2)
            txn_rows.append({
                'customer_id':      cid, 'week': wk,
                'purchase_day':     purchase_day,
                'order_value_rs':   order_val,
                'wallet_at_checkout': round(wallet, 2),
                'cashback_applied': cashback_applied,
                'net_revenue_rs':   net_rev,
                'full_price':       int(cashback_applied < 5),
            })

        # ── Weekly aggregated features (ground-truth-adjacent, for validation) ─
        sess_by_day = {s['day_in_window']: s['sessions'] for s in wk_sessions}
        early_sess  = np.mean([sess_by_day.get(d, 0) for d in [1, 2, 3]])
        late_sess   = np.mean([sess_by_day.get(d, 0) for d in [6, 7]])
        j_curve     = late_sess / (early_sess + 0.5)  # smoothed ratio

        scratch_hit = [e['day_in_window'] for e in wk_scratch_events if e['scratched'] == 1]
        s_vel = sum(1 for d in scratch_hit if d <= 3) / max(len(scratch_hit), 1)

        exp_frac = expired_amount / (collected_total + expired_amount + 1e-9)
        tte = (7 - purchase_day) if buys else np.nan
        ccr = (cashback_applied / order_val) if order_val > 0 else 0.0

        amts = [e['added_to_wallet'] for e in wk_scratch_events if e['added_to_wallet'] > 0]
        acc_slope = float(np.polyfit(range(1, len(amts)+1), amts, 1)[0]) if len(amts) >= 2 else 0.0

        weekly_rows.append({
            'customer_id':                cid,
            'week':                       wk,
            'effective_archetype':        cur_arch,
            'week_ite':                   round(wk_ite, 4),
            'j_curve_ratio':              round(j_curve, 4),
            'scratch_velocity':           round(s_vel, 4),
            'accumulation_slope':         round(acc_slope, 4),
            'expired_cashback_fraction':  round(exp_frac, 4),
            'wallet_end_rs':              round(wallet, 2),
            'time_to_expiry_at_conversion': round(float(tte), 1) if not np.isnan(tte) else np.nan,
            'coupon_contribution_ratio':  round(ccr, 4),
            'weekly_sessions':            round(sum(s['sessions'] for s in wk_sessions), 2),
            'weekly_orders':              int(buys),
            'weekly_revenue_rs':          round(order_val, 2),
            'cashback_applied_rs':        round(cashback_applied, 2),
        })

# Save raw CSVs
df_gt.to_csv('ground_truth/customers_gt.csv', index=False)
df_raw.to_csv('raw_data/customers.csv', index=False)
pd.DataFrame(scratch_rows).to_csv('raw_data/scratch_cards.csv', index=False)
pd.DataFrame(session_rows).to_csv('raw_data/daily_sessions.csv', index=False)
pd.DataFrame(txn_rows).to_csv('raw_data/transactions.csv', index=False)
pd.DataFrame(weekly_rows).to_csv('ground_truth/weekly_features_gt.csv', index=False)
pd.DataFrame(drift_log).to_csv('ground_truth/archetype_drift.csv', index=False)

print(f"  ✅ Raw data written. Customers: {N_CUSTOMERS}, Weeks: {N_WEEKS}")

# ── Quick sim health check ────────────────────────────────────────────────────
wdf = pd.DataFrame(weekly_rows)
print("\n  SIM HEALTH CHECK:")
print(f"  Archetype dist: {df_gt['true_archetype'].value_counts(normalize=True).round(3).to_dict()}")

w1 = wdf[wdf['week'] == 1]
jc_mean = w1.groupby('effective_archetype')['j_curve_ratio'].mean()
sep = jc_mean.get('hunter', 0) / (jc_mean.get('sure_thing', 1) + 1e-9)
print(f"  j_curve separation (hunter/sure_thing): {sep:.2f}x  [target 4–6x]")

exp_means = wdf.groupby('effective_archetype')['expired_cashback_fraction'].mean()
print(f"  expired_cashback_fraction: {exp_means.round(4).to_dict()}")
print(f"  Hunter exp_frac > Sure Thing? {'✅' if exp_means.get('hunter',0) > exp_means.get('sure_thing',0) else '❌ STILL WRONG'}")

drift_pct = pd.DataFrame(drift_log)
drift_by_week = drift_pct.groupby('week')['drifted'].mean()
print(f"  Drift % by week 6–8: {drift_by_week.iloc[5:].round(3).to_dict()}")

# #region agent log
_dbg('final_script.py:sim_health', 'j_curve and exp_frac separation', {
    'jc_hunter': float(jc_mean.get('hunter', 0)), 'jc_sure_thing': float(jc_mean.get('sure_thing', 0)),
    'jc_sep_ratio': float(sep), 'exp_frac_by_arch': {k: float(v) for k, v in exp_means.items()}
}, 'H1')
# #endregion