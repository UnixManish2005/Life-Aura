"""
Dashboard page – overview metrics, life score, today's tasks & expenses.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import date, datetime
import random

from utils.db import get_session, Task, Expense, Habit, Goal
from utils.charts import life_score_gauge, expense_pie_chart, productivity_bar
from utils.auth import require_login

QUOTES = [
    "The secret of getting ahead is getting started. — Mark Twain",
    "It always seems impossible until it's done. — Nelson Mandela",
    "Focus on being productive instead of busy. — Tim Ferriss",
    "Don't watch the clock; do what it does. Keep going. — Sam Levenson",
    "Success is the sum of small efforts, repeated day in and day out.",
    "Your future is created by what you do today, not tomorrow.",
    "Small daily improvements over time lead to stunning results.",
]


def compute_life_score(user_id: int, session) -> float:
    today = date.today()

    # Task score (40%)
    tasks    = session.query(Task).filter(Task.user_id == user_id).all()
    t_total  = len(tasks)
    t_done   = sum(1 for t in tasks if t.status == "Completed")
    t_score  = (t_done / t_total * 100) if t_total else 50

    # Habit score (30%)
    habits   = session.query(Habit).filter(Habit.user_id == user_id).all()
    h_score  = min(sum(h.streak for h in habits) / max(len(habits), 1) * 10, 100) if habits else 50

    # Expense score (20%) – did user stay under a theoretical budget?
    expenses = session.query(Expense).filter(Expense.user_id == user_id).all()
    e_score  = max(100 - len(expenses) * 2, 20) if expenses else 70  # simplified

    # Goal score (10%)
    goals   = session.query(Goal).filter(Goal.user_id == user_id).all()
    g_score = (
        sum(min(g.progress / g.target * 100, 100) for g in goals) / len(goals)
        if goals else 50
    )

    score = (t_score * 0.4) + (h_score * 0.3) + (e_score * 0.2) + (g_score * 0.1)
    return round(min(score, 100), 1)


def render():
    require_login()
    user_id  = st.session_state["user_id"]
    username = st.session_state["username"]
    session  = get_session()

    today = date.today()

    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown(f'<p class="page-title">👋 Welcome back, {username}!</p>', unsafe_allow_html=True)
    st.caption(f"📅 {datetime.now().strftime('%A, %d %B %Y')}")

    # Motivational quote
    quote = random.choice(QUOTES)
    st.info(f"💡 *{quote}*")
    st.divider()

    # ── Fetch data ───────────────────────────────────────────────────────────
    tasks    = session.query(Task).filter(Task.user_id == user_id).all()
    today_tasks  = [t for t in tasks if t.due_date == today]
    done_today   = [t for t in today_tasks if t.status == "Completed"]
    pending_all  = [t for t in tasks if t.status == "Pending"]

    expenses = session.query(Expense).filter(Expense.user_id == user_id).all()
    exp_df   = pd.DataFrame([{
        "amount": e.amount, "category": e.category, "date": e.date
    } for e in expenses])

    today_exp   = sum(e.amount for e in expenses if e.date == today)
    month_exp   = sum(
        e.amount for e in expenses
        if e.date.month == today.month and e.date.year == today.year
    )

    habits    = session.query(Habit).filter(Habit.user_id == user_id).all()
    best_streak = max((h.streak for h in habits), default=0)

    goals     = session.query(Goal).filter(Goal.user_id == user_id).all()
    g_pct     = (
        sum(min(g.progress / g.target * 100, 100) for g in goals) / len(goals)
        if goals else 0
    )

    life_score = compute_life_score(user_id, session)
    session.close()

    # ── KPI row ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📋 Tasks Today",    f"{len(done_today)}/{len(today_tasks)}")
    c2.metric("💰 Today's Spend",  f"₹{today_exp:,.0f}")
    c3.metric("📅 Monthly Spend",  f"₹{month_exp:,.0f}")
    c4.metric("🔥 Best Streak",    f"{best_streak} days")
    c5.metric("🎯 Goal Progress",  f"{g_pct:.0f}%")

    st.divider()

    # ── Charts row ───────────────────────────────────────────────────────────
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.subheader("💰 Expenses by Category")
        st.plotly_chart(expense_pie_chart(exp_df), use_container_width=True, key="dash_exp_pie")

    with col_right:
        st.subheader("🏆 Life Score")
        st.plotly_chart(life_score_gauge(life_score), use_container_width=True, key="dash_life_gauge")
        st.caption("Based on tasks · habits · expense control · goals")

    st.divider()

    # ── Productivity snapshot ────────────────────────────────────────────────
    col_prod, col_tasks = st.columns(2)

    with col_prod:
        st.subheader("📊 Task Status")
        completed_n = sum(1 for t in tasks if t.status == "Completed")
        pending_n   = len(tasks) - completed_n
        st.plotly_chart(productivity_bar(completed_n, pending_n), use_container_width=True, key="dash_prod_bar")

    with col_tasks:
        st.subheader("📝 Today's Pending Tasks")
        today_pending = [t for t in today_tasks if t.status == "Pending"]
        if today_pending:
            for t in today_pending[:6]:
                pri_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(t.priority, "⚪")
                st.markdown(f"{pri_color} **{t.task_name}** — *{t.category}*")
        else:
            st.success("✅ All tasks for today are done!")

    # ── Habit streaks ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("🔥 Active Habit Streaks")
    if habits:
        cols = st.columns(min(len(habits), 4))
        for i, h in enumerate(habits[:4]):
            cols[i].metric(h.habit_name, f"{h.streak} 🔥 days")
    else:
        st.info("No habits tracked yet. Head to the Habit Tracker to add some!")
