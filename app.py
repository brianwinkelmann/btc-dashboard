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
st.set_page_config(page_title="Crypto Dashboard", layout="wide")

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
TZ = pytz.timezone("America/Argentina/Buenos_Aires")

# ------------------------------------------------
# 4. Selección de moneda y configuración avanzada
# ------------------------------------------------
st.sidebar.title("⚙️ Configuración")

# Selección de moneda
selected_symbol = st.sidebar.selectbox(
    "Selecciona la moneda",
    ["BTCUSDT", "ETHUSDT", "USDTARS"],
    format_func=lambda x: {"BTCUSDT": "Bitcoin (BTC)", "ETHUSDT": "Ethereum (ETH)", "USDTARS": "USDT/ARS"}[x]
)

# Configuración avanzada
st.sidebar.markdown("### Configuración avanzada")
enable_autorefresh = st.sidebar.checkbox("Habilitar auto-actualización", value=True)
refresh_interval = st.sidebar.slider("Intervalo de actualización (segundos)", min_value=10, max_value=120, value=20, step=5)

# Guardar configuración en session_state
st.session_state["enable_autorefresh"] = enable_autorefresh
st.session_state["refresh_interval"] = refresh_interval

# Aplicar configuración de auto-refresh
if enable_autorefresh:
    st_autorefresh(interval=refresh_interval * 1000, key="auto_refresh")

# Archivo CSV basado en la moneda seleccionada
csv_file = f"{selected_symbol.lower()}_historical.csv"

# ------------------------------------------------
# 5. Carga de datos optimizada y cacheada por moneda
# ------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def load_data(symbol):
    """Cargar datos desde el archivo CSV correspondiente a la moneda seleccionada."""
    path = f"{symbol.lower()}_historical.csv"
    try:
        # Cargar solo las columnas necesarias
        df = pd.read_csv(path, usecols=["Open Time", "Close"], parse_dates=["Open Time"])
        df["Open Time"] = pd.to_datetime(df["Open Time"], utc=True).dt.tz_convert(TZ)
        return df.sort_values("Open Time").reset_index(drop=True)
    except FileNotFoundError:
        st.error(f"El archivo {path} no se encontró. Verifica que exista y contenga datos válidos.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()

# ------------------------------------------------
# 7. Funciones auxiliares optimizadas
# ------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def get_filtered_data(df, start_date, end_date):
    """Filtrar los datos según el rango seleccionado."""
    start_dt = TZ.localize(datetime.combine(start_date, dt_time.min))
    end_dt = TZ.localize(datetime.combine(end_date, dt_time.max))
    filtered = df[(df["Open Time"] >= start_dt) & (df["Open Time"] <= end_dt)]
    return filtered

# ------------------------------------------------
# 8. Lógica principal para manejar el cambio de moneda
# ------------------------------------------------
# Cargar datos para la moneda seleccionada
df = load_data(selected_symbol)

# Validar si el archivo CSV contiene datos
if df.empty:
    st.error(f"No hay datos disponibles para {selected_symbol}. Verifica que el archivo contenga datos válidos.")
    st.stop()

# Actualizar valores dependientes de la moneda seleccionada
last_time = df["Open Time"].iloc[-1]
last_close = df["Close"].iloc[-1]

# Inicializar rango de fechas y datos filtrados
if "start_date" not in st.session_state or st.session_state.last_symbol != selected_symbol:
    st.session_state.start_date = (last_time - timedelta(days=7)).date()
    st.session_state.end_date = last_time.date()
    st.session_state.last_symbol = selected_symbol

# Filtrar los datos según el rango seleccionado
filtered_data = get_filtered_data(df, st.session_state.start_date, st.session_state.end_date)

# Validar si los datos filtrados están vacíos
if filtered_data.empty:
    st.warning(f"No hay datos disponibles para {selected_symbol} en el rango seleccionado.")
    st.stop()

# ------------------------------------------------
# 9. Generar el gráfico
# ------------------------------------------------
def generate_chart(filtered_data, start_date, end_date):
    """Generar el gráfico de precios con línea de promedio."""
    avg_price = filtered_data["Close"].mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=filtered_data["Open Time"],
        y=filtered_data["Close"],
        mode="lines+markers",
        name="Precio",
        line=dict(color="#00E5FF", width=2),
        marker=dict(size=4)
    ))
    fig.add_trace(go.Scatter(
        x=filtered_data["Open Time"],
        y=[avg_price] * len(filtered_data),
        mode="lines",
        name="Promedio",
        line=dict(color="orange", dash="dash", width=2)
    ))
    fig.update_layout(
        title=f"{selected_symbol}: {start_date} → {end_date}",
        template="plotly_dark",
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis_title="Fecha",
        yaxis_title="Precio",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified",
        plot_bgcolor="#1E1E1E",
        paper_bgcolor="#121212",
        font=dict(color="#C9D1D9")
    )
    return fig

