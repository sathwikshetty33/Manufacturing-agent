# custom_tools/dynamic_scheduling_agent/tasks.py
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import uuid
from typing import Union, Dict, List

# -----------------------
# Helpers
# -----------------------
def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def _save_artifact(df: pd.DataFrame, prefix="schedule"):
    _ensure_dir("/tmp/dynamic_scheduling")
    fname = f"/tmp/dynamic_scheduling/{prefix}_{uuid.uuid4().hex}.csv"
    df.to_csv(fname, index=False)
    return fname

def _normalize_demand_series(demand_input: Union[str, Dict, List], start_date: str, end_date: str) -> pd.Series:
    """
    Accepts:
      - JSON-like dict: {"2025-11-20": 500, ...}
      - List of {"date": "...", "demand": ...}
      - CSV URL (string starting with http or local path)
    Returns a pandas Series indexed by daily dates between start_date & end_date.
    """
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    days = pd.date_range(start_dt, end_dt, freq='D')

    # Case: dict or JSON string parseable to dict
    if isinstance(demand_input, dict):
        series = pd.Series({pd.to_datetime(k): float(v) for k, v in demand_input.items()})
    elif isinstance(demand_input, list):
        series = pd.Series({pd.to_datetime(item['date']): float(item['demand']) for item in demand_input})
    elif isinstance(demand_input, str):
        # If looks like a URL or path, attempt to load CSV with columns date,demand
        if demand_input.lower().startswith("http") or os.path.exists(demand_input):
            df = pd.read_csv(demand_input)
            cols = [c.lower() for c in df.columns]
            date_col = next((c for c in cols if 'date' in c), None)
            val_col = next((c for c in cols if any(k in c for k in ('demand','value','qty','quantity'))), None)
            if date_col is None or val_col is None:
                raise ValueError("CSV must contain date and demand/value columns")
            df.columns = cols
            df['date'] = pd.to_datetime(df[date_col])
            df = df.set_index('date')
            series = df[val_col].resample('D').sum()
        else:
            # try parse JSON string
            try:
                parsed = json.loads(demand_input)
                return _normalize_demand_series(parsed, start_date, end_date)
            except Exception as e:
                raise ValueError("Unsupported demand_series string input") from e
    else:
        raise ValueError("Unsupported demand input type")

    # Reindex to requested days (fill missing with 0)
    series = series.reindex(days, fill_value=0).astype(float)
    series.index = pd.to_datetime(series.index)
    return series

# -----------------------
# Core single-day scheduler
# -----------------------
def generate_schedule_single_day(date: str, demand: float, machines: int = 5, throughput_per_machine: int = 100, labor_per_shift: int = 5):
    """
    Schedule for a single date using an explicit demand value.
    Returns artifact path and summary.
    """
    dt = pd.to_datetime(date)
    required = float(demand)
    capacity = machines * throughput_per_machine

    machines_needed = int(np.ceil(required / throughput_per_machine)) if required > 0 else 0
    machines_running = min(machines_needed, machines)
    output = machines_running * throughput_per_machine
    fulfilled = min(output, required)
    backlog_end = max(0.0, required - fulfilled)
    operators_required = machines_running * labor_per_shift

    df = pd.DataFrame([{
        "date": dt.strftime("%Y-%m-%d"),
        "demand": required,
        "machines_running": machines_running,
        "capacity_today": int(output),
        "fulfilled_today": float(fulfilled),
        "backlog_end": float(backlog_end),
        "operators_required": int(operators_required),
        "materials_required": float(fulfilled)
    }])

    artifact = _save_artifact(df, prefix="schedule_single")
    summary = {
        "date": dt.strftime("%Y-%m-%d"),
        "demand": float(demand),
        "machines_running": int(machines_running),
        "fulfilled": float(fulfilled),
        "backlog_end": float(backlog_end),
        "operators_required": int(operators_required),
        "artifact": artifact
    }

    return {"schedule_artifact": artifact, "summary": summary, "status": "success"}

# -----------------------
# Core multi-day scheduler (accepts demand_map or CSV URL)
# -----------------------
def generate_schedule_multi_day(demand_series: Union[str, Dict, List], start_date: str, end_date: str, machines: int = 5, throughput_per_machine: int = 100, labor_per_shift: int = 5):
    """
    demand_series may be:
      - a JSON dict {"YYYY-MM-DD": demand, ...}
      - a list [{"date":"YYYY-MM-DD","demand":123}, ...]
      - a CSV URL or local path to a CSV with date,demand columns
    """
    series = _normalize_demand_series(demand_series, start_date, end_date)
    schedule_rows = []
    backlog = 0.0

    for day, demand in series.items():
        required = float(demand) + backlog
        capacity = machines * throughput_per_machine
        machines_needed = int(np.ceil(required / throughput_per_machine)) if required > 0 else 0
        machines_running = min(machines_needed, machines)
        output = machines_running * throughput_per_machine
        fulfilled = min(output, required)
        backlog = max(0.0, required - fulfilled)
        operators_required = machines_running * labor_per_shift

        schedule_rows.append({
            "date": day.strftime("%Y-%m-%d"),
            "demand": float(demand),
            "machines_running": machines_running,
            "capacity_today": int(output),
            "fulfilled_today": float(fulfilled),
            "backlog_end": float(backlog),
            "operators_required": int(operators_required),
            "materials_required": float(fulfilled)
        })

    schedule_df = pd.DataFrame(schedule_rows)
    artifact = _save_artifact(schedule_df, prefix="schedule_multi")
    summary = {
        "start_date": start_date,
        "end_date": end_date,
        "total_demand": float(schedule_df['demand'].sum()),
        "total_planned_output": float(schedule_df['fulfilled_today'].sum()),
        "peak_machines": int(schedule_df['machines_running'].max()),
        "avg_operators_per_day": float(schedule_df['operators_required'].mean()),
        "artifact": artifact
    }
    return {"schedule_artifact": artifact, "summary": summary, "status": "success"}

# -----------------------
# Convenience: schedule directly from CSV URL
# -----------------------
def generate_schedule_from_csv(csv_url: str, start_date: str, end_date: str, machines: int = 5, throughput_per_machine: int = 100, labor_per_shift: int = 5):
    return generate_schedule_multi_day(csv_url, start_date, end_date, machines, throughput_per_machine, labor_per_shift)
