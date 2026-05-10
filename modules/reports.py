"""
Reports – generate and download PDF / CSV reports.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import date

from utils.db import get_session, Task, Expense, Habit, HabitCheckIn, Goal
from utils.report_generator import generate_report
from utils.ai_helper import generate_monthly_summary
from utils.auth import require_login


def render():
    require_login()
    user_id  = st.session_state["user_id"]
    username = st.session_state["username"]

    st.markdown('<p class="page-title">📄 Reports</p>', unsafe_allow_html=True)
    st.caption("Download PDF and CSV reports for your data.")
    st.divider()

    session = get_session()
    today   = date.today()

    tasks    = session.query(Task).filter(Task.user_id == user_id).all()
    expenses = session.query(Expense).filter(Expense.user_id == user_id).all()
    habits   = session.query(Habit).filter(Habit.user_id == user_id).all()
    goals    = session.query(Goal).filter(Goal.user_id == user_id).all()

    month_expenses = [
        e for e in expenses
        if e.date.month == today.month and e.date.year == today.year
    ]

    # ── Build report data dicts ────────────────────────────────────────────────
    task_stats = {
        "total":     len(tasks),
        "completed": sum(1 for t in tasks if t.status == "Completed"),
        "overdue":   sum(1 for t in tasks if t.status == "Pending" and t.due_date and t.due_date < today),
    }

    cat_totals: dict = {}
    for e in month_expenses:
        cat_totals[e.category] = cat_totals.get(e.category, 0) + e.amount

    expense_stats = {
        "total":      sum(e.amount for e in month_expenses),
        "budget":     st.session_state.get("monthly_budget", 0),
        "categories": cat_totals,
    }

    habit_stats = {
        "habits":     [{"name": h.habit_name, "streak": h.streak} for h in habits],
        "avg_streak": sum(h.streak for h in habits) / len(habits) if habits else 0,
    }

    goal_stats = {
        "goals": [{"name": g.goal_name, "progress": g.progress, "target": g.target} for g in goals]
    }
    session.close()

    # ── Preview ───────────────────────────────────────────────────────────────
    st.subheader(f"📅 {today.strftime('%B %Y')} Report Preview")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📋 Task Summary**")
        c = task_stats
        st.markdown(
            f'<div class="dash-card">'
            f'Total: {c["total"]} | ✅ Done: {c["completed"]} | ⚠️ Overdue: {c["overdue"]}'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown("**🔥 Habit Summary**")
        st.markdown(
            f'<div class="dash-card">'
            f'Habits: {len(habits)} | Avg Streak: {habit_stats["avg_streak"]:.1f} days'
            f'</div>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("**💰 Expense Summary**")
        e = expense_stats
        st.markdown(
            f'<div class="dash-card">'
            f'Spent: ₹{e["total"]:,.0f} | Budget: ₹{e["budget"]:,.0f}'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown("**🎯 Goal Summary**")
        completed_goals = sum(1 for g in goals if g.progress >= g.target)
        st.markdown(
            f'<div class="dash-card">'
            f'Goals: {len(goals)} | ✅ Completed: {completed_goals}'
            f'</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # ── PDF Report ────────────────────────────────────────────────────────────
    st.subheader("📥 Download Reports")

    col_pdf, col_csv = st.columns(2)

    with col_pdf:
        st.markdown("**📄 PDF Monthly Report**")
        ai_summary = ""
        include_ai = st.checkbox("Include AI insights in PDF (requires API key)")

        if st.button("Generate PDF Report", type="primary"):
            if include_ai:
                with st.spinner("Generating AI insights…"):
                    user_stats = {
                        "tasks": task_stats, "expenses": expense_stats,
                        "habits": habit_stats, "goals": goal_stats,
                        "month": today.strftime("%B %Y"),
                    }
                    ai_summary = generate_monthly_summary(user_stats)

            with st.spinner("Building PDF…"):
                pdf_bytes = generate_report(
                    username=username,
                    task_stats=task_stats,
                    expense_stats=expense_stats,
                    habit_stats=habit_stats,
                    goal_stats=goal_stats,
                    ai_summary=ai_summary,
                )

            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"life_dashboard_{today.strftime('%Y_%m')}.pdf",
                mime="application/pdf",
            )

    with col_csv:
        st.markdown("**📊 CSV Data Export**")
        export_type = st.selectbox("Select data", ["Expenses", "Tasks", "Habits", "Goals"])

        if st.button("Generate CSV"):
            if export_type == "Expenses":
                df = pd.DataFrame([{
                    "Date": e.date, "Category": e.category,
                    "Description": e.description, "Amount": e.amount
                } for e in expenses])
            elif export_type == "Tasks":
                df = pd.DataFrame([{
                    "Task": t.task_name, "Category": t.category,
                    "Priority": t.priority, "Due": t.due_date, "Status": t.status
                } for t in tasks])
            elif export_type == "Habits":
                df = pd.DataFrame([{
                    "Habit": h.habit_name, "Streak": h.streak,
                    "Last Check-in": h.completion_date
                } for h in habits])
            else:
                df = pd.DataFrame([{
                    "Goal": g.goal_name, "Target": g.target,
                    "Progress": g.progress, "Deadline": g.deadline
                } for g in goals])

            csv = df.to_csv(index=False)
            st.download_button(
                label=f"⬇️ Download {export_type} CSV",
                data=csv,
                file_name=f"{export_type.lower()}_{today}.csv",
                mime="text/csv"
            )
