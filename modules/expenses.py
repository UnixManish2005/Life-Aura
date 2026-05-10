"""
Expense Tracker – add/delete expenses, budgets, category analytics, alerts.
Budget is now persisted in the database (survives restarts).
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import date, datetime

from utils.db import get_session, Expense, get_user_budget, set_user_budget
from utils.charts import expense_pie_chart, monthly_expense_line, monthly_bar_chart
from utils.auth import require_login

CATEGORIES = ["Food", "Travel", "Shopping", "Education", "Entertainment", "Health", "Other"]


def render():
    require_login()
    user_id = st.session_state["user_id"]

    st.markdown('<p class="page-title">💰 Expense Tracker</p>', unsafe_allow_html=True)
    st.caption("Track every rupee – manage budgets and spot spending patterns.")
    st.divider()

    # ── Load budget from DB (persisted across restarts) ───────────────────────
    # Only read from DB once per session; after that use session_state as cache
    if "monthly_budget" not in st.session_state:
        st.session_state.monthly_budget = get_user_budget(user_id)

    session  = get_session()
    expenses = session.query(Expense).filter(Expense.user_id == user_id).all()
    today    = date.today()

    exp_df = pd.DataFrame([{
        "id":          e.id,
        "amount":      e.amount,
        "category":    e.category,
        "description": e.description or "",
        "date":        e.date,
    } for e in expenses])

    # ── Metrics ───────────────────────────────────────────────────────────────
    month_total = sum(
        e.amount for e in expenses
        if e.date.month == today.month and e.date.year == today.year
    )
    today_total = sum(e.amount for e in expenses if e.date == today)
    budget      = st.session_state.monthly_budget
    remaining   = budget - month_total if budget else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💸 Today",      f"₹{today_total:,.0f}")
    c2.metric("📅 This Month", f"₹{month_total:,.0f}")
    c3.metric("💼 Budget",     f"₹{budget:,.0f}" if budget else "Not set")
    c4.metric(
        "✅ Remaining",
        f"₹{remaining:,.0f}" if remaining is not None else "—",
        delta=f"₹{remaining:,.0f}" if remaining is not None else None,
        delta_color="inverse",
    )

    # ── Budget alerts ─────────────────────────────────────────────────────────
    if budget and month_total > budget:
        st.markdown(
            f'<div class="alert-danger">⚠️ Budget exceeded by ₹{month_total - budget:,.0f}! '
            f'Consider cutting back on non-essential spending.</div>',
            unsafe_allow_html=True,
        )
    elif budget and month_total > budget * 0.8:
        st.markdown(
            f'<div class="alert-warning">📣 You\'ve used {month_total/budget*100:.0f}% of '
            f'your monthly budget.</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Set budget & add expense ──────────────────────────────────────────────
    col_budget, col_add = st.columns(2)

    with col_budget:
        with st.expander("💼 Set Monthly Budget", expanded=False):
            new_budget = st.number_input(
                "Monthly Budget (₹)",
                min_value=0.0,
                step=500.0,
                value=float(st.session_state.monthly_budget),
                key="budget_input",
            )
            if st.button("💾 Save Budget"):
                # Persist to DB so it survives app restarts
                set_user_budget(user_id, new_budget)
                st.session_state.monthly_budget = new_budget
                st.success(f"Budget saved: ₹{new_budget:,.0f}")
                st.rerun()

    with col_add:
        with st.expander("➕ Add Expense", expanded=False):
            with st.form("add_expense_form"):
                r1c1, r1c2 = st.columns(2)
                amount      = r1c1.number_input("Amount (₹) *", min_value=0.01, step=10.0)
                category    = r1c2.selectbox("Category", CATEGORIES)
                description = st.text_input("Description", placeholder="Optional note")
                exp_date    = st.date_input("Date", value=today)
                submitted   = st.form_submit_button("Add Expense")

            if submitted:
                new_exp = Expense(
                    user_id=user_id, amount=amount,
                    category=category, description=description, date=exp_date,
                )
                session.add(new_exp)
                session.commit()
                st.success(f"₹{amount:.0f} ({category}) added!")
                st.rerun()

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    tab_pie, tab_trend, tab_monthly = st.tabs(
        ["🥧 By Category", "📈 Daily Trend", "📊 Monthly"]
    )
    with tab_pie:
        st.plotly_chart(expense_pie_chart(exp_df), use_container_width=True, key="exp_pie")
    with tab_trend:
        month_df = (
            exp_df[pd.to_datetime(exp_df["date"]).dt.month == today.month]
            if not exp_df.empty else exp_df
        )
        st.plotly_chart(monthly_expense_line(month_df), use_container_width=True, key="exp_line")
    with tab_monthly:
        st.plotly_chart(monthly_bar_chart(exp_df), use_container_width=True, key="exp_bar")

    st.divider()

    # ── Expense list ──────────────────────────────────────────────────────────
    st.subheader("📋 Expense Records")
    if not exp_df.empty:
        fc1, fc2 = st.columns(2)
        filter_cat   = fc1.selectbox("Filter Category", ["All"] + CATEGORIES)
        month_options = ["All"] + sorted(
            exp_df["date"].apply(lambda d: d.strftime("%b %Y")).unique().tolist(),
            reverse=True,
        )
        filter_month = fc2.selectbox("Filter Month", month_options)

        disp = exp_df.copy()
        if filter_cat != "All":
            disp = disp[disp["category"] == filter_cat]
        if filter_month != "All":
            disp = disp[pd.to_datetime(disp["date"]).dt.strftime("%b %Y") == filter_month]

        disp_show = disp[["id","date","category","description","amount"]].sort_values(
            "date", ascending=False
        )
        st.dataframe(disp_show, use_container_width=True, hide_index=True)

        col_del1, col_del2 = st.columns([1, 3])
        del_id = col_del1.number_input("Delete Expense by ID", min_value=0, step=1, value=0)
        if col_del2.button("🗑️ Delete Expense") and del_id:
            exp_to_del = session.query(Expense).filter(
                Expense.id == int(del_id), Expense.user_id == user_id
            ).first()
            if exp_to_del:
                session.delete(exp_to_del)
                session.commit()
                st.success("Expense deleted.")
                st.rerun()
            else:
                st.error("Expense not found or doesn't belong to you.")

        csv = disp_show.to_csv(index=False)
        st.download_button("⬇️ Export CSV", csv, "expenses.csv", "text/csv")
    else:
        st.info("No expenses recorded yet. Add your first expense above!")

    session.close()
