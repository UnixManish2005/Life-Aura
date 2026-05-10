"""
Life Aura – Main entry point.
Run with: streamlit run app.py
"""

import os
import sys
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Path setup ───────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from utils.db import init_db
from utils.auth import signup_user, login_user, logout

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=" Life Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "**welcome to Life Dashboard** – Your personal productivity hub.",
    },
)

# ── Inject custom CSS ─────────────────────────────────────────────────────────
css_path = os.path.join(BASE_DIR, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Init DB ───────────────────────────────────────────────────────────────────
init_db()

# ── Session defaults ──────────────────────────────────────────────────────────
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("user_id",   None)
st.session_state.setdefault("username",  None)


# ════════════════════════════════════════════════════════════════════════════
# AUTH SCREENS
# ════════════════════════════════════════════════════════════════════════════

def show_auth():
    """Login / Signup screen shown when user is not authenticated."""
    st.markdown(
        """
        <div style="text-align:center;padding:2rem 0 1rem">
            <div style="font-size:3.5rem">🌱</div>
            <h1 style="font-family:'Space Grotesk',sans-serif;font-size:2.5rem;
                       background:linear-gradient(135deg,#6366f1,#22d3ee);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                       margin:0">Welcome To Life Aura</h1>
            <p style="color:#94a3b8;margin-top:0.5rem">
                Your personal productivity & expense analytics hub
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        tab_login, tab_signup = st.tabs(["🔐 Login", "✨ Sign Up"])

        # ── Login ──────────────────────────────────────────────────────────
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                success, msg, user = login_user(username, password)
                if success:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"]   = user.id
                    st.session_state["username"]  = user.username
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

            st.caption("If you dont have an Account : create an account via Sign Up tab.")

        # ── Sign Up ────────────────────────────────────────────────────────
        with tab_signup:
            with st.form("signup_form"):
                new_user  = st.text_input("Username")
                new_email = st.text_input("Email")
                new_pw    = st.text_input("Password", type="password")
                cfm_pw    = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                if new_pw != cfm_pw:
                    st.error("Passwords do not match.")
                elif len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    success, msg = signup_user(new_user, new_email, new_pw)
                    if success:
                        st.success(msg + " Please login.")
                    else:
                        st.error(msg)

    # Features grid
    st.divider()
    st.markdown('<p style="text-align:center;color:#94a3b8">Features</p>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    for col, icon, title, desc in [
        (f1, "📋", "Task Planner",   "Organise your day"),
        (f2, "🔥", "Habit Tracker",  "Build streaks"),
        (f3, "💰", "Expense Tracker","Manage finances"),
        (f4, "🤖", "AI Insights",    "Smart coaching"),
    ]:
        col.markdown(
            f'<div class="dash-card" style="text-align:center">'
            f'<div style="font-size:2rem">{icon}</div>'
            f'<strong>{title}</strong><br>'
            f'<span style="color:#94a3b8;font-size:0.85rem">{desc}</span>'
            f'</div>',
            unsafe_allow_html=True
        )


# ════════════════════════════════════════════════════════════════════════════
# MAIN APP (authenticated)
# ════════════════════════════════════════════════════════════════════════════

PAGES = {
    "🏠 Dashboard":       ("dashboard",   "modules.dashboard"),
    "📋 Daily Planner":   ("planner",     "modules.planner"),
    "🔥 Habit Tracker":   ("habits",      "modules.habits"),
    "💰 Expense Tracker": ("expenses",    "modules.expenses"),
    "🎯 Goals":           ("goals",       "modules.goals"),
    "📊 Analytics":       ("analytics",   "modules.analytics"),
    "🤖 AI Insights":     ("ai_insights", "modules.ai_insights"),
    "📄 Reports":         ("reports",     "modules.reports"),
    "⚙️ Settings":        ("settings",    "modules.settings"),
}


def show_app():
    """Main application shell with sidebar navigation."""
    with st.sidebar:
        # Brand
        st.markdown(
            '<div style="padding:12px 0 8px">'
            '<span style="font-size:1.5rem">🚀</span> '
            '<span style="font-family:\'Space Grotesk\',sans-serif;font-weight:700;'
            'font-size:1.1rem;background:linear-gradient(135deg,#6366f1,#22d3ee);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
            'AI Life Dashboard</span>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<p style="color:#94a3b8;font-size:0.8rem;margin-top:-4px">'
            f'👤 {st.session_state["username"]}</p>',
            unsafe_allow_html=True
        )
        st.divider()

        selected = st.radio(
            "Navigate",
            list(PAGES.keys()),
            label_visibility="collapsed"
        )
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    # ── Render selected page ──────────────────────────────────────────────────
    _, module_path = PAGES[selected]
    import importlib
    mod = importlib.import_module(module_path)
    mod.render()


# ════════════════════════════════════════════════════════════════════════════
# Entry
# ════════════════════════════════════════════════════════════════════════════

if st.session_state["logged_in"]:
    show_app()
else:
    show_auth()

# ════════════════════════════════════════════════════════════════════════════
# FOOTER / WATERMARK
# ════════════════════════════════════════════════════════════════════════════

from datetime import datetime

current_year = datetime.now().year

st.markdown(
    f"""
    <style>
    .footer {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: rgba(10, 10, 20, 0.92);
        backdrop-filter: blur(10px);
        color: #94a3b8;
        text-align: center;
        padding: 10px 0;
        font-size: 14px;
        border-top: 1px solid rgba(255,255,255,0.08);
        z-index: 999999;
    }}

    .footer strong {{
        color: #22d3ee;
    }}

    .footer a {{
        color: #6366f1;
        text-decoration: none;
        font-weight: 600;
    }}

    .footer a:hover {{
        color: #22d3ee;
    }}
    </style>

    <div class="footer">
        © {current_year} <strong>Manishankar Dey</strong> • 
        All Rights Reserved • 
        Created with ❤️ using Streamlit
    </div>
    """,
    unsafe_allow_html=True
)