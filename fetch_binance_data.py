# import os
# import time
# import pandas as pd
# from binance.client import Client
# from datetime import datetime, timedelta, timezone

# # API keys (dejar en blanco si es solo lectura pública)
# api_key = ""
# api_secret = ""

# # Parámetros
# symbols = ["BTCUSDT", "ETHUSDT", "USDTARS"]  # Monedas a descargar
# interval = Client.KLINE_INTERVAL_1MINUTE
# start_days_ago = 370  # Últimos 370 días
# limit = 1000  # Máximo permitido por Binance

# # Inicializar cliente
# client = Client(api_key, api_secret)

# # Función para descargar datos históricos
# def fetch_historical_data(symbol, start_days_ago, interval, limit):
#     print(f"⏳ Descargando datos históricos para {symbol}...")
    
#     # Calcular fechas
#     end_time = datetime.now(timezone.utc)  # Usar timezone-aware UTC
#     start_time = end_time - timedelta(days=start_days_ago)
    
#     # Acumulador
#     all_klines = []
    
#     # Loop para paginar
#     while start_time < end_time:
#         klines = client.get_historical_klines(
#             symbol=symbol,
#             interval=interval,
#             start_str=start_time.isoformat(),
#             limit=limit
#         )
        
#         if not klines:
#             break
        
#         all_klines.extend(klines)
        
#         # Obtener el tiempo de la última vela y avanzar un minuto
#         last_open_time = klines[-1][0]
#         start_time = datetime.fromtimestamp(last_open_time / 1000.0, tz=timezone.utc) + timedelta(minutes=1)
        
#         # Esperar un poco para evitar rate limit
#         time.sleep(0.3)
    
#     # Crear DataFrame
#     df = pd.DataFrame(all_klines, columns=[
#         "Open Time", "Open", "High", "Low", "Close", "Volume", "Close Time", 
#         "Quote Asset Volume", "Number of Trades", "Taker Buy Base Vol", 
#         "Taker Buy Quote Vol", "Ignore"
#     ])
    
#     # Convertir tipos
#     numeric_columns = ["Open", "High", "Low", "Close", "Volume"]
#     df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
    
#     # Timestamp
#     df["Open Time"] = pd.to_datetime(df["Open Time"], unit="ms", utc=True)
#     df["Open Time"] = df["Open Time"].dt.tz_convert("America/Argentina/Buenos_Aires")
    
#     # Selección de columnas clave
#     df = df[["Open Time", "Open", "High", "Low", "Close", "Volume"]]
#     df = df.sort_values("Open Time", ascending=False)
    
#     # Guardar CSV
#     csv_file = f"{symbol.lower()}_historical.csv"
#     df.to_csv(csv_file, index=False)
#     print(f"✅ Archivo {csv_file} generado con datos históricos de {symbol}")

# # Descargar datos para cada moneda
# for symbol in symbols:
#     fetch_historical_data(symbol, start_days_ago, interval, limit)







import os
import time
import pandas as pd
import pytz
from binance.client import Client
from datetime import datetime, timedelta, timezone

# Configuración
api_key = os.getenv("BINANCE_API_KEY", "")
api_secret = os.getenv("BINANCE_API_SECRET", "")
symbols = ["BTCUSDT", "ETHUSDT", "USDTARS"]  # Monedas a descargar
interval = Client.KLINE_INTERVAL_1MINUTE
limit = 1000
tz = pytz.timezone("America/Argentina/Buenos_Aires")

# Cliente Binance
client = Client(api_key, api_secret)

# Fechas UTC y local — rolling window de 3 días
now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
cutoff_utc = now_utc - timedelta(days=3)  # ← Cambiado a 3 días
cutoff_local = cutoff_utc.astimezone(tz)

print(f"🚀 Iniciando actualización – corte en {cutoff_local.strftime('%Y-%m-%d %H:%M')} (hora local)")

# Función para descargar y procesar datos de una moneda
def fetch_and_save_data(symbol):
    print(f"🔄 Procesando {symbol}...")
    csv_file = f"{symbol.lower()}_historical.csv"

    # Descargar velas nuevas (desde cutoff_utc hasta ahora)
    klines = []
    start = cutoff_utc
    while start < now_utc:
        try:
            batch = client.get_historical_klines(symbol, interval, start.isoformat(), limit=limit)
        except Exception as e:
            print(f"⚠️ Error al descargar klines para {symbol}: {e}")
            break

        if not batch:
            break

        klines += batch
        # Usamos la última vela completa
        last_ms = batch[-1][0]
        start = datetime.fromtimestamp(last_ms / 1000, tz=timezone.utc) + timedelta(minutes=1)
        time.sleep(0.3)

    print(f"✅ Descargadas {len(klines)} velas nuevas para {symbol}")

    # Crear DataFrame nuevo
    new = pd.DataFrame(klines, columns=[
        "Open Time", "Open", "High", "Low", "Close", "Volume",
        "Close Time", "Quote Asset Volume", "Number of Trades",
        "Taker Buy Base Vol", "Taker Buy Quote Vol", "Ignore"
    ])[["Open Time", "Open", "High", "Low", "Close", "Volume"]]

    # Convertir timestamp y filtrar futuros
    new["Open Time"] = pd.to_datetime(new["Open Time"], unit="ms", utc=True)
    new = new[new["Open Time"] <= pd.Timestamp.now(timezone.utc)]
    new["Open Time"] = new["Open Time"].dt.tz_convert(tz)
    new[["Open", "High", "Low", "Close", "Volume"]] = new[["Open", "High", "Low", "Close", "Volume"]].apply(pd.to_numeric)

    print(f"🔄 Nuevo DataFrame para {symbol} tiene {len(new)} filas")

    # Leer CSV existente y purgar últimos 3 días
    if os.path.exists(csv_file):
        print(f"📂 Cargando {csv_file}")
        old = pd.read_csv(csv_file, parse_dates=["Open Time"])
        old["Open Time"] = pd.to_datetime(old["Open Time"], utc=True).dt.tz_convert(tz)
        print(f"📈 Datos previos antes del delete: {len(old)} filas")
        old = old[old["Open Time"] < cutoff_local]
        print(f"❌ Filas eliminadas; quedan {len(old)} filas antiguas")
    else:
        print(f"⚠️ No existe CSV para {symbol}; creando uno nuevo")
        old = pd.DataFrame(columns=new.columns)

    # Concatenar, eliminar duplicados y ordenar
    print(f"➕ Insertando {len(new)} filas nuevas para {symbol}")
    out = pd.concat([old, new], ignore_index=True)
    out = out.drop_duplicates(subset="Open Time")
    out = out.sort_values("Open Time", ascending=False)

    # Guardar CSV actualizado
    out.to_csv(csv_file, index=False)
    print(f"🎉 Actualización completa: {len(out)} filas totales en {csv_file}")

# Descargar datos para cada moneda
for symbol in symbols:
    fetch_and_save_data(symbol)