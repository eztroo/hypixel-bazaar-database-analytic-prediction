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
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

load_dotenv()

DEFAULT_TABLES = ["bazaar_snapshots", "mayor_snapshots"]


def get_engine():
    db_url = os.environ["DATABASE_URL"]
    return create_engine(db_url)


def export_table(engine, table_name, outdir, chunksize=200_000, start_id=0):
    """Export tabel ke Parquet per-batch. start_id: lanjut dari id terakhir yang sudah pernah di-export."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    last_id, part, total = start_id, 0, 0
    query = text(f"SELECT * FROM {table_name} WHERE id > :last_id ORDER BY id LIMIT :n")

    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            try:
                conn.exec_driver_sql("SET statement_timeout = 0")
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"[warn] gagal set statement_timeout: {e}")

        while True:
            df = pd.read_sql(query, conn, params={"last_id": last_id, "n": chunksize})
            conn.commit()  # tutup transaksi: lepas lock baca sebelum batch berikutnya
            if df.empty:
                break
            part += 1
            path = outdir / f"{table_name}_id{int(df['id'].iloc[0])}-{int(df['id'].iloc[-1])}.parquet"
            df.to_parquet(path, compression="snappy", index=False)
            last_id = int(df["id"].iloc[-1])
            total += len(df)
            print(f"[export] {table_name}: part {part} -> {len(df):,} baris (total {total:,}), id terakhir {last_id}")

    print(f"[export] {table_name} selesai: {total:,} baris. id terakhir yang ke-export: {last_id}")
    return total


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
