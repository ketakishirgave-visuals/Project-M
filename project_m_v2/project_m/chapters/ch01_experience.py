import os
import streamlit as st
from ui_helpers import sim_footer, continue_to, screenshot_row

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "screens")


def render(data, skim_mode):
    st.markdown("## Chapter 1 — What Actually Happens When Someone Gets Cashback")

    st.markdown(
        """
        <div class="pm-card-dark">
            <div class="pm-question">Before we assess the economics, what does this experience actually look like?</div>
            <div class="pm-answer">Users scratch daily cards, funds sit in a wallet with a 7-day expiry,
            and redemption happens at checkout. The 7-day window is a deliberate product design choice —
            it creates a natural point of urgency ahead of every conversion decision.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Reference UI patterns")
    st.caption(
        "Representative screenshots of the gamified cashback mechanic this analysis is modeled on — "
        "shown for context, not as production data from any specific company."
    )
    screenshot_row([
        (os.path.join(ASSETS_DIR, "push_win_slot.png"), "Gamified reveal — a spin mechanic sits in front of the cashback card"),
        (os.path.join(ASSETS_DIR, "push_win_congrats.jpg"), "Confirmation moment — reinforces the reward before the value is shown"),
        (os.path.join(ASSETS_DIR, "wallet_credit.png"), "Wallet credit with an explicit expiry date printed at the point of reward"),
    ])
    st.write("")

    # Storyboard panels
    st.markdown("#### The lifecycle, step by step")
    panels = [
        ("🎴", "Day 1 — Scratch", "A card appears and the user reveals a cashback amount, typically ₹5–₹100. The reward is randomized, which keeps engagement high regardless of the amount."),
        ("👛", "Days 1–6 — Wallet Accumulation", "The amount lands in a digital wallet and can accumulate across the 7-day window as more cards are revealed."),
        ("⏳", "Day 6–7 — The Expiry Window", "The wallet balance approaches its 7-day expiry. This is where conversion pressure is structurally highest."),
        ("🛒", "Day 7 — Checkout or Expiry", "The user either applies the balance at checkout and converts, or the balance expires unused."),
        ("🔄", "Week 2 — Cycle Reset", "The window resets and a new card appears. Behavior compounds across cycles, which is why segment-level analysis matters more than any single week."),
    ]

    for i, (icon, title, desc) in enumerate(panels):
        col_icon, col_text = st.columns([1, 7])
        with col_icon:
            st.markdown(f"<div style='font-size:2rem; padding-top:6px;'>{icon}</div>", unsafe_allow_html=True)
        with col_text:
            st.markdown(f"**{title}**")
            st.markdown(f"<span style='color:#B9BBC2;'>{desc}</span>", unsafe_allow_html=True)
        if i < len(panels) - 1:
            st.markdown("<div style='margin-left:3.5rem; color:#3A3E46;'>↓</div>", unsafe_allow_html=True)

    if not skim_mode:
        st.markdown("---")
        st.markdown("#### Try it — watch a wallet balance approach the expiry cliff")
        wallet_start = st.slider("Starting wallet balance (₹)", min_value=10, max_value=200, value=80, step=5)
        cols = st.columns(7)
        for day_idx, col in enumerate(cols):
            day = day_idx + 1
            # Simple linear decay on days 5-7 to simulate urgency effect
            remaining = wallet_start if day <= 4 else wallet_start * max(0, (7 - day + 1) / 3)
            decay_pct = remaining / 200
            color = "#3FA66B" if day <= 4 else ("#D4A24C" if day == 5 else "#C4573F")
            with col:
                st.markdown(
                    f"""<div style='text-align:center; padding:8px 0;'>
                    <div style='font-size:0.72rem; color:#9A9CA3;'>Day {day}</div>
                    <div style='font-size:1.05rem; font-weight:700; color:{color};'>₹{remaining:.0f}</div>
                    <div style='height:60px; width:100%; background:#22252C; border-radius:6px; position:relative; overflow:hidden;'>
                      <div style='position:absolute; bottom:0; width:100%; height:{decay_pct*100:.0f}%;
                        background:{color}; border-radius:4px;'></div>
                    </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
        st.caption("Days 6–7 carry the highest conversion pressure — a structural feature of the mechanic, not a behavioral trait of any one user.")

    continue_to("ch2", "Is Cashback Free?")
    sim_footer()
