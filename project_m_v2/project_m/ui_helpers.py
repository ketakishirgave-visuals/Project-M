"""
Project M — Shared UI helpers
Reusable rendering primitives used identically across every chapter so the
"chapter anatomy" (Question → Answer+badge → compact evidence → opt-in expandables)
stays consistent app-wide.

v2 notes: typography, tone and evidence-linking were revised in this pass.
Information architecture, chapter sequence, dark theme and navigation are unchanged.
"""
import streamlit as st

ACCENT = "#D4A24C"          # single restrained accent — CTAs, metrics, badges
BG = "#181A1F"               # deep charcoal, not pure black
CARD = "#F6F4EF"             # soft off-white
CARD_DARK = "#22252C"
TEXT_ON_DARK = "#EDEBE6"
TEXT_MUTED = "#9A9CA3"

BADGES = {
    "strong": ("✅ Strong evidence", "#3FA66B"),
    "moderate": ("🟡 Moderate evidence", "#D4A24C"),
    "exploratory": ("🔴 Exploratory only", "#C4573F"),
}


def inject_global_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: "Poppins", "Arial", "Helvetica Neue", sans-serif;
        }}

        .stApp {{
            background-color: {BG};
            color: {TEXT_ON_DARK};
            font-family: "Poppins", "Arial", "Helvetica Neue", sans-serif;
        }}
        section[data-testid="stSidebar"] {{
            background-color: #14161A;
            border-right: 1px solid #2A2D34;
        }}
        section[data-testid="stSidebar"] * {{
            font-family: "Poppins", "Arial", sans-serif;
        }}

        /* ── Type scale ──────────────────────────────────────────────────
           Headings: Poppins SemiBold/Bold, tight letter-spacing, confident weight.
           Body: Poppins Regular, generous line-height for readability.        */
        h1 {{
            font-family: "Poppins", "Arial", sans-serif;
            font-weight: 700;
            font-size: 2.1rem;
            letter-spacing: -0.01em;
            line-height: 1.25;
        }}
        h2 {{
            font-family: "Poppins", "Arial", sans-serif;
            font-weight: 600;
            font-size: 1.5rem;
            letter-spacing: -0.005em;
            line-height: 1.3;
        }}
        h3, h4 {{
            font-family: "Poppins", "Arial", sans-serif;
            font-weight: 600;
            font-size: 1.15rem;
            line-height: 1.35;
        }}
        p, li, span, div {{
            line-height: 1.6;
        }}
        .stMarkdown, .stMarkdown p {{
            font-size: 0.98rem;
        }}
        .stCaption, [data-testid="stCaptionContainer"] {{
            font-family: "Poppins", "Arial", sans-serif;
            font-weight: 400;
        }}

        .pm-card {{
            background-color: {CARD};
            color: #1C1C1C;
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            margin-bottom: 0.9rem;
            border: 1px solid #E4E0D6;
        }}
        .pm-card-dark {{
            background-color: {CARD_DARK};
            color: {TEXT_ON_DARK};
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            margin-bottom: 0.9rem;
            border: 1px solid #2E323B;
        }}
        .pm-question {{
            font-size: 1.2rem;
            font-weight: 600;
            font-family: "Poppins", "Arial", sans-serif;
            margin-bottom: 0.4rem;
            color: {TEXT_ON_DARK};
            letter-spacing: -0.005em;
        }}
        .pm-answer {{
            font-size: 1rem;
            font-weight: 400;
            line-height: 1.6;
            color: {TEXT_ON_DARK};
        }}
        .pm-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 6px;
            color: #12130f;
        }}
        .pm-tag {{
            display: inline-block;
            padding: 3px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.3px;
            text-transform: uppercase;
        }}
        .pm-footer {{
            margin-top: 2.2rem;
            padding-top: 0.8rem;
            border-top: 1px solid #2A2D34;
            font-size: 0.76rem;
            font-weight: 400;
            color: {TEXT_MUTED};
        }}
        .pm-accent {{ color: {ACCENT}; }}
        .pm-metric-big {{
            font-size: 2rem;
            font-weight: 700;
            color: {ACCENT};
            font-family: "Poppins", "Arial", sans-serif;
        }}

        /* ── Evidence chips (SQL-as-supporting-evidence, not main story) ── */
        .pm-evidence-wrap {{
            margin: 0.6rem 0 1.1rem 0;
        }}
        .pm-evidence-label {{
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            color: {TEXT_MUTED};
            margin-bottom: 0.35rem;
        }}

        /* ── Before / after cleaning demonstration ───────────────────────── */
        .pm-ba-col {{
            border-radius: 10px;
            padding: 0.8rem 1rem;
            font-size: 0.85rem;
            height: 100%;
        }}
        .pm-ba-before {{
            background: #2B211E;
            border: 1px solid #4A2E28;
        }}
        .pm-ba-after {{
            background: #1E2A22;
            border: 1px solid #2C4A38;
        }}
        .pm-ba-label {{
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.4rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def confidence_badge(level: str) -> str:
    """Returns inline HTML for a confidence badge. level in {strong, moderate, exploratory}"""
    label, color = BADGES[level]
    return f'<span class="pm-badge" style="background-color:{color};">{label}</span>'


def action_tag_color(tag: str) -> str:
    return {
        "Invest": "#3FA66B",
        "Maintain": "#7C8CA6",
        "Reduce": "#D4A24C",
        "Exclude": "#C4573F",
    }.get(tag, "#7C8CA6")


def render_action_tag(tag: str):
    color = action_tag_color(tag)
    st.markdown(
        f'<span class="pm-tag" style="background-color:{color}22; color:{color}; '
        f'border:1px solid {color};">{tag}</span>',
        unsafe_allow_html=True,
    )


def question_answer(question: str, answer: str, badge_level: str = None):
    badge_html = confidence_badge(badge_level) if badge_level else ""
    st.markdown(
        f"""
        <div class="pm-card-dark">
            <div class="pm-question">{question}</div>
            <div class="pm-answer">{answer} {badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def receipts_expander(label_suffix, question, computation, output_md, insight, key=None):
    """Standard 'View the receipts →' expander: Question → Query/computation → Output → Insight."""
    with st.expander(f"🧾 View the receipts — {label_suffix}", expanded=False):
        st.markdown("**Question this answers:**")
        st.markdown(f"_{question}_")
        st.markdown("**Query / computation:**")
        st.code(computation, language="sql" if computation.strip().upper().startswith(("SELECT", "WITH")) else "python")
        st.markdown("**Output:**")
        output_md()
        st.markdown("**Plain-language insight:**")
        st.info(insight)


def how_this_was_built(label_suffix, body_md_func):
    with st.expander(f"⚙️ How this was built — {label_suffix}", expanded=False):
        body_md_func()


def sim_footer():
    st.markdown(
        """
        <div class="pm-footer">
        🔬 Simulated dataset — 2,000 synthetic customer journeys. Not real transaction data.
        </div>
        """,
        unsafe_allow_html=True,
    )


def continue_to(chapter_key: str, chapter_label: str):
    if st.button(f"Continue to {chapter_label} →", key=f"continue_{chapter_key}"):
        st.session_state.chapter = chapter_key
        st.rerun()


def evidence_used(block_ids: list, key: str):
    """
    Compact 'Evidence Used' row. Keeps SQL out of the main narrative — each chip
    links through to the relevant block in Chapter 11 (The SQL Investigation)
    instead of inlining a query on the page the person is reading.
    block_ids: list of strings like "SQL Block 0", "SQL Block 3B"
    """
    st.markdown(
        '<div class="pm-evidence-wrap"><div class="pm-evidence-label">🧾 Evidence used</div></div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(block_ids) + 1)
    for i, block in enumerate(block_ids):
        with cols[i]:
            if st.button(block, key=f"evid_{key}_{i}", use_container_width=True):
                st.session_state.chapter = "ch11"
                st.session_state.sql_focus_block = block
                st.rerun()


def before_after(title: str, before_lines: list, after_lines: list, transform: str, caption: str = None):
    """
    Visual Before → Python transformation → After block for the data-cleaning chapter.
    before_lines / after_lines: short list of strings (rows of a mini sample table).
    transform: a short one-liner describing the Python operation applied (not full code —
    full code stays in the linked script).
    """
    st.markdown(f"**{title}**")
    b, arrow, a = st.columns([5, 1, 5])
    with b:
        st.markdown('<div class="pm-ba-col pm-ba-before">', unsafe_allow_html=True)
        st.markdown('<div class="pm-ba-label" style="color:#C4573F;">Before</div>', unsafe_allow_html=True)
        for line in before_lines:
            st.markdown(f"`{line}`")
        st.markdown("</div>", unsafe_allow_html=True)
    with arrow:
        st.markdown(
            f"""<div style="text-align:center; padding-top:2.4rem; font-size:1.4rem; color:#9A9CA3;">→</div>""",
            unsafe_allow_html=True,
        )
    with a:
        st.markdown('<div class="pm-ba-col pm-ba-after">', unsafe_allow_html=True)
        st.markdown('<div class="pm-ba-label" style="color:#3FA66B;">After</div>', unsafe_allow_html=True)
        for line in after_lines:
            st.markdown(f"`{line}`")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.8rem; color:{ACCENT}; margin:0.3rem 0 0.2rem 0;">'
        f'⚙ Python: {transform}</div>',
        unsafe_allow_html=True,
    )
    if caption:
        st.caption(caption)


def screenshot_row(items: list, caption_style=True):
    """
    items: list of (image_path, caption) tuples. Renders a row of product
    screenshots — used only where a screenshot clarifies the mechanic being
    discussed, never as decoration.
    """
    cols = st.columns(len(items))
    for col, (path, cap) in zip(cols, items):
        with col:
            st.image(path, use_container_width=True)
            if caption_style:
                st.markdown(
                    f'<div style="font-size:0.78rem; color:{TEXT_MUTED}; text-align:center; margin-top:-0.6rem;">{cap}</div>',
                    unsafe_allow_html=True,
                )
