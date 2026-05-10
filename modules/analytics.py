"""
Analytics – interactive charts across expenses, tasks, habits, and goals.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime

from utils.db import get_session, Task, Expense, Habit, HabitCheckIn, Goal
from utils.charts import (
    expense_pie_chart, monthly_expense_line, monthly_bar_chart,
    productivity_bar, goal_progress_chart, life_score_gauge
)
from utils.auth import require_login

PALETTE = ["#6366f1","#22d3ee","#f59e0b","#10b981","#f43f5e","#a78bfa","#34d399"]
BG      = "rgba(0,0,0,0)"


def render():
    require_login()
    user_id = st.session_state["user_id"]

    st.markdown('<p class="page-title">📊 Analytics</p>', unsafe_allow_html=True)
    st.caption("Deep-dive into your productivity, spending, and habit patterns.")
    st.divider()

    session  = get_session()
    today    = date.today()

    # ── Fetch ─────────────────────────────────────────────────────────────────
    tasks    = session.query(Task).filter(Task.user_id == user_id).all()
    expenses = session.query(Expense).filter(Expense.user_id == user_id).all()
    habits   = session.query(Habit).filter(Habit.user_id == user_id).all()
    goals    = session.query(Goal).filter(Goal.user_id == user_id).all()

    exp_df = pd.DataFrame([{
        "amount": e.amount, "category": e.category,
        "date": pd.to_datetime(e.date), "description": e.description
    } for e in expenses])

    task_df = pd.DataFrame([{
        "status": t.status, "priority": t.priority,
        "category": t.category,
        "created_at": pd.to_datetime(t.created_at)
    } for t in tasks])

    # ── Tab layout ────────────────────────────────────────────────────────────
    tab_exp, tab_tasks, tab_habits, tab_goals = st.tabs([
        "💰 Expenses", "📋 Tasks", "🔥 Habits", "🎯 Goals"
    ])

    # ===================== EXPENSES =====================
    with tab_exp:
        st.subheader("Expense Analytics")
        if exp_df.empty:
            st.info("No expense data yet.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Category Distribution**")
                st.plotly_chart(expense_pie_chart(exp_df), use_container_width=True, key="an_exp_pie")
            with col2:
                st.markdown("**Daily Spending Trend**")
                st.plotly_chart(monthly_expense_line(exp_df), use_container_width=True, key="an_exp_line")

            st.markdown("**Month-over-Month Spending**")
            st.plotly_chart(monthly_bar_chart(exp_df), use_container_width=True, key="an_exp_monthly")

            # Category trend
            st.markdown("**Category Trends Over Time**")
            exp_df["month"] = exp_df["date"].dt.strftime("%b %Y")
            cat_monthly = exp_df.groupby(["month","category"])["amount"].sum().reset_index()
            if not cat_monthly.empty:
                fig = px.bar(
                    cat_monthly, x="month", y="amount", color="category",
                    color_discrete_sequence=PALETTE, barmode="stack"
                )
                fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG,
                                  font=dict(color="#e2e8f0"),
                                  legend=dict(bgcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig, use_container_width=True, key="an_exp_cat_trend")

            # Top 5 expenses
            st.markdown("**Top 5 Expenses**")
            top5 = exp_df.nlargest(5, "amount")[["date","category","description","amount"]]
            st.dataframe(top5, use_container_width=True, hide_index=True)

    # ===================== TASKS =====================
    with tab_tasks:
        st.subheader("Task Analytics")
        if task_df.empty:
            st.info("No task data yet.")
        else:
            completed = task_df[task_df["status"] == "Completed"].shape[0]
            pending   = task_df[task_df["status"] == "Pending"].shape[0]

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Task Status**")
                st.plotly_chart(productivity_bar(completed, pending), use_container_width=True, key="an_task_status")
            with col2:
                st.markdown("**Tasks by Priority**")
                pri_counts = task_df["priority"].value_counts().reset_index()
                pri_counts.columns = ["priority","count"]
                fig = px.pie(pri_counts, values="count", names="priority",
                             color_discrete_sequence=PALETTE, hole=0.4)
                fig.update_layout(paper_bgcolor=BG, font=dict(color="#e2e8f0"),
                                  legend=dict(bgcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig, use_container_width=True, key="an_task_priority_pie")

            st.markdown("**Tasks by Category**")
            cat_counts = task_df["category"].value_counts().reset_index()
            cat_counts.columns = ["category","count"]
            fig2 = px.bar(cat_counts, x="count", y="category", orientation="h",
                          color_discrete_sequence=[PALETTE[0]])
            fig2.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color="#e2e8f0"),
                               xaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
                               yaxis=dict(gridcolor="rgba(255,255,255,0.07)"))
            st.plotly_chart(fig2, use_container_width=True, key="an_task_cat")

    # ===================== HABITS =====================
    with tab_habits:
        st.subheader("Habit Analytics")
        if not habits:
            st.info("No habits tracked yet.")
        else:
            # Streak bar chart
            habit_names   = [h.habit_name for h in habits]
            habit_streaks = [h.streak for h in habits]
            fig = go.Figure(go.Bar(
                x=habit_names, y=habit_streaks,
                marker_color=PALETTE[:len(habits)],
                text=habit_streaks, textposition="outside"
            ))
            fig.update_layout(
                title="Current Streaks",
                paper_bgcolor=BG, plot_bgcolor=BG,
                font=dict(color="#e2e8f0"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.07)"),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True, key="an_habit_streak")

            # Consistency by habit
            st.markdown("**Check-in Consistency**")
            consistency_data = []
            for h in habits:
                total_ci = session.query(HabitCheckIn).filter(HabitCheckIn.habit_id == h.id).count()
                days = max((today - h.created_at.date()).days, 1)
                consistency_data.append({
                    "Habit": h.habit_name,
                    "Check-ins": total_ci,
                    "Days Active": days,
                    "Consistency": f"{total_ci/days*100:.0f}%"
                })
            st.dataframe(pd.DataFrame(consistency_data), use_container_width=True, hide_index=True)

    # ===================== GOALS =====================
    with tab_goals:
        st.subheader("Goal Analytics")
        if not goals:
            st.info("No goals set yet.")
        else:
            goal_list = [{"name": g.goal_name, "progress": g.progress, "target": g.target} for g in goals]
            st.plotly_chart(goal_progress_chart(goal_list), use_container_width=True, key="an_goals_progress")

            # Days remaining
            goal_timeline = []
            for g in goals:
                days_left = (g.deadline - today).days if g.deadline else None
                goal_timeline.append({
                    "Goal":       g.goal_name,
                    "Progress %": f"{min(g.progress/g.target*100,100):.0f}%" if g.target else "0%",
                    "Deadline":   str(g.deadline) if g.deadline else "No deadline",
                    "Days Left":  days_left if days_left is not None else "—",
                    "Status":     "✅" if g.progress >= g.target else
                                  "⚠️" if days_left and days_left <= 7 else "🔄"
                })
            st.dataframe(pd.DataFrame(goal_timeline), use_container_width=True, hide_index=True)

    session.close()
