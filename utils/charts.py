"""
Reusable Plotly chart builders for the dashboard.
All charts use a consistent dark theme.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# ── Theme constants ──────────────────────────────────────────────────────────
BG       = "rgba(0,0,0,0)"
GRID_CLR = "rgba(255,255,255,0.07)"
FONT_CLR = "#e2e8f0"
ACCENT   = "#6366f1"
PALETTE  = ["#6366f1","#22d3ee","#f59e0b","#10b981","#f43f5e","#a78bfa","#34d399"]

BASE_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font=dict(color=FONT_CLR, family="Inter, sans-serif"),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR),
    yaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR),
)


def _apply(fig):
    fig.update_layout(**BASE_LAYOUT)
    return fig


# ── Chart functions ──────────────────────────────────────────────────────────

def expense_pie_chart(df: pd.DataFrame):
    """Category-wise expense pie chart."""
    if df.empty:
        return _empty_fig("No expense data yet")
    cat_totals = df.groupby("category")["amount"].sum().reset_index()
    fig = px.pie(
        cat_totals, values="amount", names="category",
        color_discrete_sequence=PALETTE, hole=0.4
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply(fig)


def monthly_expense_line(df: pd.DataFrame):
    """Daily spending trend line chart."""
    if df.empty:
        return _empty_fig("No expense data yet")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    daily = df.groupby("date")["amount"].sum().reset_index()
    fig = px.line(
        daily, x="date", y="amount",
        markers=True, color_discrete_sequence=[ACCENT]
    )
    fig.update_traces(fill="tozeroy", fillcolor="rgba(99,102,241,0.12)")
    return _apply(fig)


def monthly_bar_chart(df: pd.DataFrame):
    """Month-over-month spending bar chart."""
    if df.empty:
        return _empty_fig("No expense data yet")
    df = df.copy()
    df["date"]  = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.strftime("%b %Y")
    monthly     = df.groupby("month")["amount"].sum().reset_index()
    fig = px.bar(
        monthly, x="month", y="amount",
        color_discrete_sequence=[ACCENT]
    )
    return _apply(fig)


def productivity_bar(completed: int, pending: int):
    """Task completion bar chart."""
    fig = go.Figure(go.Bar(
        x=["Completed", "Pending"],
        y=[completed, pending],
        marker_color=[PALETTE[4] if pending else PALETTE[3], PALETTE[0]],
        text=[completed, pending],
        textposition="outside"
    ))
    fig.update_layout(showlegend=False, **BASE_LAYOUT)
    return fig


def habit_heatmap(checkin_df: pd.DataFrame, habit_name: str):
    """Calendar-style heatmap for a habit's check-ins (last 12 weeks)."""
    today = datetime.today().date()
    start = today - timedelta(weeks=12)
    date_range = pd.date_range(start, today, freq="D")
    heat = pd.DataFrame({"date": date_range})
    heat["date"] = heat["date"].dt.date

    if not checkin_df.empty:
        checkin_df = checkin_df.copy()
        checkin_df["date"] = pd.to_datetime(checkin_df["date"]).dt.date
        heat = heat.merge(
            checkin_df.assign(done=1)[["date", "done"]],
            on="date", how="left"
        ).fillna(0)
    else:
        heat["done"] = 0

    heat["week"]    = pd.to_datetime(heat["date"]).dt.isocalendar().week
    heat["weekday"] = pd.to_datetime(heat["date"]).dt.weekday

    fig = go.Figure(go.Heatmap(
        x=heat["week"],
        y=heat["weekday"],
        z=heat["done"],
        colorscale=[[0, "rgba(255,255,255,0.06)"], [1, PALETTE[1]]],
        showscale=False,
        xgap=3, ygap=3
    ))
    fig.update_yaxes(
        tickvals=list(range(7)),
        ticktext=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    )
    fig.update_layout(title=f"Check-in heatmap: {habit_name}", **BASE_LAYOUT)
    return fig


def goal_progress_chart(goals: list[dict]):
    """Horizontal bar chart showing goal progress."""
    if not goals:
        return _empty_fig("No goals yet")
    names = [g["name"] for g in goals]
    pcts  = [min(g["progress"] / g["target"] * 100, 100) for g in goals]
    fig   = go.Figure(go.Bar(
        x=pcts, y=names, orientation="h",
        marker_color=PALETTE[:len(goals)],
        text=[f"{p:.0f}%" for p in pcts],
        textposition="inside"
    ))
    fig.update_xaxes(range=[0, 100])
    fig.update_layout(showlegend=False, **BASE_LAYOUT)
    return fig


def life_score_gauge(score: float):
    """Gauge chart for life score (0–100)."""
    color = PALETTE[4] if score < 40 else PALETTE[2] if score < 70 else PALETTE[3]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Life Score", "font": {"color": FONT_CLR}},
        gauge={
            "axis":       {"range": [0, 100], "tickcolor": FONT_CLR},
            "bar":        {"color": color},
            "bgcolor":    "rgba(255,255,255,0.05)",
            "bordercolor": "rgba(255,255,255,0.1)",
            "steps": [
                {"range": [0,  40], "color": "rgba(244,63,94,0.15)"},
                {"range": [40, 70], "color": "rgba(245,158,11,0.15)"},
                {"range": [70,100], "color": "rgba(16,185,129,0.15)"},
            ],
        }
    ))
    fig.update_layout(paper_bgcolor=BG, font=dict(color=FONT_CLR), margin=dict(t=30, b=10))
    return fig


def _empty_fig(msg: str):
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(color=FONT_CLR, size=14))
    return _apply(fig)
