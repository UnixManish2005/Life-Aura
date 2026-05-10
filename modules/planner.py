"""
Daily Planner – add, edit, delete tasks with priority and categories.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import date, datetime

from utils.db import get_session, Task
from utils.auth import require_login

CATEGORIES = ["Work", "Personal", "Health", "Learning", "Finance", "Social", "Other"]
PRIORITIES  = ["High", "Medium", "Low"]


def render():
    require_login()
    user_id = st.session_state["user_id"]

    st.markdown('<p class="page-title">📋 Daily Planner</p>', unsafe_allow_html=True)
    st.caption("Manage your tasks, set priorities, and track daily completion.")
    st.divider()

    session = get_session()
    tasks   = session.query(Task).filter(Task.user_id == user_id).order_by(Task.created_at.desc()).all()

    # ── Summary metrics ───────────────────────────────────────────────────────
    total    = len(tasks)
    done     = sum(1 for t in tasks if t.status == "Completed")
    pending  = total - done
    today    = date.today()
    overdue  = sum(1 for t in tasks if t.status == "Pending" and t.due_date and t.due_date < today)
    rate     = int(done / total * 100) if total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tasks",      total)
    c2.metric("✅ Completed",      done)
    c3.metric("⏳ Pending",        pending)
    c4.metric("⚠️ Overdue",        overdue)
    st.progress(rate / 100, text=f"Completion: {rate}%")
    st.divider()

    # ── Add task ──────────────────────────────────────────────────────────────
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("add_task_form"):
            col1, col2 = st.columns(2)
            task_name  = col1.text_input("Task Name *")
            category   = col2.selectbox("Category", CATEGORIES)
            col3, col4 = st.columns(2)
            priority   = col3.selectbox("Priority", PRIORITIES)
            due_date   = col4.date_input("Due Date", value=today)
            submitted  = st.form_submit_button("Add Task")

        if submitted:
            if task_name.strip():
                new_task = Task(
                    user_id=user_id, task_name=task_name.strip(),
                    category=category, priority=priority, due_date=due_date
                )
                session.add(new_task)
                session.commit()
                st.success(f"Task **{task_name}** added!")
                st.rerun()
            else:
                st.error("Task name cannot be empty.")

    # ── Task tabs ─────────────────────────────────────────────────────────────
    tab_pending, tab_done, tab_all = st.tabs(["⏳ Pending", "✅ Completed", "📑 All Tasks"])

    def task_card(t: Task, key_prefix: str):
        pri_map = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
        icon    = pri_map.get(t.priority, "⚪")
        overdue_flag = t.due_date and t.due_date < today and t.status == "Pending"

        with st.container():
            col_name, col_cat, col_due, col_act = st.columns([3, 1.5, 1.5, 2])
            col_name.markdown(
                f"{icon} **{t.task_name}**"
                + (" 🚨" if overdue_flag else "")
            )
            col_cat.caption(t.category)
            col_due.caption(str(t.due_date) if t.due_date else "—")

            with col_act:
                btn_col1, btn_col2 = st.columns(2)
                if t.status == "Pending":
                    if btn_col1.button("✅", key=f"done_{key_prefix}_{t.id}", help="Mark complete"):
                        t.status = "Completed"
                        session.commit()
                        st.rerun()
                else:
                    if btn_col1.button("↩️", key=f"undo_{key_prefix}_{t.id}", help="Mark pending"):
                        t.status = "Pending"
                        session.commit()
                        st.rerun()
                if btn_col2.button("🗑️", key=f"del_{key_prefix}_{t.id}", help="Delete"):
                    session.delete(t)
                    session.commit()
                    st.rerun()
        st.markdown('<hr style="margin:4px 0; opacity:0.15">', unsafe_allow_html=True)

    with tab_pending:
        pending_tasks = [t for t in tasks if t.status == "Pending"]
        if pending_tasks:
            st.markdown(
                '<p class="section-label">Priority · Task · Category · Due · Actions</p>',
                unsafe_allow_html=True
            )
            for t in pending_tasks:
                task_card(t, "pend")
        else:
            st.success("🎉 No pending tasks — great job!")

    with tab_done:
        done_tasks = [t for t in tasks if t.status == "Completed"]
        if done_tasks:
            for t in done_tasks:
                task_card(t, "done")
        else:
            st.info("No completed tasks yet.")

    with tab_all:
        if tasks:
            df = pd.DataFrame([{
                "ID":       t.id,
                "Task":     t.task_name,
                "Category": t.category,
                "Priority": t.priority,
                "Due":      t.due_date,
                "Status":   t.status,
                "Created":  t.created_at.strftime("%Y-%m-%d"),
            } for t in tasks])
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False)
            st.download_button("⬇️ Export CSV", csv, "tasks.csv", "text/csv")
        else:
            st.info("No tasks found.")

    session.close()
