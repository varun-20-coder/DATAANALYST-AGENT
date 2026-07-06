# 📊 AI Data Analyst Agent

An AI-powered data analysis agent that lets you **upload any CSV/Excel dataset**
and instantly get automatic cleaning, exploratory data analysis, natural-language
Q&A, SQL generation, forecasting, business insights, and a downloadable PDF report.

Built entirely with **free tools**: Streamlit, Pandas, Plotly, scikit-learn, and
the free tier of the **Google Gemini API**.

---

## ✨ Features

- 📂 Upload CSV or Excel files
- 🧹 Automatic data cleaning (duplicates, missing values, type detection, date parsing)
- 📊 Summary statistics, missing-value report, outlier detection (IQR)
- 🔗 Correlation heatmap
- 📈 Interactive Plotly visualizations (trend, bar, distribution, heatmap)
- 💬 **Chat with your data** — ask questions in plain English
- 🗄️ **Natural language → SQL** assistant (SQLite backend)
- 🔮 Simple trend forecasting ("predict next month's sales")
- 🧠 AI-generated business insights & recommendations (Gemini API)
- 📄 One-click downloadable PDF report

---

## 🗂️ Project Structure

```
AI-Data-Agent/
│
├── app.py                     # Main Streamlit application
├── requirements.txt           # Python dependencies
├── data/                      # Place additional datasets here (optional)
├── utils/
│   ├── data_cleaning.py       # Loading, cleaning, EDA helper functions
│   ├── visualization.py       # Plotly chart builders
│   ├── ai_agent.py            # Gemini API wrapper (Q&A, SQL gen, insights)
│   └── report_generator.py    # PDF report builder (fpdf2)
├── models/
│   └── forecasting.py         # Lightweight linear-regression forecasting
├── assets/                    # Static assets (logos, screenshots, etc.)
├── README.md
└── sample_data.csv            # Bundled synthetic 2-year sales dataset for demo
```

---

## 🚀 Getting Started (Local)

### 1. Clone / unzip the project
```bash
cd AI-Data-Agent
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get a free Gemini API key
Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
and generate a free API key. You'll paste this into the app's sidebar — it is
**never** hard-coded or committed to the repo.

### 5. Run the app
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. Upload your own CSV/Excel file, or
click **"Load sample_data.csv"** in the sidebar to explore with demo data.

---

## ☁️ Free Deployment (Streamlit Community Cloud)

1. Push this project to a public GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **"New app"**, select your repo, branch, and set the main file to `app.py`.
4. Deploy. You'll get a public URL like:
   ```
   https://your-app-name.streamlit.app
   ```
5. Users paste their own free Gemini API key into the sidebar at runtime — no
   secrets need to be stored on the server for the basic demo. (Optionally, you
   can pre-configure a key via Streamlit's `st.secrets` for a fully turnkey demo.)
6. Add the live link to your resume / LinkedIn / portfolio.

---

## 🧠 How It Works (Architecture)

```
 CSV / Excel Upload
        │
        ▼
 Pandas Data Cleaning  (utils/data_cleaning.py)
        │
        ▼
 AI Agent (Google Gemini API)  (utils/ai_agent.py)
        │
        ├── Answer Natural-Language Questions
        ├── Generate SQL from Natural Language
        ├── Detect Trends / Outliers / Missing Data
        ├── Generate Business Insights
        └── Generate Recommendations & Executive Summary
        │
        ▼
 Streamlit Dashboard (app.py)
   ├── Overview & EDA
   ├── Visualizations (Plotly)
   ├── Chat with Data
   ├── SQL Assistant (SQLite)
   ├── Forecast (scikit-learn Linear Regression)
   └── Insights & PDF Report Export
```

---

## 🛠️ Tech Stack

| Tool | Purpose | Free? |
|---|---|---|
| Python | Core language | ✅ |
| Streamlit | Interactive web UI | ✅ |
| Pandas / NumPy | Data cleaning & analysis | ✅ |
| Plotly | Interactive charts | ✅ |
| scikit-learn | Forecasting (Linear Regression) | ✅ |
| SQLite | In-memory SQL engine for the SQL Assistant | ✅ |
| Google Gemini API | Conversational analytics & insights | ✅ (free tier) |
| fpdf2 | PDF report generation | ✅ |
| GitHub + Streamlit Community Cloud | Hosting & deployment | ✅ |

---

## 📌 Example Questions to Try

- "Which region has the highest sales?"
- "Show the monthly sales trend."
- "Which products are underperforming?"
- "Predict next month's sales." *(use the Forecast tab)*
- "Show the top 10 customers by revenue." *(use the SQL Assistant tab)*

---

## 📄 Resume Blurb

> **AI Data Analyst Agent**
> *Technologies: Python, Pandas, Plotly, Streamlit, Gemini API, SQL, scikit-learn*
> Developed an AI-powered data analysis agent that allows users to upload
> CSV/Excel datasets and ask questions in natural language. Automated data
> cleaning, exploratory data analysis (EDA), visualization, forecasting, and
> business insight generation. Integrated Google's Gemini API for
> conversational analytics, natural-language-to-SQL querying, and actionable
> recommendations. Deployed on Streamlit Community Cloud for public access.

---

## 🔒 Notes on API Keys

- Never commit your Gemini API key to GitHub.
- The app reads the key at runtime from a sidebar input (session-only, not persisted).
- For a fixed personal deployment, you can instead store it in
  `.streamlit/secrets.toml` (excluded from version control) and read it via
  `st.secrets["GEMINI_API_KEY"]`.

---

## 🧪 Offline / Demo Mode

If no Gemini API key is provided, the cleaning, EDA, visualization, SQL
execution (with manually written SQL), and forecasting features still work
fully — only the AI-generated Q&A, NL-to-SQL, and insights features require
the API key.
