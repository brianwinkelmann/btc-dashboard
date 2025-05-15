import pytz
from pathlib import Path

# Ruta al CSV de datos
DATA_PATH = Path(__file__).parent / "btc_sample.csv"

# Timezone para todo
TIMEZONE = pytz.timezone("America/Argentina/Buenos_Aires")

# Dashboard defaults
MIN_HISTORY_DAYS = 30
CACHE_TTL = 300  # segundos