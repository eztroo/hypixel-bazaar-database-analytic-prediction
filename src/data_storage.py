"""
Phase 4 - Save Raw Data (+ simpan data processed).

Prinsip utama: raw data (JSON asli dari API) TIDAK PERNAH diubah/ditimpa
setelah disimpan. Ini "arsip" - kalau logic parsing/cleaning di Phase 3
ternyata perlu direvisi nanti, kita masih punya sumber data asli untuk
diproses ulang, tanpa perlu fetch ulang (yang untuk data masa lalu tidak
mungkin dilakukan lagi).

Struktur penyimpanan:
    data/raw/<YYYY-MM-DD>/bazaar_<HHMMSS>.json   -> 1 file per fetch
    data/processed/bazaar_<YYYY-MM-DD>.csv        -> 1 file per hari, di-append
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src import config


def save_raw_response(raw_data: dict, fetched_at: datetime) -> Path:
    """
    Simpan response mentah dari API sebagai file JSON, tidak diubah sama sekali.

    Args:
        raw_data: dict mentah hasil fetch_bazaar()
        fetched_at: waktu fetch (dipakai untuk penamaan folder/file)

    Returns:
        Path ke file JSON yang baru disimpan.
    """
    date_folder = config.DATA_RAW_DIR / fetched_at.strftime("%Y-%m-%d")
    date_folder.mkdir(parents=True, exist_ok=True)

    filename = f"bazaar_{fetched_at.strftime('%H%M%S')}.json"
    file_path = date_folder / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f)

    return file_path


def save_processed_snapshot(df: pd.DataFrame, fetched_at: datetime) -> Path:
    """
    Simpan DataFrame yang sudah di-parse & clean (Phase 3) ke CSV harian.
    Append kalau file untuk tanggal itu sudah ada, bikin baru kalau belum.

    Returns:
        Path ke file CSV yang dipakai/dibuat.
    """
    filename = f"bazaar_{fetched_at.strftime('%Y-%m-%d')}.csv"
    file_path = config.DATA_PROCESSED_DIR / filename

    file_exists = file_path.exists()
    df.to_csv(file_path, mode="a", header=not file_exists, index=False)

    return file_path


if __name__ == "__main__":
    # Test cepat manual: python -m src.data_storage
    from src.data_cleaner import clean_bazaar_snapshot, parse_bazaar_snapshot
    from src.hypixel_client import fetch_bazaar

    now = datetime.now(timezone.utc)
    raw = fetch_bazaar()

    raw_path = save_raw_response(raw, now)
    print(f"[OK] Raw JSON disimpan ke: {raw_path}")

    df = parse_bazaar_snapshot(raw)
    df_clean = clean_bazaar_snapshot(df)
    processed_path = save_processed_snapshot(df_clean, now)
    print(f"[OK] Processed CSV disimpan ke: {processed_path} ({len(df_clean)} baris)")
