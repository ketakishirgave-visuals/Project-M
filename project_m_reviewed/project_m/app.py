"""
PROJECT M — Customer Segmentation & Cashback Policy Optimization
The Investigation — a case-study-style walkthrough of the full analytics pipeline.
Run with: streamlit run app.py
"""
import streamlit as st

from data_loader import load_all
from ui_helpers import inject_global_css, ACCENT

# Import each chapter module; each exposes a top-level render(data, skim_mode) function
import chapters.ch00_landing      as ch00
import chapters.ch01_experience   as ch01
import chapters.ch02_is_it_free   as ch02
import chapters.ch03_price_inflation as ch03
import chapters.ch04_why_expensive as ch04
import chapters.ch05_cleaning      as ch05
import chapters.ch06_features      as ch06
import chapters.ch07_segmentation  as ch07
import chapters.ch07b_hunter_intent as ch07b
import chapters.ch08_optimization  as ch08
import chapters.ch09_confidence    as ch09
import chapters.ch10_recommendation as ch10
import chapters.ch11_sql_index     as ch11
import chapters.ch12_executive_recommendations as ch12

st.set_page_config(
    page_title="Project M— The Investigation (Inspired by Myntra)",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

CHAPTERS = [
    ("ch0",  "0 · Cold Open",              ch00),
    ("ch1",  "1 · The Experience",         ch01),
    ("ch2",  "2 · Is Cashback Free?",      ch02),
    ("ch3",  "3 · Price Inflation Check",  ch03),
    ("ch4",  "4 · Why Still Expensive",    ch04),
    ("ch5",  "5 · Cleaning the Evidence",  ch05),
    ("ch6",  "6 · Feature Engineering",    ch06),
    ("ch7",  "7 · Six Segments",           ch07),
    ("ch7b", "7.5 · Hunter Intent",        ch07b),
    ("ch8",  "8 · Optimization Engine",    ch08),
    ("ch9",  "9 · Confidence & Range",     ch09),
    ("ch10", "10 · The Decision",          ch10),
    ("ch11", "11 · SQL Investigation",     ch11),
    ("ch12", "12 · Executive Recommendations", ch12),
]
CHAPTER_LOOKUP = {k: (label, mod) for k, label, mod in CHAPTERS}

# ── Session state defaults ──────────────────────────────────────────────────
if "chapter" not in st.session_state:
    st.session_state.chapter = "ch0"
if "skim_mode" not in st.session_state:
    st.session_state.skim_mode = False
if "show_architecture" not in st.session_state:
    st.session_state.show_architecture = False

data = load_all()


# ── Global header ─────────────────────────────────────────────────────────────
head_l, _, head_r1, head_r2, head_r3, head_r4 = st.columns([3, 2.5, 1.5, 1.5, 1.2, 1.2])
with head_l:
    if st.button("**Project M**", key="wordmark"):
        st.session_state.chapter = "ch0"
        st.rerun()
with head_r1:
    if st.button("🗺 Architecture", key="arch_btn"):
        st.session_state.show_architecture = not st.session_state.show_architecture
with head_r2:
    st.session_state.skim_mode = st.toggle(
        "Skim mode", value=st.session_state.skim_mode,
        help="Key Findings Only ⟷ Full Investigation")
with head_r3:
    if st.button("🔗 GitHub", key="github_btn", use_container_width=True):
        st.markdown("[Visit GitHub](https://github.com/ketakishirgave-visuals/Project-M)")
with head_r4:
    if st.button("💼 LinkedIn", key="linkedin_btn", use_container_width=True):
        st.markdown("[Visit LinkedIn](https://www.linkedin.com/in/ketaki-shirgave/)")
    

st.markdown(
    f'<div style="text-align:right; margin-top: 1.5rem; margin-bottom: 1.0rem;">'
    f'<span style="background:{ACCENT}22; color:{ACCENT}; border:1px solid {ACCENT}; '
    f'padding:2px 10px; border-radius:14px; font-size:0.75rem; font-weight:600;">'
    f"🔬 Simulated Data</span></div>",
    unsafe_allow_html=True,
)

# ── Architecture modal ─────────────────────────────────────────────────────────
if st.session_state.show_architecture:
    with st.container(border=True):
        st.markdown("### 🗺 Full Pipeline Architecture")
        pipeline_steps = [
            ("Block 1", "Data Simulation", "2,000 customers · 56-day event loop · 3 archetypes"),
            ("Block 2", "Data Cleaning", "Null taxonomy · dedup · ghost sessions · audit trail"),
            ("Block 3", "Feature Engineering", "12 label-blind behavioral features extracted"),
            ("Block 3.5", "Hunter Intent Classification", "Composite gaming-intent index, cross-segment"),
            ("Block 4", "Segmentation (GMM)", "6 stable clusters, validated across 4 random seeds"),
            ("Block 5", "Causality Audit", "Response score × redemption rate = defendability index"),
            ("Block 6", "Policy Optimization", "Constrained elasticity ladder, margin-maximizing"),
            ("—", "Policy Simulator", "Action-framed interactive what-if (Ch. 8)"),
            ("—", "Monte Carlo", "Range-of-outcomes confidence bands (Ch. 9)"),
            ("—", "Business Recommendation", "The memo — segment actions, limitations, next steps"),
            ("—", "Executive Recommendations", "Consulting-style recommendation list, each traced to a specific SQL block (Ch. 12)"),
        ]
        for block, name, detail in pipeline_steps:
            st.markdown(f"**`{block}`** — **{name}** · _{detail}_")
        if st.button("✕ Close", key="close_arch"):
            st.session_state.show_architecture = False
            st.rerun()

st.divider()

# ── Floating chapter rail (sidebar) ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📖 Chapters")
    for key, label, _ in CHAPTERS:
        is_active = st.session_state.chapter == key
        if st.button(
            f"**{label}**" if is_active else label,
            key=f"nav_{key}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.chapter = key
            st.rerun()
    st.markdown("---")
    st.caption("Navigation is non-linear — jump anywhere, anytime.")

# ── Render current chapter ─────────────────────────────────────────────────────
label, mod = CHAPTER_LOOKUP[st.session_state.chapter]
mod.render(data, st.session_state.skim_mode)
