"""
Authentication helpers: signup, login, logout, password hashing.
"""

import bcrypt
import streamlit as st
from utils.db import get_session, User, init_db


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def signup_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    init_db()
    session = get_session()
    try:
        existing = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return False, "Username or email already exists."
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password)
        )
        session.add(user)
        session.commit()
        return True, "Account created successfully!"
    except Exception as e:
        session.rollback()
        return False, f"Error: {e}"
    finally:
        session.close()


def login_user(username: str, password: str) -> tuple[bool, str, object]:
    """Verify credentials. Returns (success, message, user_obj)."""
    session = get_session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return False, "User not found.", None
        if not verify_password(password, user.password_hash):
            return False, "Incorrect password.", None
        # Detach from session so we can use outside
        session.expunge(user)
        return True, "Login successful!", user
    except Exception as e:
        return False, f"Error: {e}", None
    finally:
        session.close()


def logout():
    for key in ["logged_in", "user_id", "username"]:
        st.session_state.pop(key, None)
    st.rerun()


def require_login():
    """Redirect to login if not authenticated."""
    if not st.session_state.get("logged_in"):
        st.warning("Please login to access this page.")
        st.stop()
