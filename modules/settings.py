"""
Settings – profile, budget, theme preference, API key config.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils.db import get_session, User, get_user_budget, set_user_budget
from utils.auth import require_login, hash_password, verify_password


def render():
    require_login()
    user_id  = st.session_state["user_id"]
    username = st.session_state["username"]

    st.markdown('<p class="page-title">⚙️ Settings</p>', unsafe_allow_html=True)
    st.divider()

    session = get_session()
    user    = session.query(User).filter(User.id == user_id).first()

    tab_profile, tab_budget, tab_api = st.tabs(["👤 Profile", "💼 Budget", "🔑 API Config"])

    # ── Profile ───────────────────────────────────────────────────────────────
    with tab_profile:
        st.subheader("Profile Information")
        st.markdown(
            f'<div class="dash-card">'
            f'<strong>Username:</strong> {user.username}<br>'
            f'<strong>Email:</strong> {user.email}<br>'
            f'<strong>Member since:</strong> {user.created_at.strftime("%d %b %Y")}'
            f'</div>',
            unsafe_allow_html=True
        )

        st.subheader("Change Password")
        with st.form("change_pw"):
            old_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password",     type="password")
            cfm_pw = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Update Password"):
                if not verify_password(old_pw, user.password_hash):
                    st.error("Current password is incorrect.")
                elif new_pw != cfm_pw:
                    st.error("Passwords do not match.")
                elif len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    user.password_hash = hash_password(new_pw)
                    session.commit()
                    st.success("Password updated successfully!")

    # ── Budget ────────────────────────────────────────────────────────────────
    with tab_budget:
        st.subheader("Monthly Budget")
        # Always read from DB as source of truth
        db_budget = get_user_budget(user_id)
        if "monthly_budget" not in st.session_state:
            st.session_state.monthly_budget = db_budget

        new_budget = st.number_input(
            "Set Monthly Budget (₹)", min_value=0.0, step=500.0,
            value=float(db_budget)
        )
        if st.button("💾 Save Budget Setting"):
            set_user_budget(user_id, new_budget)
            st.session_state.monthly_budget = new_budget
            st.success(f"Budget saved: ₹{new_budget:,.0f} (persisted to database)")

        st.divider()
        st.subheader("Notification Preferences")
        st.checkbox("Budget exceeded alert", value=True)
        st.checkbox("Daily task reminder", value=True)
        st.checkbox("Habit check-in reminder", value=False)
        st.info("Notification settings are saved per session.")

    # ── API Config ───────────────────────────────────────────────────────────
    with tab_api:
        st.subheader("OpenRouter API Configuration")
        st.markdown(
            "AI features require a free OpenRouter API key. "
            "[Get your key →](https://openrouter.ai/keys)"
        )

        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        current_key = ""
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("OPENROUTER_API_KEY"):
                        current_key = line.split("=", 1)[-1].strip()

        key_display = "✅ Key configured" if (current_key and current_key != "your_openrouter_api_key_here") else "❌ Not configured"
        st.info(f"Status: {key_display}")

        new_key = st.text_input("Enter API Key", type="password", placeholder="sk-or-...")
        if st.button("Save API Key"):
            if new_key.strip():
                try:
                    with open(env_path, "w") as f:
                        f.write(f"OPENROUTER_API_KEY={new_key.strip()}\n")
                    st.success("API key saved! Restart the app for changes to take effect.")
                except Exception as e:
                    st.error(f"Could not save: {e}")
            else:
                st.error("Please enter a valid API key.")

        st.divider()
        st.subheader("Supported Free Models")
        models = {
            "mistralai/mistral-7b-instruct": "Fast, great for analysis",
            "deepseek/deepseek-chat":         "Excellent reasoning",
            "meta-llama/llama-3-8b-instruct": "Open source, reliable",
        }
        for model, desc in models.items():
            st.markdown(f"- **{model}** – {desc}")

    session.close()
