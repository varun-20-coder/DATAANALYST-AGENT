"""
AI Data Analyst Agent
======================
Upload a CSV/Excel file, get automatic cleaning + EDA, chat with your
data in plain English, generate SQL from natural language, forecast
trends, and export a polished PDF report.

Run locally:
    streamlit run app.py
"""

import os
import sqlite3
import tempfile

import pandas as pd
import streamlit as st

from utils import data_cleaning as dc
from utils import visualization as viz
from utils import ai_agent as agent
from utils import report_generator as report
from models import forecasting as fc


# ---------------------------------------------------------------------------
# Page config & styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Data Analyst Agent",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-title {font-size: 2.1rem; font-weight: 700; color: #1e3c72; margin-bottom: 0;}
    .subtitle {color: #666; font-size: 1rem; margin-top: 0;}
    .stTabs [data-baseweb="tab-list"] {gap: 6px;}
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6; border-radius: 8px 8px 0 0; padding: 8px 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">📊 AI Data Analyst Agent</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Upload any CSV/Excel file and get instant cleaning, EDA, '
    'AI-powered Q&A, SQL generation, forecasts, and a downloadable report.</p>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
for key, default in {
    "df": None,
    "raw_df": None,
    "cleaning_report": [],
    "date_cols": [],
    "filename": None,
    "api_key": "",
    "insights_text": "",
    "exec_summary": "",
    "chart_paths": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------------------------------------------------------
# Sidebar: file upload + API key
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Setup")

    api_key_input = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=st.session_state.api_key,
        help="Get a free key at https://aistudio.google.com/app/apikey",
    )
    st.session_state.api_key = api_key_input

    if not st.session_state.api_key:
        st.info(agent.offline_notice())

    st.markdown("---")
    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])

    if uploaded_file is not None and uploaded_file.name != st.session_state.filename:
        try:
            raw_df = dc.load_data(uploaded_file)
            cleaned_df, cleaning_report, date_cols = dc.clean_data(raw_df.copy())
            st.session_state.raw_df = raw_df
            st.session_state.df = cleaned_df
            st.session_state.cleaning_report = cleaning_report
            st.session_state.date_cols = date_cols
            st.session_state.filename = uploaded_file.name
            st.session_state.insights_text = ""
            st.session_state.exec_summary = ""
            st.success(f"Loaded '{uploaded_file.name}' successfully!")
        except Exception as e:
            st.error(f"Failed to load file: {e}")

    if st.session_state.df is not None:
        st.markdown("---")
        st.caption("📁 Or try the bundled sample dataset")
    if st.button("Load sample_data.csv"):
        sample_path = os.path.join(os.path.dirname(__file__), "sample_data.csv")
        raw_df = pd.read_csv(sample_path)
        cleaned_df, cleaning_report, date_cols = dc.clean_data(raw_df.copy())
        st.session_state.raw_df = raw_df
        st.session_state.df = cleaned_df
        st.session_state.cleaning_report = cleaning_report
        st.session_state.date_cols = date_cols
        st.session_state.filename = "sample_data.csv"
        st.session_state.insights_text = ""
        st.session_state.exec_summary = ""
        st.success("Loaded sample dataset!")

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
if st.session_state.df is None:
    st.info("👈 Upload a CSV/Excel file or load the sample dataset from the sidebar to get started.")
    st.stop()

df = st.session_state.df
roles = dc.guess_column_roles(df)

tabs = st.tabs([
    "🔎 Overview",
    "📈 Visualizations",
    "💬 Chat with Data",
    "🗄️ SQL Assistant",
    "🔮 Forecast",
    "🧠 Insights & Report",
])

