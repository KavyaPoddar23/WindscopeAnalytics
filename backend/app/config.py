from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"