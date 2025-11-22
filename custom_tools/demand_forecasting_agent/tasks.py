import pandas as pd
import numpy as np
from datetime import datetime
from statsmodels.tsa.arima.model import ARIMA

# -----------------------------------------------------------
# Helper loader
# -----------------------------------------------------------
def _load_csv(csv_url: str):
    df = pd.read_csv(csv_url)
    df.columns = [c.lower() for c in df.columns]
    if "date" not in df or ("demand" not in df and "value" not in df):
        raise ValueError("CSV must contain columns: date, demand/value")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # unify column name
    if "value" in df:
        df.rename(columns={"value": "demand"}, inplace=True)
    return df


# -----------------------------------------------------------
# ML Forecasting Helpers
# -----------------------------------------------------------
def _forecast_arima(series, periods=1):
    model = ARIMA(series, order=(2,1,2))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=periods)
    return float(forecast.iloc[-1]), model_fit


# -----------------------------------------------------------
# DAILY FORECAST
# -----------------------------------------------------------
def daily_forecast(csv_url: str, target_date: str):
    df = _load_csv(csv_url)
    df = df.set_index("date")

    # calculate how many days forward
    last_date = df.index.max()
    target_dt = pd.to_datetime(target_date)
    periods = (target_dt - last_date).days

    if periods <= 0:
        # historical value
        if target_dt in df.index:
            return {
                "target": target_date,
                "prediction": float(df.loc[target_dt, "demand"]),
                "model_used": "ARIMA",
                "status": "success",
            }
        else:
            raise ValueError("Target date is before last data point, and no value exists.")

    pred, model_fit = _forecast_arima(df["demand"], periods=periods)

    return {
        "target": target_date,
        "prediction": pred,
        "model_used": "ARIMA",
        "status": "success",
    }


# -----------------------------------------------------------
# MONTHLY FORECAST
# -----------------------------------------------------------
def monthly_forecast(csv_url: str, target_month: str):
    df = _load_csv(csv_url)
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("month")["demand"].sum()
    monthly.index = monthly.index.to_timestamp()

    last = monthly.index.max()
    target_dt = pd.to_datetime(target_month + "-01")
    months_forward = (target_dt.year - last.year) * 12 + (target_dt.month - last.month)

    pred, model_fit = _forecast_arima(monthly, periods=max(1, months_forward))

    return {
        "target": target_month,
        "prediction": pred,
        "model_used": "ARIMA",
        "status": "success",
    }


# -----------------------------------------------------------
# YEARLY FORECAST
# -----------------------------------------------------------
def yearly_forecast(csv_url: str, target_year: str):
    df = _load_csv(csv_url)
    df["year"] = df["date"].dt.year
    yearly = df.groupby("year")["demand"].sum()

    last_year = yearly.index.max()
    target_y = int(target_year)
    years_forward = target_y - last_year

    pred, model_fit = _forecast_arima(yearly, periods=max(1, years_forward))

    return {
        "target": target_year,
        "prediction": pred,
        "model_used": "ARIMA",
        "status": "success",
    }


# -----------------------------------------------------------
# MASTER WRAPPER: generate_forecast
# -----------------------------------------------------------
def generate_forecast(csv_url: str, target: str):
    """
    Auto-detect whether target is:
    YYYY-MM-DD → daily
    YYYY-MM     → monthly
    YYYY        → yearly
    """
    # DAILY
    try:
        if len(target) == 10:  # "YYYY-MM-DD"
            datetime.strptime(target, "%Y-%m-%d")
            return daily_forecast(csv_url, target)
    except:
        pass

    # MONTHLY
    try:
        if len(target) == 7:  # "YYYY-MM"
            datetime.strptime(target, "%Y-%m")
            return monthly_forecast(csv_url, target)
    except:
        pass

    # YEARLY
    try:
        if len(target) == 4:  # "YYYY"
            int(target)
            return yearly_forecast(csv_url, target)
    except:
        pass

    raise ValueError("Invalid target format. Expected YYYY or YYYY-MM or YYYY-MM-DD.")
