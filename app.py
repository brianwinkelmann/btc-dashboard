import pathlib
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, time as dt_time
from dateutil.relativedelta import relativedelta
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu
import pytz

# ------------------------------------------------
# 1. Configuración inicial (debe ir justo después de imports)
# ------------------------------------------------
st.set_page_config(page_title="BTC Dashboard", layout="wide")

# ------------------------------------------------
# 2. Inyectar CSS externo
# ------------------------------------------------
css_path = pathlib.Path("assets/styles.css")
st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ------------------------------------------------
# 3. Auto‐refresh y timezone
# ------------------------------------------------
st_autorefresh(interval=20_000, key="auto_refresh")
TZ = pytz.timezone("America/Argentina/Buenos_Aires")

# ------------------------------------------------
# 4. Carga de datos
# ------------------------------------------------
@st.cache_data(ttl=300)
def load_data(path="btc_sample.csv"):
    df = pd.read_csv(path, parse_dates=["Open Time"])
    df["Open Time"] = pd.to_datetime(df["Open Time"], utc=True).dt.tz_convert(TZ)
    return df.sort_values("Open Time").reset_index(drop=True)

df = load_data()
last_time  = df["Open Time"].iloc[-1]
last_close = df["Close"].iloc[-1]

# ------------------------------------------------
# 5. Menú hamburguesa en header
# ------------------------------------------------
selected = option_menu(
    menu_title=None,
    options=["Inicio", "Sobre nosotros"],
    icons=["house", "info-circle"],
    menu_icon="list",         # icono hamburguesa
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0 !important", "background-color": "transparent"},
        "nav-link": {
            "border": "1px solid #C9D1D9",
            "border-radius": "0.5rem",
            "padding": "0.5rem 1rem",
            "margin": "0 0.5rem",
            "color": "#C9D1D9",
            "font-size": "1rem"
        },
        "nav-link-selected": {
            "background-color": "#00E5FF",
            "color": "#0A0E1A",
            "border": "1px solid #00E5FF"
        }
    }
)

# ------------------------------------------------
# 6. Página "Sobre nosotros"
# ------------------------------------------------
if selected == "Sobre nosotros":
    st.header("🛠️ Avauras - Sobre nosotros")
    st.write("""
        **Avauras** es una plataforma dedicada a ofrecer información en tiempo real de Bitcoin  
        y otros servicios financieros. Nuestro equipo fusiona experiencia en datos,  
        desarrollo de software y diseño UX para crear interfaces limpias, atractivas  
        y fáciles de usar.
    """)
    st.write("---")
    st.write("📧 contacto@avauras.com")
    st.stop()

# ------------------------------------------------
# 7. Página "Inicio"
# ------------------------------------------------
st.header("💸 Bitcoin en tiempo real")
st.caption("Actualización automática – datos cada minuto desde Binance")

if len(df) < 30 * 24 * 60:
    st.warning("Se recomienda al menos 30 días de historial para un dashboard completo.")

# 7.1 Último precio
st.markdown(f"""
<div style="text-align:center;font-size:48px;font-weight:bold;color:#00E5FF;">
  ${last_close:,.2f}
</div>
<div style="text-align:center;font-size:14px;color:gray;margin-bottom:1rem;">
  {last_time.strftime('%Y-%m-%d %H:%M:%S')} (ARG)
</div>
""", unsafe_allow_html=True)

# 7.2 KPIs comparativas
st.subheader("📊 Comparaciones rápidas")
cols    = st.columns(4, gap="large")
periods = [("1 hora", 60), ("24 horas", 1440), ("1 semana", 10080), ("1 mes", 43200)]

for i, (label, mins) in enumerate(periods):
    col = cols[i]
    if len(df) >= mins:
        past_val  = df["Close"].iloc[-mins]
        past_time = df["Open Time"].iloc[-mins]
        diff      = last_close - past_val
        pct       = diff / past_val * 100
        color     = "red" if pct < 0 else "limegreen"
        col.markdown(f"""
          <div class="kpi-card">
            <div style="font-size:1rem;font-weight:bold;color:#C9D1D9;margin-bottom:0.5rem;">
              Comparación hace {label}
            </div>
            <div style="font-size:1.5rem;color:{color};">{pct:+.2f}%</div>
            <div style="font-size:1rem;color:{color};margin-bottom:0.5rem;">{diff:+.2f} USD</div>
            <div style="font-size:0.8rem;color:gray;">
              Precio en {past_time.strftime('%Y-%m-%d %H:%M')}
            </div>
          </div>
        """, unsafe_allow_html=True)
    else:
        col.markdown('<div class="kpi-card">--</div>', unsafe_allow_html=True)

# 7.3 Tabla de estadísticas (últimos 12 meses)
st.subheader("📈 Estadísticas clave (últimos 12 meses)")
es_months = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
stats = {}
for i in range(12):
    m_dt  = last_time - relativedelta(months=i)
    y, m  = m_dt.year, m_dt.month
    label = f"{es_months[m-1]} {y}"
    start = m_dt.replace(day=1, hour=0, minute=0, second=0)
    end   = (start + relativedelta(months=1)) - timedelta(seconds=1)
    series = df[(df["Open Time"] >= start) & (df["Open Time"] <= end)]["Close"]
    if not series.empty:
        stats[label] = {
            "Máximo":    series.max(),
            "Mínimo":    series.min(),
            "Promedio":  series.mean(),
            "Desv. est.":series.std()
        }
stats_df = pd.DataFrame(stats).T.round(2).applymap(lambda x: f"${x:,.2f}")
st.table(stats_df)

# 7.4 Selector de rango y gráfico
st.subheader("🗓 Filtrar rango de fechas")
opt_col, date_col = st.columns([1,2], gap="small")

with opt_col:
    range_opt = st.radio("", ["Últimos 7 d","Últimos 15 d","Últimos 30 d","Personalizado"])
days      = int(range_opt.split()[1]) if range_opt != "Personalizado" else 7

start_def = (last_time - timedelta(days=days)).date()
end_def   = last_time.date()

with date_col:
    start_date, end_date = st.date_input(
        "Selecciona un rango",
        value=[start_def, end_def],
        min_value=df["Open Time"].dt.date.min(),
        max_value=last_time.date()
    )

start_dt = TZ.localize(datetime.combine(start_date, dt_time.min))
end_dt   = TZ.localize(datetime.combine(end_date,   dt_time.max))
df_f     = df[(df["Open Time"] >= start_dt) & (df["Open Time"] <= end_dt)]

fig = go.Figure(go.Scatter(
    x=df_f["Open Time"], y=df_f["Close"],
    mode="lines+markers",
    line=dict(color="#00E5FF", width=2),
    marker=dict(size=4)
))
fig.update_layout(
    title=f"BTC/USDT: {start_date} → {end_date}",
    template="plotly_dark",
    margin=dict(l=20, r=20, t=60, b=20),
    xaxis_title="Fecha",
    yaxis_title="Precio (USD)"
)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

# 7.5 Timestamp
st.markdown(f"""
<div style="text-align:center;font-size:12px;color:gray;margin-top:1rem;">
  🕒 Última actualización: {datetime.now(TZ):%Y-%m-%d %H:%M:%S} (ARG)
</div>
""", unsafe_allow_html=True)