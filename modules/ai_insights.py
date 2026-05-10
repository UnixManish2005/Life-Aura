"""
AI Insights – expense analysis, productivity coaching, and chat assistant.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import date

from utils.db import get_session, Task, Expense, Habit, Goal
from utils.ai_helper import (
    generate_expense_analysis, generate_productivity_analysis,
    generate_monthly_summary, chat_with_memory
)
from utils.auth import require_login


def render():
    require_login()
    user_id = st.session_state["user_id"]

    st.markdown('<p class="page-title">🤖 AI Insights</p>', unsafe_allow_html=True)
    st.caption("Powered by OpenRouter · Free AI models")
    st.divider()

    session  = get_session()
    today    = date.today()

    tasks    = session.query(Task).filter(Task.user_id == user_id).all()
    expenses = session.query(Expense).filter(Expense.user_id == user_id).all()
    habits   = session.query(Habit).filter(Habit.user_id == user_id).all()
    goals    = session.query(Goal).filter(Goal.user_id == user_id).all()
    session.close()

    # ── Build context dicts ───────────────────────────────────────────────────
    month_expenses = [
        e for e in expenses
        if e.date.month == today.month and e.date.year == today.year
    ]
    cat_totals = {}
    for e in month_expenses:
        cat_totals[e.category] = cat_totals.get(e.category, 0) + e.amount

    expense_data = {
        "total":      sum(e.amount for e in month_expenses),
        "categories": cat_totals,
        "budget":     st.session_state.get("monthly_budget", 0),
    }

    task_data = {
        "total":     len(tasks),
        "completed": sum(1 for t in tasks if t.status == "Completed"),
        "overdue":   sum(1 for t in tasks if t.status == "Pending" and t.due_date and t.due_date < today),
    }

    user_stats = {
        "tasks":          task_data,
        "expenses":       expense_data,
        "habits":         [{"name": h.habit_name, "streak": h.streak} for h in habits],
        "goals":          [{"name": g.goal_name, "progress": g.progress, "target": g.target} for g in goals],
        "month":          today.strftime("%B %Y"),
    }

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_insights, tab_chat = st.tabs(["💡 AI Insights", "💬 AI Chat Assistant"])

    # ===== INSIGHTS TAB =====
    with tab_insights:
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("💰 Spending Analysis")
            if st.button("Analyse My Expenses", key="btn_exp"):
                with st.spinner("Analysing your expenses…"):
                    result = generate_expense_analysis(expense_data)
                st.markdown(
                    f'<div class="dash-card">{result}</div>',
                    unsafe_allow_html=True
                )

            st.subheader("📋 Productivity Analysis")
            if st.button("Analyse My Productivity", key="btn_prod"):
                with st.spinner("Analysing productivity…"):
                    result = generate_productivity_analysis(task_data)
                st.markdown(
                    f'<div class="dash-card">{result}</div>',
                    unsafe_allow_html=True
                )

        with col_right:
            st.subheader("📅 Monthly Summary")
            if st.button("Generate Monthly Summary", key="btn_monthly"):
                with st.spinner("Generating your monthly summary…"):
                    result = generate_monthly_summary(user_stats)
                st.markdown(
                    f'<div class="dash-card">{result}</div>',
                    unsafe_allow_html=True
                )

            # Quick stats for context
            st.subheader("📊 Your Stats")
            st.markdown(
                f'<div class="dash-card">'
                f'<p>📋 <strong>Tasks:</strong> {task_data["completed"]}/{task_data["total"]} completed</p>'
                f'<p>💰 <strong>Month Spend:</strong> ₹{expense_data["total"]:,.0f}</p>'
                f'<p>🔥 <strong>Habits:</strong> {len(habits)} tracked</p>'
                f'<p>🎯 <strong>Goals:</strong> {len(goals)} active</p>'
                f'</div>',
                unsafe_allow_html=True
            )

        # Suggested prompts
        st.divider()
        st.subheader("💡 Suggested Questions")
        suggestions = [
            "How can I improve my productivity?",
            "Where am I spending most money?",
            "Give me my monthly summary.",
            "How can I build better habits?",
            "What should I focus on this week?",
        ]
        cols = st.columns(len(suggestions))
        for i, suggestion in enumerate(suggestions):
            if cols[i].button(suggestion, key=f"sug_{i}"):
                st.session_state.setdefault("chat_history", [])
                with st.spinner("Thinking…"):
                    reply = chat_with_memory(suggestion)
                st.success(f"**You:** {suggestion}")
                st.info(f"**AI:** {reply}")

    # ===== CHAT TAB =====
    with tab_chat:
        st.subheader("💬 Chat with AI Assistant")
        st.caption("Ask anything about your productivity, habits, or finances.")

        # Display conversation history
        history = st.session_state.get("chat_history", [])
        if history:
            st.markdown('<div style="max-height:400px;overflow-y:auto">', unsafe_allow_html=True)
            for msg in history:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="chat-user">🧑 {msg["content"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="chat-ai">🤖 {msg["content"]}</div>',
                        unsafe_allow_html=True
                    )
            st.markdown('</div>', unsafe_allow_html=True)
            st.divider()

        # Input
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Your message",
                placeholder="e.g. How can I reduce my food expenses?"
            )
            submitted  = st.form_submit_button("Send 💬")

        if submitted and user_input.strip():
            with st.spinner("AI is thinking…"):
                reply = chat_with_memory(user_input.strip())
            st.rerun()

        # Clear chat
        if history:
            if st.button("🗑️ Clear Chat History"):
                st.session_state.chat_history = []
                st.rerun()
