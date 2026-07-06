"""
visualization.py
------------------
Reusable Plotly chart builders for the AI Data Analyst Agent.
All functions return a Plotly Figure object, ready to render with
st.plotly_chart(fig, use_container_width=True).
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


CHART_TEMPLATE = "plotly_white"


def plot_trend(df, date_col, value_col, freq="ME", agg="sum"):
    """Line chart of a value column aggregated over time."""
    temp = df[[date_col, value_col]].dropna()
    temp = temp.set_index(date_col)
    resampled = temp.resample(freq).agg(agg).reset_index()

    fig = px.line(
        resampled,
        x=date_col,
        y=value_col,
        markers=True,
        title=f"{value_col} Trend Over Time",
        template=CHART_TEMPLATE,
    )
    fig.update_layout(xaxis_title=date_col, yaxis_title=value_col)
    return fig


def plot_bar_by_category(df, category_col, value_col, agg="sum", top_n=None, ascending=False):
    """Bar chart showing a value aggregated by category, optionally top-N."""
    grouped = df.groupby(category_col)[value_col].agg(agg).reset_index()
    grouped = grouped.sort_values(value_col, ascending=ascending)
    if top_n:
        grouped = grouped.head(top_n)

    fig = px.bar(
        grouped,
        x=category_col,
        y=value_col,
        text_auto=".2s",
        title=f"{value_col} by {category_col}",
        template=CHART_TEMPLATE,
        color=value_col,
        color_continuous_scale="Blues",
    )
    fig.update_layout(xaxis_title=category_col, yaxis_title=value_col)
    return fig


def plot_correlation_heatmap(corr_df):
    """Heatmap of a correlation matrix."""
    fig = px.imshow(
        corr_df,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        title="Correlation Heatmap",
        template=CHART_TEMPLATE,
    )
    return fig


def plot_distribution(df, col, bins=30):
    """Histogram showing the distribution of a numeric column."""
    fig = px.histogram(
        df,
        x=col,
        nbins=bins,
        title=f"Distribution of {col}",
        template=CHART_TEMPLATE,
    )
    return fig


def plot_missing_values(missing_df):
    """Bar chart of missing value percentages per column."""
    if missing_df.empty:
        return None
    fig = px.bar(
        missing_df.reset_index().rename(columns={"index": "column"}),
        x="column",
        y="missing_pct",
        title="Missing Values by Column (%)",
        template=CHART_TEMPLATE,
        color="missing_pct",
        color_continuous_scale="Reds",
    )
    return fig


def plot_forecast(history_df, date_col, value_col, forecast_df):
    """
    Line chart showing historical values plus a forecasted continuation.
    forecast_df must have the same date_col / value_col columns.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history_df[date_col],
            y=history_df[value_col],
            mode="lines+markers",
            name="Actual",
            line=dict(color="#1f77b4"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_df[date_col],
            y=forecast_df[value_col],
            mode="lines+markers",
            name="Forecast",
            line=dict(color="#ff7f0e", dash="dash"),
        )
    )
    fig.update_layout(
        title=f"{value_col} Forecast",
        template=CHART_TEMPLATE,
        xaxis_title=date_col,
        yaxis_title=value_col,
    )
    return fig


def plot_generic_from_sql_result(result_df):
    """
    Try to auto-visualize an arbitrary SQL query result:
    - If there's exactly one categorical + one numeric column -> bar chart
    - If there's a date column + numeric -> line chart
    - Otherwise return None (display as table only)
    """
    if result_df.empty or result_df.shape[1] < 2:
        return None

    date_cols = [c for c in result_df.columns if pd.api.types.is_datetime64_any_dtype(result_df[c])]
    numeric_cols = [c for c in result_df.columns if pd.api.types.is_numeric_dtype(result_df[c])]
    other_cols = [c for c in result_df.columns if c not in date_cols and c not in numeric_cols]

    try:
        if date_cols and numeric_cols:
            return px.line(
                result_df, x=date_cols[0], y=numeric_cols[0],
                markers=True, template=CHART_TEMPLATE, title="Query Result Trend"
            )
        if other_cols and numeric_cols:
            return px.bar(
                result_df, x=other_cols[0], y=numeric_cols[0],
                template=CHART_TEMPLATE, title="Query Result", color=numeric_cols[0],
                color_continuous_scale="Blues",
            )
    except Exception:
        return None

    return None
