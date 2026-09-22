"""
scripts/export_backup.py

Export tabel Supabase (Postgres) ke file Parquet lokal, per tabel,
dengan chunked reading supaya aman untuk dataset besar (jutaan baris).

Requirement:
    pip install sqlalchemy psycopg2-binary pandas pyarrow python-dotenv

Environment variable yang dibutuhkan (taruh di .env, sama seperti yang
dipakai run_once.py -- pakai connection string mode "Session pooling"
dari Supabase, BUKAN Direct connection, karena alasan IPv4/IPv6 yang
sama seperti waktu setup GitHub Actions):

    DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>:<port>/<db>

Usage:
    python scripts/export_backup.py
    python scripts/export_backup.py --tables bazaar_snapshots mayor_snapshots
    python scripts/export_backup.py --outdir backup/2026-09-17 --chunksize 200000
"""

import os
import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

DEFAULT_TABLES = ["bazaar_snapshots", "mayor_snapshots"]


def get_engine():
    db_url = os.environ["DATABASE_URL"]
    return create_engine(db_url)


def export_table(engine, table_name: str, outdir: Path, chunksize: int):
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / f"{table_name}.parquet"

    print(f"[export] {table_name} -> {out_path}")

    chunks = []
    total_rows = 0
    # baca per-chunk supaya tidak membebani RAM untuk tabel jutaan baris
    for i, chunk in enumerate(
        pd.read_sql_table(table_name, con=engine, chunksize=chunksize)
    ):
        chunks.append(chunk)
        total_rows += len(chunk)
        print(f"  chunk {i}: +{len(chunk)} baris (total {total_rows})")

    if not chunks:
        print(f"  [WARN] tabel {table_name} kosong, dilewati.")
        return

    df = pd.concat(chunks, ignore_index=True)
    df.to_parquet(out_path, engine="pyarrow", compression="snappy", index=False)
    size_mb = out_path.stat().st_size / 1e6
    print(f"  selesai: {total_rows} baris, {size_mb:.2f} MB -> {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Export tabel Supabase ke Parquet")
    parser.add_argument("--tables", nargs="+", default=DEFAULT_TABLES,
                         help="Nama tabel yang mau di-export (default: bazaar_snapshots mayor_snapshots)")
    parser.add_argument("--outdir", default="backup",
                         help="Folder output, mis. backup/2026-09-17")
    parser.add_argument("--chunksize", type=int, default=100_000,
                         help="Jumlah baris per chunk saat membaca dari DB")
    args = parser.parse_args()

    engine = get_engine()
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    outdir = Path(args.outdir)
    for table in args.tables:
        if table not in existing_tables:
            print(f"[SKIP] tabel '{table}' tidak ditemukan di database.")
            continue
        export_table(engine, table, outdir, args.chunksize)

    print("\nSelesai. Cek isi folder:", outdir.resolve())


if __name__ == "__main__":
    main()
