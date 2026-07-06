# Project Siphon — Data Cleaning Audit

**Generated:** 2026-06-20 14:56 UTC  
**Pipeline block:** Block 2 — Data Cleaning  
**Input directory:** `raw_data/`  
**Output directory:** `cleaned_data/`  

---

## 1. Scope

Four raw tables are cleaned in this block:

| Table | Raw rows | Clean rows | Δ |
|-------|----------|------------|---|
| `customers.csv` | 2,000 | 2,000 | +0 |
| `daily_sessions.csv` | 112,000 | 112,000 | +0 |
| `scratch_cards.csv` | 112,000 | 112,000 | +0 |
| `transactions.csv` | 14,583 | 14,583 | +0 |

---

## 2. Cleaning Steps

### 2a. City Tier Normalisation (`customers.csv`)

**Problem:** `city_tier` was injected with deliberate format variants to simulate
real-world ETL inconsistencies. Values included mixed cases, spacing, and underscore
variants (e.g. `T1`, `Tier 1`, `tier_1`, `TIER 1`). Additionally ~5% of rows had
a null `city_tier`.

**Fix applied:**
- Built a canonical mapping dict from all known variants to their clean key (`T1`, `T2`, `T3`).
- Applied `map()` to normalise all non-null values.
- Remaining nulls (unmapped) imputed with **mode** of the cleaned column — not hardcoded
  to `T1`, which would introduce silent distributional bias.

**Result:** 97 nulls resolved.
Distinct values after: df_cust_clean['city_tier'].unique()

---

### 2b. Gender Null Imputation (`customers.csv`)

**Problem:** ~4% of `gender` values were null (simulated missing demographic data).

**Fix applied:** Nulls filled with string `'Unknown'` — preserves the row for
downstream modelling without introducing gender distribution bias.

**Result:** 83 nulls → `'Unknown'`.

---

### 2c. Scratch Card NaN Taxonomy (`scratch_cards.csv`)

**Problem:** `card_amount_rs` contains two structurally distinct null types:

| Null type | Condition | Meaning | Action |
|-----------|-----------|---------|--------|
| Structural null | `scratched=0` + `card_amount_rs=NaN` | Card not issued | **Do NOT impute** — correct sparse |
| Injected mess | `scratched=1` + `card_amount_rs=NaN` | API timeout simulation | Impute |
| Hunter skip | `scratched=1` + `deliberately_expired=1` | Strategic card skip | Keep as-is |

**Fix applied for injected mess only:**
- Identified rows where `scratched=1` AND `card_amount_rs=NaN`.
- Imputed with per-customer median of non-null `card_amount_rs`.
- Fallback to global column median for customers with no non-null history.

**Result:** 0 API-timeout NaNs imputed.

---

### 2d. Transaction Deduplication and Cashback Overage Cap (`transactions.csv`)

**Problem 1 — Duplicates:** Exact duplicate rows can appear from upstream event
stream re-delivery.

**Fix:** `drop_duplicates()` on full row — keeps first occurrence.

**Result:** 0 duplicates removed.

**Problem 2 — Cashback > Order Value:** Wallet balance applied at checkout
occasionally exceeded the order value due to a simulation edge case.

**Fix:** Capped `cashback_applied` at `order_value_rs`, then recomputed
`net_revenue_rs = order_value_rs - cashback_applied`.

**Result:** 0 overage rows corrected.

---

### 2e. Ghost Session Fix (`daily_sessions.csv`)

**Problem:** Rows where `sessions=0` but `session_dur_min > 0` — a physical
impossibility. These are ghost records from logging failures.

**Fix:** Estimated `sessions` from `session_dur_min` using the median
minutes-per-session ratio computed from all valid (non-ghost) rows.
Applied `max(1, round(...))` to ensure at least 1 session.

**Result:** 3880 ghost sessions corrected.

---

### 2f. Negative Net Revenue Drop (`transactions.csv`)

**Problem:** `net_revenue_rs < 0` is economically impossible — would mean
cashback exceeded order value after the overage cap in step 2d.

**Fix:** Rows with `net_revenue_rs < 0` are dropped entirely.

**Result:** 0 rows dropped.

---

## 3. What Was NOT Cleaned (Intentional Structure)

| Column | Condition | Reason preserved |
|--------|-----------|-----------------|
| `card_amount_rs` | `scratched=0`, NaN | Card not issued — correct sparse representation |
| `deliberately_expired` | `= 1` | Hunter strategic skip — valid behavioral signal |
| `week_ite` | varies per week | Hunter ITE degrades 0.468→0.559 by design |
| `borderline` customers | mixed behavior | 36% overlap zone required for realistic ML |

---

## 4. Cleaning Issue Log

Summary of all issues detected and resolved:

1. city_tier: 97 nulls fixed, 3 distinct values remain
2. gender: 83 nulls → 'Unknown'
3. scratch_cards: 0 API-timeout NaNs imputed
4. transactions: 0 duplicates removed
5. transactions: 0 cashback > order_value overages capped
6. sessions: 3880 ghost sessions fixed
7. transactions: 0 negative net_revenue rows dropped

---

## 5. Column Null Counts After Cleaning

### customers.csv
```
  customer_id                     nulls: 0
  city_tier                       nulls: 97
  gender                          nulls: 83
  age                             nulls: 0
  signup_tenure_weeks             nulls: 0
  historical_ltv_rs               nulls: 0
```

### daily_sessions.csv
```
  customer_id                     nulls: 0
  week                            nulls: 0
  day_in_window                   nulls: 0
  sessions                        nulls: 0
  session_dur_min                 nulls: 0
```

### scratch_cards.csv
```
  customer_id                     nulls: 0
  week                            nulls: 0
  day_in_window                   nulls: 0
  card_amount_rs                  nulls: 31152
  scratched                       nulls: 0
  deliberately_expired            nulls: 0
  added_to_wallet                 nulls: 0
```

### transactions.csv
```
  customer_id                     nulls: 0
  week                            nulls: 0
  purchase_day                    nulls: 0
  order_value_rs                  nulls: 0
  wallet_at_checkout              nulls: 0
  cashback_applied                nulls: 0
  net_revenue_rs                  nulls: 0
  full_price                      nulls: 0
```

---

_End of cleaning audit._