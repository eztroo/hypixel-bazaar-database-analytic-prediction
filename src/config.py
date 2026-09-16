"""
Konfigurasi pusat untuk seluruh project.
Semua modul di phase berikutnya (Phase 1 dst) mengambil setting dari sini,
supaya tidak ada hardcode path/URL/key tersebar di banyak file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Root folder project (2 level di atas file ini: src/config.py -> project root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env dari root project
load_dotenv(BASE_DIR / ".env")

# --- API ---
HYPIXEL_API_KEY = os.getenv("HYPIXEL_API_KEY", "")
HYPIXEL_BASE_URL = "https://api.hypixel.net"
BAZAAR_ENDPOINT = f"{HYPIXEL_BASE_URL}/v2/skyblock/bazaar"  # endpoint ini keyless

# --- Fetch behaviour (dipakai mulai Phase 5) ---
FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", "60"))

# --- Phase 2: retry & sanity check ---
# Jumlah produk Bazaar normal ada di kisaran 1800-an (per pengecekan manual).
# Diberi buffer cukup jauh di bawahnya supaya tidak false-positive kalau Hypixel
# nambah/kurangin beberapa item, tapi tetap ketahuan kalau API balikin data rusak/kosong.
MIN_EXPECTED_PRODUCTS = 1000
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 5  # jeda awal, akan digandakan tiap percobaan (5s -> 10s -> 20s)

# --- Phase 6: database ---
# Default: SQLite lokal (file di data/bazaar.db), zero setup, cocok untuk dev/testing.
# Nanti saat deploy, tinggal isi DATABASE_URL di .env dengan connection string
# Postgres/Supabase - kode di src/database.py tidak perlu diubah sama sekali.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'bazaar.db'}")

# --- Paths ---
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
LOGS_DIR = BASE_DIR / "logs"

# Pastikan folder-folder penting selalu ada saat config di-import
for _dir in (DATA_RAW_DIR, DATA_PROCESSED_DIR, LOGS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
