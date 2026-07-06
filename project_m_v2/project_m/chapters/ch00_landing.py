import streamlit as st
from ui_helpers import sim_footer, ACCENT


def render(data, skim_mode):
    st.markdown(
    f"""
    <div style="text-align:center; padding: 3rem 1rem 1rem 1rem;width: 100%;">
        <h1 style="font-size:2.6rem;">Are Customers Loyal to the Brand or Just the Cashback?</h1>
       
    </div>

    <div style="text-align:center; padding: 0.5rem 0 0.5rem 0;">
        <p style="font-size:1.0rem; color:#9A9CA3;">
        Analysis by <span style="color:#FD913C; font-weight:800;">Ketaki Shirgave</span>
        </p>
    </div>
   
   <div class="pm-card-dark" style="font-family: Arial, sans-serif; width: 100%;">
        <div style="text-align: center; padding: 1rem 0; width: 100%; margin: 0 auto;">
            <p style="font-size: 1.5rem; color: #E2E4E9; line-height: 1.5; margin: 0;">
            An end-to-end behavioral analytics system that measures <strong>cashback dependency</strong>, <strong>customer segmentation</strong>, 
            <strong>incentive ROI</strong>, <strong>leakage</strong>, and <strong>long-term retention</strong> using <strong>SQL, Python, statistical testing, and simulation</strong>.
            <br><br>
            A <strong>simulated investigation</strong> — 2,000 synthetic customer journeys modeled on real-world
            cashback-wallet mechanics. <strong>No real company data is used.</strong>
            </p>
        </div>
    </div>
  
    
    
    """,
    unsafe_allow_html=True,
)

    st.markdown("#### The mechanic, in one loop")
    c1, c2, c3, c4 = st.columns(4)
    steps = [
        ("🎯", "Scratch", "Daily card revealed, random cashback value"),
        ("👛", "Wallet", "Value lands in a wallet balance"),
        ("⏳", "7-Day Expiry", "Balance decays toward a hard cliff"),
        ("🛒", "Redemption", "Applied at checkout — or lost"),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], steps):
        with col:
            st.markdown(
                f"""<div class="pm-card"><div style="font-size:1.6rem;">{icon}</div>
                <b>{title}</b><br><span style="font-size:0.85rem;">{desc}</span></div>""",
                unsafe_allow_html=True,
            )

    st.write("")
    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("Walk Through the Findings →", type="primary", use_container_width=True):
            st.session_state.chapter = "ch1"
            st.rerun()
    with b2:
        if st.button("Jump straight to the recommendation →", use_container_width=True):
            st.session_state.chapter = "ch10"
            st.rerun()

    sim_footer()
