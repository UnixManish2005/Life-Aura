"""
Goals – add goals, track progress, deadline reminders.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from utils.db import get_session, Goal
from utils.charts import goal_progress_chart
from utils.auth import require_login


def render():
    require_login()
    user_id = st.session_state["user_id"]

    st.markdown('<p class="page-title">🎯 Goals</p>', unsafe_allow_html=True)
    st.caption("Set meaningful goals, track progress, and hit your targets.")
    st.divider()

    session = get_session()
    goals   = session.query(Goal).filter(Goal.user_id == user_id).all()
    today   = date.today()

    # ── Add goal ──────────────────────────────────────────────────────────────
    with st.expander("➕ Add New Goal", expanded=not goals):
        with st.form("add_goal_form"):
            col1, col2 = st.columns(2)
            g_name    = col1.text_input("Goal Name *", placeholder="e.g. Read 12 books")
            g_target  = col2.number_input("Target (units)", min_value=1.0, value=100.0, step=1.0)
            g_deadline = st.date_input("Deadline", value=today + timedelta(days=30))
            submitted  = st.form_submit_button("Add Goal")
        if submitted:
            if g_name.strip():
                new_goal = Goal(
                    user_id=user_id, goal_name=g_name.strip(),
                    target=g_target, deadline=g_deadline
                )
                session.add(new_goal)
                session.commit()
                st.success(f"Goal **{g_name}** added!")
                st.rerun()
            else:
                st.error("Goal name cannot be empty.")

    st.divider()

    if not goals:
        st.info("No goals set yet. Add your first goal above!")
        session.close()
        return

    # ── Summary metrics ───────────────────────────────────────────────────────
    avg_progress = sum(
        min(g.progress / g.target * 100, 100) for g in goals
    ) / len(goals)
    completed_goals = sum(1 for g in goals if g.progress >= g.target)
    urgent_goals    = sum(
        1 for g in goals
        if g.deadline and g.deadline <= today + timedelta(days=7) and g.progress < g.target
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Goals",           len(goals))
    c2.metric("🏆 Completed",           completed_goals)
    c3.metric("⚡ Due in 7 Days",       urgent_goals)
    st.divider()

    # ── Progress chart ────────────────────────────────────────────────────────
    goal_list = [{"name": g.goal_name, "progress": g.progress, "target": g.target} for g in goals]
    st.plotly_chart(goal_progress_chart(goal_list), use_container_width=True, key="goals_progress")
    st.divider()

    # ── Individual goal cards ─────────────────────────────────────────────────
    st.subheader("📋 Goal Cards")
    cols = st.columns(min(len(goals), 2))

    for idx, g in enumerate(goals):
        pct      = min(g.progress / g.target * 100, 100) if g.target else 0
        is_done  = g.progress >= g.target
        days_left = (g.deadline - today).days if g.deadline else None

        with cols[idx % 2]:
            status_color = "#10b981" if is_done else "#f59e0b" if days_left and days_left <= 7 else "#6366f1"
            st.markdown(
                f'<div class="dash-card">'
                f'<strong style="font-size:1.05rem">{g.goal_name}</strong><br>'
                f'<span style="color:{status_color}">{"✅ Completed!" if is_done else f"{pct:.0f}% complete"}</span>'
                f'{"<br>⚠️ Due soon!" if days_left and days_left <= 7 and not is_done else ""}'
                f'</div>',
                unsafe_allow_html=True
            )
            st.progress(pct / 100)

            # Update progress
            with st.form(f"update_goal_{g.id}"):
                new_prog = st.number_input(
                    f"Update Progress (max {g.target:.0f})",
                    min_value=0.0, max_value=float(g.target),
                    value=float(g.progress), step=1.0,
                    key=f"prog_{g.id}"
                )
                col_upd, col_del = st.columns(2)
                if col_upd.form_submit_button("💾 Update"):
                    g.progress = new_prog
                    session.commit()
                    st.rerun()
                if col_del.form_submit_button("🗑️ Delete"):
                    session.delete(g)
                    session.commit()
                    st.rerun()

            if days_left is not None:
                st.caption(f"📅 Deadline: {g.deadline} ({days_left} days left)")

    # ── Table ─────────────────────────────────────────────────────────────────
    st.divider()
    df = pd.DataFrame([{
        "Goal":         g.goal_name,
        "Target":       g.target,
        "Progress":     g.progress,
        "% Complete":   f"{min(g.progress/g.target*100,100):.0f}%" if g.target else "0%",
        "Deadline":     g.deadline,
        "Status":       "✅ Done" if g.progress >= g.target else "🔄 In Progress",
    } for g in goals])
    st.dataframe(df, use_container_width=True, hide_index=True)
    session.close()
