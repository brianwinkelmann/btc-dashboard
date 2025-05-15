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
# 1. Configuración inicial
# ------------------------------------------------
st.set_page_config(page_title="BTC Dashboard", layout="wide")

# ------------------------------------------------
# 2. Inyectar CSS externo
# ------------------------------------------------
css_path = pathlib.Path("assets/styles.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
else:
    st.warning("El archivo de estilos CSS no se encontró. Verifica la ruta.")

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
    try:
        df = pd.read_csv(path, parse_dates=["Open Time"])
        df["Open Time"] = pd.to_datetime(df["Open Time"], utc=True).dt.tz_convert(TZ)
        return df.sort_values("Open Time").reset_index(drop=True)
    except FileNotFoundError:
        st.error(f"El archivo {path} no se encontró. Verifica la ruta.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.stop()

last_time = df["Open Time"].iloc[-1]
last_close = df["Close"].iloc[-1]

# ------------------------------------------------
# 5. Inicializar valores en st.session_state
# ------------------------------------------------
if "selected_range" not in st.session_state:
    st.session_state.selected_range = "Últimos 7 días"
if "start_date" not in st.session_state:
    st.session_state.start_date = (last_time - timedelta(days=7)).date()
if "end_date" not in st.session_state:
    st.session_state.end_date = last_time.date()
if "filtered_data" not in st.session_state:
    st.session_state.filtered_data = df[(df["Open Time"] >= TZ.localize(datetime.combine(st.session_state.start_date, dt_time.min))) &
                                         (df["Open Time"] <= TZ.localize(datetime.combine(st.session_state.end_date, dt_time.max)))]

# ------------------------------------------------
# 6. Funciones auxiliares
# ------------------------------------------------
def get_filtered_data(start_date, end_date):
    """Filtrar los datos según el rango seleccionado."""
    start_dt = TZ.localize(datetime.combine(start_date, dt_time.min))
    end_dt = TZ.localize(datetime.combine(end_date, dt_time.max))
    return df[(df["Open Time"] >= start_dt) & (df["Open Time"] <= end_dt)]

def generate_chart(filtered_data, start_date, end_date):
    """Generar el gráfico de precios."""
    fig = go.Figure(go.Scatter(
        x=filtered_data["Open Time"], y=filtered_data["Close"],
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
    return fig

# ------------------------------------------------
# 7. Menú hamburguesa en header
# ------------------------------------------------
selected = option_menu(
    menu_title=None,
    options=["Inicio", "Sobre nosotros"],
    icons=["house", "info-circle"],
    menu_icon="list",  # Icono hamburguesa
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
# 8. Página "Sobre nosotros"
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
# 9. Página "Inicio"
# ------------------------------------------------
st.header("💸 Bitcoin en tiempo real")
st.caption("Actualización automática – datos cada minuto desde Binance")

if len(df) < 30 * 24 * 60:
    st.warning("Se recomienda al menos 30 días de historial para un dashboard completo.")

# 9.1 Último precio
st.markdown(f"""
<div style="text-align:center;font-size:48px;font-weight:bold;color:#00E5FF;">
  ${last_close:,.2f}
</div>
<div style="text-align:center;font-size:14px;color:gray;margin-bottom:1rem;">
  {last_time.strftime('%Y-%m-%d %H:%M:%S')} (ARG)
</div>
""", unsafe_allow_html=True)

# 9.2 Comparaciones rápidas
st.subheader("📊 Comparaciones rápidas")
cols = st.columns(4, gap="large")
periods = [("1 hora", 60), ("24 horas", 1440), ("1 semana", 10080), ("1 mes", 43200)]

for i, (label, mins) in enumerate(periods):
    col = cols[i]
    if len(df) >= mins:
        past_val = df["Close"].iloc[-mins]
        past_time = df["Open Time"].iloc[-mins]
        diff = last_close - past_val
        pct = diff / past_val * 100
        color = "red" if pct < 0 else "limegreen"
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

# 9.3 Tabla de estadísticas (últimos 12 meses)
st.subheader("📈 Estadísticas clave (últimos 12 meses)")
es_months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
stats = {}
for i in range(12):
    m_dt = last_time - relativedelta(months=i)
    y, m = m_dt.year, m_dt.month
    label = f"{es_months[m-1]} {y}"
    start = m_dt.replace(day=1, hour=0, minute=0, second=0)
    end = (start + relativedelta(months=1)) - timedelta(seconds=1)
    series = df[(df["Open Time"] >= start) & (df["Open Time"] <= end)]["Close"]
    if not series.empty:
        stats[label] = {
            "Máximo": series.max(),
            "Mínimo": series.min(),
            "Promedio": series.mean(),
            "Desv. est.": series.std()
        }
stats_df = pd.DataFrame(stats).T.round(2).applymap(lambda x: f"${x:,.2f}")
st.table(stats_df)

# 9.4 Selector de rango y gráfico
st.subheader("🗓 Filtrar rango de fechas")

# Botones rápidos para rangos predefinidos
st.markdown("### Selecciona un rango rápido:")
col1, col2, col3, col4 = st.columns(4)

# Botones con lógica para actualizar el estado seleccionado
with col1:
    if st.button("Últimos 7 días", key="btn_7d"):
        st.session_state.selected_range = "Últimos 7 días"
        st.session_state.start_date = (last_time - timedelta(days=7)).date()
        st.session_state.end_date = last_time.date()
        st.session_state.filtered_data = get_filtered_data(st.session_state.start_date, st.session_state.end_date)
with col2:
    if st.button("Últimos 15 días", key="btn_15d"):
        st.session_state.selected_range = "Últimos 15 días"
        st.session_state.start_date = (last_time - timedelta(days=15)).date()
        st.session_state.end_date = last_time.date()
        st.session_state.filtered_data = get_filtered_data(st.session_state.start_date, st.session_state.end_date)
with col3:
    if st.button("Últimos 30 días", key="btn_30d"):
        st.session_state.selected_range = "Últimos 30 días"
        st.session_state.start_date = (last_time - timedelta(days=30)).date()
        st.session_state.end_date = last_time.date()
        st.session_state.filtered_data = get_filtered_data(st.session_state.start_date, st.session_state.end_date)
with col4:
    if st.button("Personalizado", key="btn_custom"):
        st.session_state.selected_range = "Personalizado"
        st.session_state.start_date, st.session_state.end_date = st.date_input(
            "Selecciona un rango",
            value=[st.session_state.start_date, st.session_state.end_date],
            min_value=df["Open Time"].dt.date.min(),
            max_value=last_time.date()
        )
        st.session_state.filtered_data = get_filtered_data(st.session_state.start_date, st.session_state.end_date)

# Validación del rango de fechas
if st.session_state.start_date > st.session_state.end_date:
    st.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
    st.stop()

# Mostrar el rango seleccionado
st.markdown(f"### Rango seleccionado: {st.session_state.start_date} → {st.session_state.end_date}")

# Mostrar advertencia si no hay datos
if st.session_state.filtered_data.empty:
    st.warning("No hay datos disponibles para el rango seleccionado.")
else:
    # Generar y mostrar el gráfico
    fig = generate_chart(st.session_state.filtered_data, st.session_state.start_date, st.session_state.end_date)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

# 9.5 Timestamp
st.markdown(f"""
<div style="text-align:center;font-size:12px;color:gray;margin-top:1rem;">
  🕒 Última actualización: {datetime.now(TZ):%Y-%m-%d %H:%M:%S} (ARG)
</div>
""", unsafe_allow_html=True)