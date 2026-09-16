"""
Backup: export seluruh isi tabel bazaar_snapshots & mayor_snapshots dari
database (Supabase/lokal) ke file Parquet terkompresi.

WAJIB dijalankan SEBELUM menghapus data apapun di Supabase - data historis
Bazaar tidak bisa di-fetch ulang untuk waktu yang sudah lewat, jadi begitu
dihapus tanpa backup, hilang permanen.

Cara pakai: python scripts/export_backup.py
Hasil disimpan di: data/archive/
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src import config
from src.database import engine


def export_table_to_parquet(table_name: str, output_dir: Path):
    df = pd.read_sql(f"SELECT * FROM {table_name}", engine)

    if df.empty:
        print(f"[INFO] Tabel '{table_name}' kosong, tidak ada yang diekspor.")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_path = output_dir / f"{table_name}_backup_{timestamp}.parquet"

    df.to_parquet(file_path, compression="snappy", index=False)

    size_kb = file_path.stat().st_size / 1024
    print(f"[OK] {len(df)} baris dari '{table_name}' -> {file_path.name} ({size_kb:.1f} KB)")
    return file_path


if __name__ == "__main__":
    archive_dir = config.BASE_DIR / "data" / "archive"

    print("=== Backup database sebelum penghapusan ===\n")
    export_table_to_parquet("bazaar_snapshots", archive_dir)
    export_table_to_parquet("mayor_snapshots", archive_dir)

    print(f"\nSelesai. File backup ada di: {archive_dir}")
    print("Setelah dicek file-nya valid, baru aman untuk hapus data di Supabase.")
