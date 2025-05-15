import pandas as pd
from datetime import datetime, time
from config import DATA_PATH, TIMEZONE

def load_data() -> pd.DataFrame:
    """Carga el CSV, fuerza tz-aware y ordena."""
    df = pd.read_csv(DATA_PATH, parse_dates=["Open Time"])
    df["Open Time"] = (
        pd.to_datetime(df["Open Time"], utc=True)
          .dt.tz_convert(TIMEZONE)
    )
    return df.sort_values("Open Time").reset_index(drop=True)

def compute_kpis(df: pd.DataFrame, current_time: datetime) -> dict:
    """Devuelve precios pasados para comparaciones rápidas."""
    mins = {"1h":60, "24h":60*24, "7d":60*24*7, "30d":60*24*30}
    last_close = df["Close"].iloc[-1]
    out = {}
    for label, m in mins.items():
        idx = -m if len(df) >= m else None
        past = df["Close"].iloc[idx] if idx else None
        out[label] = {"current": last_close, "past": past}
    return out

def filter_by_date(df: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
    """Filtra df entre start y end (ambos tz-aware)."""
    return df[(df["Open Time"] >= start) & (df["Open Time"] <= end)]