"""
Demo: ambil snapshot Bazaar (1 atau beberapa kali), lalu jalankan pipeline
lengkap Phase 1-4: fetch -> simpan raw JSON -> parse -> clean -> simpan
processed CSV (harian).

Ini BUKAN Phase 5 (automatic collector) yang sebenarnya - itu nanti pakai
scheduler yang jalan terus-menerus di background dengan interval bisa diatur.
Script ini cuma buat kamu lihat hasil konkret Phase 1-4 dalam bentuk sederhana.

Cara pakai:
    python scripts/quick_fetch_demo.py            -> ambil 1x snapshot
    python scripts/quick_fetch_demo.py --n 2       -> ambil 2x snapshot, jeda 15 detik
"""

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_cleaner import clean_bazaar_snapshot, parse_bazaar_snapshot
from src.data_storage import save_processed_snapshot, save_raw_response
from src.hypixel_client import HypixelAPIError, fetch_bazaar


def main():
    parser = argparse.ArgumentParser(description="Demo fetch Bazaar -> raw JSON + processed CSV")
    parser.add_argument("--n", type=int, default=1, help="Jumlah snapshot yang diambil (default: 1)")
    parser.add_argument("--interval", type=int, default=15, help="Jeda detik antar snapshot (default: 15)")
    args = parser.parse_args()

    for i in range(1, args.n + 1):
        print(f"[{i}/{args.n}] Fetching data Bazaar...")
        try:
            raw_data = fetch_bazaar()
        except HypixelAPIError as e:
            print(f"[FAIL] {e}")
            return

        fetched_at = datetime.now(timezone.utc)

        raw_path = save_raw_response(raw_data, fetched_at)
        print(f"[OK] Raw JSON disimpan ke: {raw_path}")

        df = parse_bazaar_snapshot(raw_data, fetched_at)
        df_clean = clean_bazaar_snapshot(df)
        processed_path = save_processed_snapshot(df_clean, fetched_at)
        print(f"[OK] {len(df_clean)} produk (processed) disimpan ke: {processed_path}")

        if i < args.n:
            print(f"Menunggu {args.interval} detik sebelum snapshot berikutnya...")
            time.sleep(args.interval)

    print("\nSelesai.")


if __name__ == "__main__":
    main()
