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
            <div class="pm-answer">Users scratch daily cards, funds sit in a wallet with a rolling 7-day expiry, 
            and redemption happens at checkout. The 7-day window is a deliberate product design choice — 
            it creates a moving portfolio of rewards that builds continuous conversion urgency.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Cashback Journey in Practice")
    st.caption(
        "Representative screenshots of the gamified cashback mechanic this analysis is modeled on -> "
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
        ("🎴", "Day 1 — Scratch & Earn", "A card appears and the user reveals a cashback amount. This individual reward starts its independent 7-day validity countdown."),
        ("👛", "Days 2–6 — Portfolio Accumulation", "The digital wallet acts as a moving ledger, accumulating daily reward inflows while tracking unique expiry timestamps for each reward tier."),
        ("⏳", "Day 7+ — The First Expiry Deadline", "The earliest earned rewards reach their 7-day expiration cliff. Unused balances vanish automatically, creating localized behavioral spikes."),
        ("🛒", "Checkout Realization", "Users manage a rolling balance pool. Urgency is structural: high-volume consumers optimize conversions to capture fading tranches rather than nominal balances."),
        ("🔄", "Cycle Reset", "New incentives enter as old ones cycle out. This continuous, overlapping pattern creates the distinct behavioral tracks mapped throughout this project."),
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
        st.markdown("#### Interactive Rolling Cashback Expiry Simulator")
        st.markdown(
            """
            <span style='color:#B9BBC2;'>Each cashback reward remains valid for seven days. Every day new rewards 
            enter the wallet while rewards earned seven days earlier expire. This rolling expiry creates continuous 
            redemption pressure and is the core behavioral mechanism explored throughout the project.</span>
            """,
            unsafe_allow_html=True,
        )
        st.write("")

        # Configure standardized reward flows
        daily_reward_inflow = st.slider("Simulated Daily Reward Amount (₹)", min_value=10, max_value=50, value=30, step=5)
        
        # Array simulating state across a timeline
        # Index represents simulated days; values represent current active ledger state
        st.markdown("**Simulated 8-Day Rolling Balance Tracking**")
        cols = st.columns(8)
        
        for day_idx in range(8):
            day = day_idx + 1
            
            # Mathematical rolling pool simulation: 
            # On day D, you have accumulated 'D' days worth of cards, capped at a max of 7 unexpired days.
            active_days_count = min(day, 7)
            current_wallet_balance = active_days_count * daily_reward_inflow
            
            # Isolate expired status flag
            expired_amount = daily_reward_inflow if day == 8 else 0
            
            # Design visual indicators (Green = accumulating, Yellow = peak pressure, Red = active expiration)
            if day <= 4:
                color = "#3FA66B"
                status_text = "Accumulating"
            elif day <= 7:
                color = "#D4A24C"
                status_text = "Peak Pressure"
            else:
                color = "#C4573F"
                status_text = f"Day 1 Expiries (-₹{expired_amount})"

            # Dynamic bar scale mapping to preserve UI layouts
            bar_pct = min(100, int((current_wallet_balance / 350) * 100))

            with cols[day_idx]:
                st.markdown(
                    f"""<div style='text-align:center; padding:8px 0; background:#1C1E24; border-radius:8px; border: 1px solid #2D3139;'>
                    <div style='font-size:0.75rem; color:#9A9CA3; font-weight:600;'>Day {day}</div>
                    <div style='font-size:1.15rem; font-weight:700; color:{color}; margin: 4px 0;'>₹{current_wallet_balance}</div>
                    <div style='font-size:0.62rem; color:#B9BBC2; height:20px;'>{status_text}</div>
                    <div style='height:80px; width:80%; background:#121418; border-radius:4px; margin: 8px auto 0 auto; position:relative; overflow:hidden;'>
                      <div style='position:absolute; bottom:0; width:100%; height:{bar_pct}%;
                        background:{color}; border-radius:2px; transition: height 0.3s ease;'></div>
                    </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
        
        st.write("")
        st.caption(
            "💡 **Mechanism Insight:** Notice that on Day 8, the balance flatlines. "
            "Even though a new reward enters, the Day 1 reward (earned 7 days prior) has reached its deadline and drops off. "
            "This forces users to continuously balance an active portfolio of expiring assets."
        )

    continue_to("ch2", "Is Cashback Free?")
    sim_footer()
