"""
PDF report generation using fpdf2.
Generates monthly productivity and expense reports.
"""

import io
from datetime import datetime
from fpdf import FPDF


class DashboardReport(FPDF):
    """Custom FPDF subclass with header/footer branding."""

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(99, 102, 241)
        self.cell(0, 10, "AI Life Dashboard", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", size=9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, f"Report generated: {datetime.now().strftime('%d %b %Y, %H:%M')}", 
                  align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_draw_color(99, 102, 241)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(99, 102, 241)
        self.ln(4)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.2)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def kv_row(self, key: str, value: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(70, 7, key)
        self.set_font("Helvetica", size=10)
        self.set_text_color(40, 40, 40)
        self.cell(0, 7, str(value), new_x="LMARGIN", new_y="NEXT")

    def paragraph(self, text: str):
        self.set_font("Helvetica", size=10)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 6, text)
        self.ln(2)


def generate_report(
    username:      str,
    task_stats:    dict,
    expense_stats: dict,
    habit_stats:   dict,
    goal_stats:    dict,
    ai_summary:    str = "",
) -> bytes:
    """
    Build a PDF report and return it as bytes.

    task_stats    : {completed, total, overdue}
    expense_stats : {total, budget, categories: {cat: amount}}
    habit_stats   : {habits: [{name, streak}], avg_streak}
    goal_stats    : {goals: [{name, progress, target}]}
    """
    pdf = DashboardReport()
    pdf.add_page()

    # ── Cover info ──────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 30, 30)
    month = datetime.now().strftime("%B %Y")
    pdf.ln(4)
    pdf.cell(0, 12, f"Monthly Report – {month}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, f"User: {username}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # ── Task summary ────────────────────────────────────────────────────────
    pdf.section_title("📋 Task Summary")
    completed = task_stats.get("completed", 0)
    total     = task_stats.get("total", 0)
    rate      = f"{(completed/total*100):.0f}%" if total else "N/A"
    pdf.kv_row("Total Tasks:",      str(total))
    pdf.kv_row("Completed:",        str(completed))
    pdf.kv_row("Pending / Overdue:",f"{total - completed} / {task_stats.get('overdue', 0)}")
    pdf.kv_row("Completion Rate:",  rate)

    # ── Expense summary ─────────────────────────────────────────────────────
    pdf.section_title("💰 Expense Summary")
    total_exp = expense_stats.get("total", 0)
    budget    = expense_stats.get("budget", 0)
    cats      = expense_stats.get("categories", {})
    pdf.kv_row("Total Expenses:", f"Rs {total_exp:.2f}")
    pdf.kv_row("Monthly Budget:", f"Rs {budget:.2f}" if budget else "Not set")
    if budget and total_exp > budget:
        pdf.set_text_color(220, 50, 50)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, f"⚠ Budget exceeded by Rs {total_exp - budget:.2f}!", 
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(60, 60, 60)
    pdf.ln(2)
    if cats:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 6, "Category breakdown:", new_x="LMARGIN", new_y="NEXT")
        for cat, amt in cats.items():
            pdf.kv_row(f"  {cat}:", f"Rs {amt:.2f}")

    # ── Habit summary ───────────────────────────────────────────────────────
    pdf.section_title("🔥 Habit Summary")
    avg_streak = habit_stats.get("avg_streak", 0)
    pdf.kv_row("Average Streak:", f"{avg_streak:.1f} days")
    habits = habit_stats.get("habits", [])
    if habits:
        for h in habits:
            pdf.kv_row(f"  {h['name']}:", f"Streak: {h['streak']} days")

    # ── Goal summary ────────────────────────────────────────────────────────
    pdf.section_title("🎯 Goal Progress")
    goals = goal_stats.get("goals", [])
    if goals:
        for g in goals:
            pct = min(g["progress"] / g["target"] * 100, 100) if g["target"] else 0
            pdf.kv_row(f"  {g['name']}:", f"{pct:.0f}% complete")
    else:
        pdf.paragraph("No goals recorded this month.")

    # ── AI Summary ──────────────────────────────────────────────────────────
    if ai_summary:
        pdf.section_title("🤖 AI Monthly Insights")
        pdf.paragraph(ai_summary)

    # ── Return bytes ────────────────────────────────────────────────────────
    return bytes(pdf.output())