# Generar y mostrar el gráfico
fig = generate_chart(filtered_data, st.session_state.start_date, st.session_state.end_date)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

# ------------------------------------------------
# 10. Mostrar información adicional
# ------------------------------------------------
st.markdown(f"""
<div style="text-align:center;font-size:48px;font-weight:bold;color:#00E5FF;">
  ${last_close:,.2f}
</div>
<div style="text-align:center;font-size:14px;color:gray;margin-bottom:1rem;">
  {last_time.strftime('%Y-%m-%d %H:%M:%S')} (ARG)
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 11. Comparaciones rápidas
# ------------------------------------------------
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

# ------------------------------------------------
# 12. Tabla de estadísticas (últimos 12 meses)
# ------------------------------------------------
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
            "Desv. est.": series.std(),
        }
stats_df = pd.DataFrame(stats).T.round(2).applymap(lambda x: f"${x:,.2f}")
st.table(stats_df)

# ------------------------------------------------
# 13. Selector de rango y gráfico
# ------------------------------------------------
st.subheader("🗓 Filtrar rango de fechas")
st.markdown("Selecciona un rango predefinido o selecciona un rango personalizado para explorar los datos.")
range_option = st.radio(
    "Selecciona un rango",
    ["Últimos 7 días", "Últimos 30 días", "Últimos 6 meses", "Últimos 12 meses", "Personalizado"]
)

if range_option == "Últimos 7 días":
    st.session_state.start_date = (last_time - timedelta(days=7)).date()
    st.session_state.end_date = last_time.date()
elif range_option == "Últimos 30 días":
    st.session_state.start_date = (last_time - timedelta(days=30)).date()
    st.session_state.end_date = last_time.date()
elif range_option == "Últimos 6 meses":
    st.session_state.start_date = (last_time - relativedelta(months=6)).date()
    st.session_state.end_date = last_time.date()
elif range_option == "Últimos 12 meses":
    st.session_state.start_date = (last_time - relativedelta(months=12)).date()
    st.session_state.end_date = last_time.date()
elif range_option == "Personalizado":
    st.session_state.start_date, st.session_state.end_date = st.date_input(
        "Selecciona un rango",
        value=[st.session_state.start_date, st.session_state.end_date],
        min_value=df["Open Time"].dt.date.min(),
        max_value=last_time.date()
    )

# Validar rango de fechas
if st.session_state.start_date > st.session_state.end_date:
    st.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
    st.stop()

# Actualizar datos filtrados
st.session_state.filtered_data = get_filtered_data(df, st.session_state.start_date, st.session_state.end_date)

# Actualizar el gráfico al cambiar de moneda o rango
st.markdown(f"### Rango seleccionado: {st.session_state.start_date} → {st.session_state.end_date}")

if st.session_state.filtered_data.empty:
    st.warning(f"No hay datos disponibles para {selected_symbol} en el rango seleccionado.")
else:
    # Regenerar el gráfico con los datos actualizados
    fig = generate_chart(st.session_state.filtered_data, st.session_state.start_date, st.session_state.end_date)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

# ------------------------------------------------
# 14. Timestamp
# ------------------------------------------------
st.markdown(f"""
<div style="text-align:center;font-size:12px;color:gray;margin-top:1rem;">
  🕒 Última actualización: {datetime.now(TZ):%Y-%m-%d %H:%M:%S} (ARG)
</div>
""", unsafe_allow_html=True)