# ---------------------------------------------------------------------------
# TAB 1: Overview
# ---------------------------------------------------------------------------
with tabs[0]:
    st.subheader("Dataset Preview")
    st.dataframe(df.head(20), use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", f"{df.shape[0]:,}")
    col2.metric("Columns", df.shape[1])
    col3.metric("Missing Cells", int(df.isna().sum().sum()))

    with st.expander("🧹 Data Cleaning Report", expanded=True):
        for line in st.session_state.cleaning_report:
            st.write(f"- {line}")

    st.subheader("Summary Statistics")
    numeric_summary, cat_summary = dc.get_summary_stats(df)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Numeric Columns**")
        st.dataframe(numeric_summary, use_container_width=True)
    with c2:
        st.markdown("**Categorical Columns**")
        st.dataframe(cat_summary, use_container_width=True)

    st.subheader("Missing Values")
    missing_df = dc.detect_missing(df)
    if missing_df.empty:
        st.success("No missing values detected. ✅")
    else:
        st.dataframe(missing_df, use_container_width=True)
        fig = viz.plot_missing_values(missing_df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Outlier Detection (IQR method)")
    outliers = dc.detect_outliers_iqr(df)
    if not outliers:
        st.success("No significant outliers detected. ✅")
    else:
        st.write(outliers)

# ---------------------------------------------------------------------------
# TAB 2: Visualizations
# ---------------------------------------------------------------------------
with tabs[1]:
    st.subheader("Explore Your Data Visually")

    numeric_cols = roles["numeric_cols"]
    categorical_cols = roles["categorical_cols"]
    date_cols = roles["date_cols"]

    viz_type = st.selectbox(
        "Choose a chart type",
        ["Trend over time", "Bar chart by category", "Correlation heatmap", "Distribution"],
    )

    if viz_type == "Trend over time":
        if not date_cols:
            st.warning("No date column detected in this dataset.")
        else:
            c1, c2, c3 = st.columns(3)
            date_col = c1.selectbox("Date column", date_cols)
            value_col = c2.selectbox("Value column", numeric_cols)
            freq_label = c3.selectbox("Aggregate by", ["Day", "Week", "Month", "Quarter", "Year"], index=2)
            freq_map = {"Day": "D", "Week": "W", "Month": "ME", "Quarter": "QE", "Year": "YE"}
            if value_col:
                fig = viz.plot_trend(df, date_col, value_col, freq=freq_map[freq_label])
                st.plotly_chart(fig, use_container_width=True)

    elif viz_type == "Bar chart by category":
        if not categorical_cols or not numeric_cols:
            st.warning("Need at least one categorical and one numeric column.")
        else:
            c1, c2, c3 = st.columns(3)
            cat_col = c1.selectbox("Category column", categorical_cols)
            val_col = c2.selectbox("Value column", numeric_cols)
            top_n = c3.slider("Top N", 3, 20, 10)
            fig = viz.plot_bar_by_category(df, cat_col, val_col, top_n=top_n)
            st.plotly_chart(fig, use_container_width=True)

    elif viz_type == "Correlation heatmap":
        corr = dc.get_correlation(df)
        if corr.empty:
            st.warning("Need at least two numeric columns for a correlation heatmap.")
        else:
            fig = viz.plot_correlation_heatmap(corr)
            st.plotly_chart(fig, use_container_width=True)

    elif viz_type == "Distribution":
        if not numeric_cols:
            st.warning("No numeric columns available.")
        else:
            col = st.selectbox("Column", numeric_cols)
            fig = viz.plot_distribution(df, col)
            st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 3: Chat with Data
# ---------------------------------------------------------------------------
with tabs[2]:
    st.subheader("💬 Ask Questions About Your Data")
    st.caption(
        "Examples: \"Which region has the highest sales?\", "
        "\"Which products are underperforming?\", \"Summarize the key trends.\""
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    question = st.chat_input("Ask a question about your dataset...")
    if question:
        st.session_state.chat_history.append(("user", question))
        with st.chat_message("user"):
            st.markdown(question)

        if not st.session_state.api_key:
            answer = agent.offline_notice()
        else:
            schema_str = dc.dataframe_to_schema_string(df)
            with st.spinner("Analyzing your data..."):
                answer = agent.ask_question(schema_str, question, st.session_state.api_key)

        st.session_state.chat_history.append(("assistant", answer))
        with st.chat_message("assistant"):
            st.markdown(answer)

# ---------------------------------------------------------------------------
# TAB 4: SQL Assistant (Natural Language -> SQL)
# ---------------------------------------------------------------------------
with tabs[3]:
    st.subheader("🗄️ Natural Language to SQL")
    st.caption("Example: \"Show the top 10 customers by revenue\"")

    nl_query = st.text_input("Type your question in plain English", key="nl_sql_input")

    if st.button("Generate & Run SQL"):
        if not st.session_state.api_key:
            st.warning(agent.offline_notice())
        elif not nl_query:
            st.warning("Please enter a question first.")
        else:
            table_name = "data"
            schema_str = dc.dataframe_to_schema_string(df, max_sample_rows=3)

            with st.spinner("Generating SQL..."):
                sql_query = agent.generate_sql_from_nl(nl_query, table_name, schema_str, st.session_state.api_key)

            st.code(sql_query, language="sql")

            try:
                conn = sqlite3.connect(":memory:")
                df.to_sql(table_name, conn, index=False, if_exists="replace")
                result_df = pd.read_sql_query(sql_query, conn)
                conn.close()

                st.dataframe(result_df, use_container_width=True)

                fig = viz.plot_generic_from_sql_result(result_df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Could not execute the generated SQL: {e}")

# ---------------------------------------------------------------------------
# TAB 5: Forecast
# ---------------------------------------------------------------------------
with tabs[4]:
    st.subheader("🔮 Forecast Future Values")

    date_cols = roles["date_cols"]
    numeric_cols = roles["numeric_cols"]

    if not date_cols or not numeric_cols:
        st.warning("Forecasting requires at least one date column and one numeric column.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        date_col = c1.selectbox("Date column", date_cols, key="fc_date")
        value_col = c2.selectbox("Value to forecast", numeric_cols, key="fc_value")
        freq_label = c3.selectbox("Period", ["Week", "Month", "Quarter"], index=1, key="fc_freq")
        periods = c4.number_input("Periods ahead", min_value=1, max_value=12, value=1)

        freq_map = {"Week": "W", "Month": "ME", "Quarter": "QE"}

        if st.button("Run Forecast"):
            try:
                history_df, forecast_df, summary = fc.forecast_next_periods(
                    df, date_col, value_col, freq=freq_map[freq_label], periods_ahead=periods
                )
                fig = viz.plot_forecast(history_df, date_col, value_col, forecast_df)
                st.plotly_chart(fig, use_container_width=True)
                st.info(summary)
                st.dataframe(forecast_df, use_container_width=True)
            except Exception as e:
                st.error(f"Forecast failed: {e}")

# ---------------------------------------------------------------------------
# TAB 6: Insights & Report
# ---------------------------------------------------------------------------
with tabs[5]:
    st.subheader("🧠 AI-Generated Business Insights")

    if st.button("Generate Insights & Recommendations"):
        if not st.session_state.api_key:
            st.warning(agent.offline_notice())
        else:
            schema_str = dc.dataframe_to_schema_string(df)
            numeric_summary, cat_summary = dc.get_summary_stats(df)
            stats_str = f"Numeric summary:\n{numeric_summary.to_string()}\n\nCategorical summary:\n{cat_summary.to_string()}"

            with st.spinner("Generating insights..."):
                insights_text = agent.generate_insights(schema_str, stats_str, st.session_state.api_key)
                exec_summary = agent.generate_executive_summary(schema_str, insights_text, st.session_state.api_key)

            st.session_state.insights_text = insights_text
            st.session_state.exec_summary = exec_summary

    if st.session_state.insights_text:
        st.markdown("### Executive Summary")
        st.write(st.session_state.exec_summary)
        st.markdown("### Insights & Recommendations")
        st.markdown(st.session_state.insights_text)

    st.markdown("---")
    st.subheader("📄 Export PDF Report")

    if st.button("Generate PDF Report"):
        with st.spinner("Building report..."):
            tmp_dir = tempfile.mkdtemp()
            chart_paths = []

            # Export a couple of representative charts as images for the PDF
            try:
                corr = dc.get_correlation(df)
                if not corr.empty:
                    fig = viz.plot_correlation_heatmap(corr)
                    path = os.path.join(tmp_dir, "corr.png")
                    fig.write_image(path, width=800, height=500)
                    chart_paths.append(path)
            except Exception:
                pass  # kaleido may be unavailable in some environments

            pdf_path = os.path.join(tmp_dir, "report.pdf")
            report.generate_pdf_report(
                output_path=pdf_path,
                dataset_name=st.session_state.filename or "dataset",
                shape=df.shape,
                cleaning_report=st.session_state.cleaning_report,
                executive_summary=st.session_state.exec_summary or "No executive summary generated yet.",
                insights_text=st.session_state.insights_text or "No insights generated yet. "
                "Click 'Generate Insights & Recommendations' above first.",
                chart_image_paths=chart_paths,
            )

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ Download PDF Report",
                    data=f.read(),
                    file_name="AI_Data_Analyst_Report.pdf",
                    mime="application/pdf",
                )

st.markdown("---")
st.caption("Built with Streamlit, Pandas, Plotly, and Google Gemini API · AI Data Analyst Agent")
