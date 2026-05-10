# 🚀 AI Life Dashboard

A modern, production-ready **Personal Productivity & Expense Analytics Dashboard** built with Python and Streamlit. Track tasks, habits, expenses, goals, and get AI-powered insights — all in one beautiful dark-themed app.

---

## ✨ Features

| Module | Highlights |
|---|---|
| 🏠 Dashboard | Life score, KPI cards, daily summary |
| 📋 Daily Planner | Tasks, priorities, categories, completion tracking |
| 🔥 Habit Tracker | Streaks, check-ins, 12-week heatmaps |
| 💰 Expense Tracker | Budgets, alerts, category analytics |
| 🎯 Goals | Progress tracking, deadline reminders |
| 📊 Analytics | Interactive Plotly charts for all modules |
| 🤖 AI Insights | Spending/productivity analysis + chat assistant |
| 📄 Reports | Download PDF & CSV reports |
| ⚙️ Settings | Profile, budget, API key config |

---

## 🛠️ Tech Stack

- **Frontend + Backend**: Streamlit
- **Database**: SQLite via SQLAlchemy ORM
- **Charts**: Plotly
- **AI**: OpenRouter API (free tier)
- **PDF**: fpdf2
- **Auth**: bcrypt password hashing

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourname/ai-life-dashboard.git
cd ai-life-dashboard
```

### 2. Create a virtual environment

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Edit the `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

Get your **free** API key at [https://openrouter.io/keys](https://openrouter.io/keys).

### 5. Run the app

```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

---

## 🔑 OpenRouter API Setup

1. Go to [https://openrouter.io](https://openrouter.io) and create a free account.
2. Navigate to **Keys** and create a new API key.
3. Add the key to your `.env` file or via the **Settings → API Config** page in the dashboard.

Free models supported:
- `mistralai/mistral-7b-instruct`
- `deepseek/deepseek-chat`
- `meta-llama/llama-3-8b-instruct`

---

## 🗂️ Project Structure

```
life_dashboard/
├── app.py                  # Main entry point
├── requirements.txt
├── .env                    # API key config
│
├── database/
│   └── database.db         # Auto-created SQLite database
│
├── pages/
│   ├── dashboard.py        # Overview & life score
│   ├── planner.py          # Task management
│   ├── habits.py           # Habit tracking
│   ├── expenses.py         # Expense tracking
│   ├── goals.py            # Goal management
│   ├── analytics.py        # Analytics charts
│   ├── ai_insights.py      # AI analysis + chatbot
│   ├── reports.py          # PDF/CSV export
│   └── settings.py         # User settings
│
├── utils/
│   ├── db.py               # SQLAlchemy models & session
│   ├── ai_helper.py        # OpenRouter API integration
│   ├── auth.py             # Authentication helpers
│   ├── charts.py           # Plotly chart builders
│   └── report_generator.py # PDF generation with fpdf2
│
└── assets/
    └── style.css           # Custom dark theme CSS
```

---

## 🌐 Deployment

### Streamlit Cloud (Recommended – Free)

1. Push your code to a public GitHub repository.
2. Go to [https://share.streamlit.io](https://share.streamlit.io).
3. Connect your GitHub repo and set the main file to `app.py`.
4. Add your `OPENROUTER_API_KEY` in the **Secrets** section:
   ```toml
   OPENROUTER_API_KEY = "sk-or-..."
   ```
5. Deploy!

> **Note**: On Streamlit Cloud, the SQLite database resets on each deployment. For production persistence, consider migrating to PostgreSQL.

### Render

1. Create a new **Web Service** on [https://render.com](https://render.com).
2. Connect your GitHub repository.
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Add environment variable: `OPENROUTER_API_KEY`
6. Deploy.

---

## 🔐 Security Notes

- Passwords are hashed with **bcrypt** before storage.
- The `.env` file should never be committed to version control.
- Add `.env` to your `.gitignore`.

---

## 🧮 Life Score Formula

```
Life Score = (Task Completion × 40%) 
           + (Habit Consistency × 30%) 
           + (Expense Control × 20%) 
           + (Goal Progress × 10%)
```

Score ranges:
- 🔴 0–40: Needs improvement
- 🟡 40–70: On track
- 🟢 70–100: Excellent

---

## 📊 Database Schema

| Table | Key Columns |
|---|---|
| `users` | id, username, email, password_hash |
| `tasks` | id, user_id, task_name, category, priority, due_date, status |
| `habits` | id, user_id, habit_name, streak, completion_date |
| `habit_checkins` | id, habit_id, date |
| `expenses` | id, user_id, amount, category, description, date |
| `goals` | id, user_id, goal_name, target, progress, deadline |

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

## 📄 License

MIT License – see [LICENSE](LICENSE) for details.
