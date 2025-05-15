import streamlit as st
st.set_page_config(page_title="BTC Dashboard", layout="wide")

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Auto-refresh cada 20 s
st_autorefresh(interval=20000, key="auto_refresh")

st.title("💸 Bitcoin en tiempo real")
st.caption("Actualización automática – datos cada minuto desde Binance")

# Leer CSV
try:
    df = pd.read_csv("btc_sample.csv", parse_dates=["Open Time"])
except FileNotFoundError:
    st.error("⚠️ No se encontró 'btc_sample.csv'. Ejecutá primero el script.")
    st.stop()

# Ordenar y reset index
df["Open Time"] = pd.to_datetime(df["Open Time"])
df = df.sort_values("Open Time").reset_index(drop=True)

# Validación mínima (30 días)
if len(df) < 1440 * 30:
    st.warning("No hay suficiente historial (se necesita al menos 30 días).")

# Último precio y hora
last_close = df["Close"].iloc[-1]
last_time  = df["Open Time"].iloc[-1]

# Índices para comparaciones
def get_idx(minutes):
    return -minutes if len(df) >= minutes else None
idx_1h = get_idx(60)
idx_1w = get_idx(60 * 24 * 7)
idx_1m = get_idx(60 * 24 * 30)

# KPI builder
def build_kpi(title, current, past):
    if past is None:
        return f"<div style='text-align:center;color:gray;font-size:14px;'>{title}<br>--</div>"
    diff = current - past
    pct  = diff / past * 100
    color = "red" if pct < 0 else "limegreen"
    return f"""
    <div style="text-align:center; margin-bottom:15px;">
      <div style="font-size:24px; color:{color};">{pct:+.2f}%</div>
      <div style="font-size:16px; color:{color};">{diff:+.2f} USD</div>
      <div style="font-size:14px; color:gray;">Precio entonces: ${past:.2f}</div>
      <div style="font-size:14px; color:gray;">{title}</div>
    </div>
    """

# Mostrar último precio, hora y etiqueta
st.markdown(f"""
<div style="text-align:center;font-size:52px;font-weight:bold;color:white;">
  ${last_close:,.2f}
</div>
<div style="text-align:center;font-size:18px;color:gray;">
  {last_time.strftime('%Y-%m-%d %H:%M:%S')}
</div>
<div style="text-align:center;font-size:16px;color:gray;margin-bottom:40px;">
  Último precio BTC/USDT
</div>
""", unsafe_allow_html=True)

# KPIs comparativas
st.subheader("📊 Comparaciones")
cols = st.columns(3)
cols[0].markdown(build_kpi("Hace 1 hora",   last_close,
                          df["Close"].iloc[idx_1h] if idx_1h else None), unsafe_allow_html=True)
cols[1].markdown(build_kpi("Hace 1 semana", last_close,
                          df["Close"].iloc[idx_1w] if idx_1w else None), unsafe_allow_html=True)
cols[2].markdown(build_kpi("Hace 1 mes",    last_close,
                          df["Close"].iloc[idx_1m] if idx_1m else None), unsafe_allow_html=True)

# Gráfico
fig = go.Figure(go.Scatter(
    x=df["Open Time"], y=df["Close"], mode="lines+markers",
    line=dict(color="cyan", width=2), marker=dict(size=4)
))
fig.update_layout(
    title="Evolución del precio de BTC",
    xaxis_title="Fecha y hora (Argentina)",
    yaxis_title="Precio (USD)",
    template="plotly_dark", showlegend=False,
    height=800, margin=dict(l=20, r=20, t=60, b=40), dragmode=False
)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# Timestamp actualización
st.markdown(
    f"<div style='text-align:center;font-size:14px;color:gray;'>🕒 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>",
    unsafe_allow_html=True
)
