"""
AI integration using OpenRouter API.
Provides expense analysis, productivity insights, and chat assistant.

Key fix: API key is resolved at call-time (not import-time) so it works
correctly on both local (.env) and Streamlit Cloud (st.secrets).
"""

import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/auto" 


def _get_api_key() -> str:
    """
    Resolve the API key at call-time so it always picks up the latest value.
    Priority:
      1. Streamlit Cloud secrets  (st.secrets)
      2. Environment variable / .env file  (os.getenv)
    """
    # 1 — Streamlit Cloud secrets
    try:
        key = st.secrets.get("OPENROUTER_API_KEY", "")
        if key:
            return key
    except Exception:
        pass  # st.secrets not available (e.g. unit tests)

    # 2 — .env / environment variable
    return os.getenv("OPENROUTER_API_KEY", "")


def _build_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://ai-life-dashboard.app",
        "X-Title":       "AI Life Dashboard",
    }


def _call_api(messages: list, max_tokens: int = 800) -> str:
    """Low-level API call. Returns assistant text or an error string."""
    api_key = _get_api_key()

    if not api_key or api_key.strip() in ("", "your_openrouter_api_key_here", "sk-or-your-key-here"):
        return (
            "⚠️ OpenRouter API key not configured.\n\n"
            "**To fix this:**\n"
            "- **Streamlit Cloud**: go to App Settings → Secrets and add:\n"
            "  `OPENROUTER_API_KEY = \"sk-or-...\"`\n"
            "- **Local**: add `OPENROUTER_API_KEY=sk-or-...` to your `.env` file\n\n"
            "Get a free key at https://openrouter.ai/keys"
        )

    payload = {
        "model":       MODEL,
        "messages":    messages,
        "max_tokens":  max_tokens,
        "temperature": 0.7,
    }
    try:
        resp = requests.post(
            API_URL,
            headers=_build_headers(api_key),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return "⚠️ Request timed out. Please try again in a moment."
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        body   = e.response.text[:300]
        if status == 401:
            return (
                "⚠️ **401 Unauthorized** – your API key was rejected.\n\n"
                "Please check:\n"
                "- The key is correct (no extra spaces)\n"
                "- It starts with `sk-or-`\n"
                "- It is added to Streamlit Cloud **Secrets**, not just the .env file"
            )
        return f"⚠️ API error {status}: {body}"
    except Exception as e:
        return f"⚠️ Unexpected error: {e}"


# ── Public API ────────────────────────────────────────────────────────────────

def get_ai_response(prompt: str, system: str = "") -> str:
    """Single-turn AI response."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return _call_api(messages)


def chat_with_memory(user_message: str) -> str:
    """Multi-turn chat using session_state conversation history."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    system = (
        "You are a helpful personal productivity and financial coach. "
        "You help users improve their habits, manage expenses, and boost productivity. "
        "Be concise, friendly, and actionable."
    )
    messages = [{"role": "system", "content": system}]
    messages += st.session_state.chat_history
    messages.append({"role": "user", "content": user_message})

    reply = _call_api(messages, max_tokens=600)

    st.session_state.chat_history.append({"role": "user",      "content": user_message})
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    return reply


def generate_expense_analysis(expense_data: dict) -> str:
    """Analyse spending from a dict summary."""
    total   = expense_data.get("total", 0)
    cats    = expense_data.get("categories", {})
    budget  = expense_data.get("budget", 0)
    cat_str = ", ".join(f"{k}: ₹{v:.0f}" for k, v in cats.items()) if cats else "No data"

    prompt = (
        f"Analyse this user's monthly expenses and give 3-4 concrete tips:\n"
        f"- Total spent: ₹{total:.0f}\n"
        f"- Budget: ₹{budget:.0f}\n"
        f"- By category: {cat_str}\n"
        f"Keep it brief and actionable."
    )
    return get_ai_response(prompt)


def generate_productivity_analysis(task_data: dict) -> str:
    """Analyse task completion and give productivity tips."""
    completed = task_data.get("completed", 0)
    total     = task_data.get("total", 0)
    rate      = (completed / total * 100) if total else 0
    overdue   = task_data.get("overdue", 0)

    prompt = (
        f"Analyse this user's productivity and give 3-4 actionable suggestions:\n"
        f"- Tasks completed: {completed}/{total} ({rate:.0f}%)\n"
        f"- Overdue tasks: {overdue}\n"
        f"Be encouraging and specific."
    )
    return get_ai_response(prompt)


def generate_monthly_summary(user_stats: dict) -> str:
    """Generate a full monthly summary report text."""
    prompt = (
        "Generate a concise monthly life summary report (200 words) for this user:\n"
        f"{user_stats}\n"
        "Include: what went well, areas to improve, and one motivational closing line."
    )
    return get_ai_response(prompt, max_tokens=400)
