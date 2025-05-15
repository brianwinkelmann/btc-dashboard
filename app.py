import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, time as dt_time
from streamlit_autorefresh import st_autorefresh
import pytz

# Configuración de la página
st.set_page_config(page_title="BTC Dashboard", layout="wide")

# Inyectar CSS personalizado
st.markdown(
    '<link rel="stylesheet" href="assets/styles.css">',
    unsafe_allow_html=True
)

# Auto‐refresh cada 20 segundos
st_autorefresh(interval=20_000, key="auto_refresh")

# Zona horaria
tz = pytz.timezone("America/Argentina/Buenos_Aires")

@st.cache_data(ttl=300)
def load_data(path="btc_sample.csv"):
    df = pd.read_csv(path, parse_dates=["Open Time"])
    df["Open Time"] = pd.to_datetime(df["Open Time"], utc=True).dt.tz_convert(tz)
    return df.sort_values("Open Time").reset_index(drop=True)

# Cargar datos
df = load_data()
last_time  = df["Open Time"].iloc[-1]
last_close = df["Close"].iloc[-1]

# Header
st.title("💸 Bitcoin en tiempo real")
st.caption("Actualización automática – datos cada minuto desde Binance")

# Advertencia si no hay historial suficiente
if len(df) < 30 * 24 * 60:
    st.warning("Se recomienda al menos 30 días de historial para un dashboard completo.")

# Mostrar último precio
st.markdown(f"""
<div style="text-align:center;font-size:48px;font-weight:bold;color:#00E5FF;">
  ${last_close:,.2f}
</div>
<div style="text-align:center;font-size:14px;color:gray;margin-bottom:1rem;">
  {last_time.strftime('%Y-%m-%d %H:%M:%S')} (ARG)
</div>
""", unsafe_allow_html=True)

# --- KPIs comparativas en tarjetas ---
def get_idx(minutes):
    return -minutes if len(df) >= minutes else None

idx_map = {
    "1 hora": get_idx(60),
    "24 horas": get_idx(60*24),
    "1 semana": get_idx(60*24*7),
    "1 mes": get_idx(60*24*30),
}

st.subheader("📊 Comparaciones rápidas")
cols = st.columns(4, gap="large")

for (label, idx), col in zip(idx_map.items(), cols):
    past = df["Close"].iloc[idx] if idx else None
    if past is not None:
        diff = last_close - past
        pct  = diff / past * 100
        color = "red" if pct < 0 else "limegreen"
        col.markdown(f"""
          <div class="kpi-card">
            <div style="font-size:1.5rem; color:{color};">{pct:+.2f}%</div>
            <div style="font-size:1rem;   color:{color};">{diff:+.2f} USD</div>
            <div style="font-size:0.8rem; color:gray;">Hace {label}</div>
          </div>
        """, unsafe_allow_html=True)
    else:
        col.markdown('<div class="kpi-card">--</div>', unsafe_allow_html=True)

# --- Selector de rango y calendario ---
st.subheader("🗓 Filtrar rango de fechas")
opt_col, date_col = st.columns([1, 2], gap="small")

with opt_col:
    range_opt = st.radio(
        "",
        ["Últimos 7 d", "Últimos 15 d", "Últimos 30 d", "Personalizado"],
        horizontal=False
    )

default_days = int(range_opt.split()[1]) if range_opt != "Personalizado" else 7
start_default = (last_time - timedelta(days=default_days)).date()
end_default   = last_time.date()

with date_col:
    start_date, end_date = st.date_input(
        "Selecciona un rango",
        value=[start_default, end_default],
        min_value=df["Open Time"].dt.date.min(),
        max_value=last_time.date()
    )

# Convertir fechas a datetime con zona
start_dt = tz.localize(datetime.combine(start_date, dt_time.min))
end_dt   = tz.localize(datetime.combine(end_date,   dt_time.max))

df_filtered = df[(df["Open Time"] >= start_dt) & (df["Open Time"] <= end_dt)]

# --- Gráfico interactivo ---
fig = go.Figure(go.Scatter(
    x=df_filtered["Open Time"],
    y=df_filtered["Close"],
    mode="lines+markers",
    line=dict(color="#00E5FF", width=2),
    marker=dict(size=4)
))
fig.update_layout(
    title=f"BTC/USDT: {start_date} → {end_date}",
    template="plotly_dark",
    margin=dict(l=20, r=20, t=60, b=20),
    xaxis=dict(title="Fecha"),
    yaxis=dict(title="Precio (USD)")
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

# --- Timestamp ---
st.markdown(
    f"<div style='text-align:center;font-size:12px;color:gray;margin-top:1rem;'>"
    f"🕒 Última actualización: {datetime.now(tz):%Y-%m-%d %H:%M:%S} (ARG)</div>",
    unsafe_allow_html=True
)