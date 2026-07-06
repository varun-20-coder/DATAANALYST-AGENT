"""
forecasting.py
---------------
Lightweight forecasting utilities used to answer questions like
"Predict next month's sales." Uses simple linear regression over
resampled time-period aggregates -- no heavy ML dependencies required.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def forecast_next_periods(df, date_col, value_col, freq="ME", periods_ahead=1, agg="sum"):
    """
    Aggregate `value_col` by time period (freq) and fit a simple linear
    regression on the period index to forecast the next `periods_ahead`
    periods.

    Returns:
        history_df: DataFrame with columns [date_col, value_col] (actuals)
        forecast_df: DataFrame with columns [date_col, value_col] (predicted)
        summary: str, human-readable explanation of the trend
    """
    temp = df[[date_col, value_col]].dropna().sort_values(date_col)
    temp = temp.set_index(date_col)
    history = temp.resample(freq).agg(agg).reset_index()
    history = history.dropna()

    if len(history) < 2:
        raise ValueError("Not enough historical data points to build a forecast.")

    history["period_index"] = np.arange(len(history))

    X = history[["period_index"]].values
    y = history[value_col].values

    model = LinearRegression()
    model.fit(X, y)

    last_index = history["period_index"].max()
    future_indices = np.arange(last_index + 1, last_index + 1 + periods_ahead).reshape(-1, 1)
    predictions = model.predict(future_indices)
    predictions = np.clip(predictions, a_min=0, a_max=None)  # sales can't be negative

    # Build future dates based on inferred frequency
    last_date = history[date_col].max()
    future_dates = pd.date_range(start=last_date, periods=periods_ahead + 1, freq=freq)[1:]

    forecast_df = pd.DataFrame({date_col: future_dates, value_col: predictions})

    slope = model.coef_[0]
    trend_word = "increasing" if slope > 0 else ("decreasing" if slope < 0 else "flat")
    avg_value = history[value_col].mean()
    pct_change = (slope / avg_value * 100) if avg_value != 0 else 0

    summary = (
        f"Based on {len(history)} historical periods, the trend for '{value_col}' is "
        f"{trend_word}, changing by approximately {pct_change:.1f}% per period on average. "
        f"The forecasted value for the next period is {predictions[0]:,.2f}."
    )

    return history[[date_col, value_col]], forecast_df, summary
