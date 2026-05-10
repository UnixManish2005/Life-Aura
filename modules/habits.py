"""
Habit Tracker – add habits, daily check-ins, streaks, and heatmaps.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from utils.db import get_session, Habit, HabitCheckIn
from utils.charts import habit_heatmap
from utils.auth import require_login


def _update_streak(habit: Habit, session) -> None:
    """Recalculate streak based on consecutive daily check-ins."""
    checkins = (
        session.query(HabitCheckIn)
        .filter(HabitCheckIn.habit_id == habit.id)
        .order_by(HabitCheckIn.date.desc())
        .all()
    )
    if not checkins:
        habit.streak = 0
        return

    dates = sorted({c.date for c in checkins}, reverse=True)
    streak = 0
    expected = date.today()
    for d in dates:
        if d == expected:
            streak += 1
            expected -= timedelta(days=1)
        elif d == expected + timedelta(days=1):
            # yesterday counts too on same day
            streak += 1
            expected -= timedelta(days=1)
        else:
            break
    habit.streak = streak
    habit.completion_date = dates[0] if dates else None


def render():
    require_login()
    user_id = st.session_state["user_id"]

    st.markdown('<p class="page-title">🔥 Habit Tracker</p>', unsafe_allow_html=True)
    st.caption("Build streaks, stay consistent, and visualize your progress.")
    st.divider()

    session = get_session()
    habits  = session.query(Habit).filter(Habit.user_id == user_id).all()

    today   = date.today()

    # ── Add habit ──────────────────────────────────────────────────────────────
    with st.expander("➕ Add New Habit", expanded=not habits):
        with st.form("add_habit_form"):
            h_name    = st.text_input("Habit Name *", placeholder="e.g. Morning Run")
            submitted = st.form_submit_button("Add Habit")
        if submitted:
            if h_name.strip():
                new_h = Habit(user_id=user_id, habit_name=h_name.strip())
                session.add(new_h)
                session.commit()
                st.success(f"Habit **{h_name}** added!")
                st.rerun()
            else:
                st.error("Habit name cannot be empty.")

    st.divider()

    if not habits:
        st.info("No habits tracked yet. Add your first habit above!")
        session.close()
        return

    # ── Summary metrics ───────────────────────────────────────────────────────
    avg_streak  = sum(h.streak for h in habits) / len(habits)
    checked_today = 0

    for h in habits:
        checkin_today = (
            session.query(HabitCheckIn)
            .filter(HabitCheckIn.habit_id == h.id, HabitCheckIn.date == today)
            .first()
        )
        if checkin_today:
            checked_today += 1

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Habits",       len(habits))
    c2.metric("⚡ Avg Streak",      f"{avg_streak:.1f} days")
    c3.metric("✅ Checked Today",    f"{checked_today}/{len(habits)}")
    st.divider()

    # ── Daily check-in ────────────────────────────────────────────────────────
    st.subheader("📅 Today's Check-in")
    cols = st.columns(min(len(habits), 3))

    for idx, h in enumerate(habits):
        col = cols[idx % len(cols)]
        checkin_today = (
            session.query(HabitCheckIn)
            .filter(HabitCheckIn.habit_id == h.id, HabitCheckIn.date == today)
            .first()
        )
        with col:
            st.markdown(
                f'<div class="dash-card" style="text-align:center">'
                f'<div style="font-size:1.3rem;margin-bottom:4px">{"✅" if checkin_today else "⏺️"}</div>'
                f'<strong>{h.habit_name}</strong><br>'
                f'<span style="color:#f59e0b">🔥 {h.streak} day streak</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            if not checkin_today:
                if st.button(f"Check In", key=f"ci_{h.id}"):
                    ci = HabitCheckIn(habit_id=h.id, date=today)
                    session.add(ci)
                    _update_streak(h, session)
                    session.commit()
                    st.rerun()
            else:
                if st.button(f"Undo Check-in", key=f"undo_{h.id}"):
                    session.delete(checkin_today)
                    _update_streak(h, session)
                    session.commit()
                    st.rerun()

            if st.button("🗑️ Delete", key=f"del_{h.id}"):
                session.delete(h)
                session.commit()
                st.rerun()

    st.divider()

    # ── Heatmaps ──────────────────────────────────────────────────────────────
    st.subheader("📊 Check-in Heatmaps (Last 12 weeks)")
    for h in habits:
        checkins_df = pd.DataFrame([
            {"date": c.date}
            for c in session.query(HabitCheckIn).filter(HabitCheckIn.habit_id == h.id).all()
        ])
        fig = habit_heatmap(checkins_df, h.habit_name)
        st.plotly_chart(fig, use_container_width=True, key=f"habit_heatmap_{h.id}")

    # ── Analytics table ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Habit Analytics")
    habit_data = []
    for h in habits:
        total_checkins = session.query(HabitCheckIn).filter(HabitCheckIn.habit_id == h.id).count()
        days_since     = (today - h.created_at.date()).days + 1
        consistency    = round(total_checkins / days_since * 100, 1) if days_since else 0
        habit_data.append({
            "Habit":        h.habit_name,
            "Streak 🔥":    h.streak,
            "Total Check-ins": total_checkins,
            "Days Tracked":   days_since,
            "Consistency %":  f"{consistency}%",
        })

    df = pd.DataFrame(habit_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    session.close()
