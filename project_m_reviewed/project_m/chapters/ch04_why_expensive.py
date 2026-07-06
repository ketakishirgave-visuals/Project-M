import streamlit as st
from ui_helpers import question_answer, sim_footer, continue_to


def render(data, skim_mode):
    st.markdown("## Chapter 4 — Then Why Is Cashback Still Expensive?")

    question_answer(
        question="If prices are honest, why does cashback still erode margin?",
        answer="Because it's distributed the same way to everyone — including people who'd have bought anyway. The waste is in targeting, not pricing.",
        badge_level="moderate",
    )

    st.markdown("#### Blanket vs. targeted distribution")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Status quo — blanket distribution**")
        segments_blanket = [
            ("Wallet Accumulators", "20%", "#3FA66B", "✅ Responds to cashback"),
            ("Organic High-Intent Buyers", "31%", "#C4573F", "❌ Buys anyway — waste"),
            ("Expiry-Driven Converters", "12%", "#D4A24C", "⚠️ Partially responsive"),
            ("Passive Expiry Converters", "18%", "#C4573F", "❌ Doesn't convert — waste"),
            ("Aggressive Expiry Converters", "13%", "#D4A24C", "⚠️ Cost-sensitive"),
            ("Premium Full-Price Loyalists", "1%", "#C4573F", "❌ Buys at full price — waste"),
        ]
        for name, pct, color, label in segments_blanket:
            st.markdown(
                f"""<div style="display:flex; align-items:center; margin-bottom:6px; gap:8px;">
                <div style="width:{pct}; min-width:40px; max-width:120px; background:{color}44;
                 border:1px solid {color}; border-radius:4px; padding:2px 6px;
                 font-size:0.75rem; color:{color}; font-weight:600;">{pct}</div>
                <div style="font-size:0.82rem; color:#EDEBE6;">{name}</div>
                <div style="font-size:0.75rem; color:#9A9CA3; margin-left:auto;">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        st.caption("Budget distributed uniformly. Roughly 50%+ goes to segments where cashback adds no incremental lift.")

    with c2:
        st.markdown("**Optimized — targeted distribution**")
        segments_targeted = [
            ("Wallet Accumulators", "45%", "#3FA66B", "+20% budget — proven causal lift"),
            ("Expiry-Driven Converters", "18%", "#D4A24C", "Maintained, not grown"),
            ("Organic High-Intent Buyers", "20%", "#D4A24C", "-20% — they convert anyway"),
            ("Aggressive Expiry Converters", "12%", "#D4A24C", "-20% — cost-optimize"),
            ("Passive Expiry Converters", "0%", "#C4573F", "Excluded — incentive trap"),
            ("Premium Full-Price Loyalists", "0%", "#C4573F", "Excluded — organic buyer"),
        ]
        for name, pct, color, label in segments_targeted:
            st.markdown(
                f"""<div style="display:flex; align-items:center; margin-bottom:6px; gap:8px;">
                <div style="width:{pct}; min-width:40px; max-width:120px; background:{color}44;
                 border:1px solid {color}; border-radius:4px; padding:2px 6px;
                 font-size:0.75rem; color:{color}; font-weight:600;">{pct}</div>
                <div style="font-size:0.82rem; color:#EDEBE6;">{name}</div>
                <div style="font-size:0.75rem; color:#9A9CA3; margin-left:auto;">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        st.caption("Budget concentrated on responsive segments. The investigation ahead establishes which segments belong in which column — and why.")

    st.markdown("---")
    st.info(
        "**The rest of this investigation builds the evidence for that right-hand column.**\n\n"
        "Chapters 5–7 establish who the segments are. Chapter 7.5 identifies who's gaming the system. "
        "Chapter 8 runs the optimization. Chapter 9 stress-tests the answer."
    )

    continue_to("ch5", "Cleaning the Evidence")
    sim_footer()
