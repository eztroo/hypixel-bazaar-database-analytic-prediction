"""
Phase 6 - Database.

Pakai SQLAlchemy supaya kode ini portable antara SQLite (lokal/testing,
tanpa setup apapun) dan PostgreSQL/Supabase (nanti pas deploy) - cukup
ganti DATABASE_URL di .env, tidak perlu ubah kode.

Skema: 1 tabel bazaar_snapshots, 1 baris = 1 produk pada 1 waktu fetch
(sama seperti struktur CSV processed di Phase 3-4). Index gabungan
(product_id, fetched_at) dipasang dari awal karena query paling umum
nanti adalah "ambil histori harga produk X dari waktu ke waktu".
"""

import pandas as pd
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base

from src import config

Base = declarative_base()


class BazaarSnapshot(Base):
    __tablename__ = "bazaar_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, nullable=False)
    fetched_at = Column(DateTime, nullable=False)
    api_last_updated = Column(BigInteger)
    buyPrice = Column(Float)
    sellPrice = Column(Float)
    buyVolume = Column(BigInteger)
    sellVolume = Column(BigInteger)
    buyMovingWeek = Column(BigInteger)
    sellMovingWeek = Column(BigInteger)
    buyOrders = Column(Integer)
    sellOrders = Column(Integer)
    is_tradeable = Column(Boolean)

    __table_args__ = (
        Index("ix_product_fetched_at", "product_id", "fetched_at"),
    )


class MayorSnapshot(Base):
    """
    Phase 8 - snapshot mayor/election. Volumenya jauh lebih kecil dari
    bazaar_snapshots (dipoll tiap beberapa jam, bukan tiap beberapa menit),
    jadi raw_json disimpan penuh tanpa khawatir soal storage.
    """
    __tablename__ = "mayor_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fetched_at = Column(DateTime, nullable=False)
    mayor_name = Column(String)
    perks = Column(String)
    is_election_active = Column(Boolean)
    raw_json = Column(String)

    __table_args__ = (
        Index("ix_mayor_fetched_at", "fetched_at"),
    )


engine = create_engine(config.DATABASE_URL)


def init_db():
    """Bikin tabel kalau belum ada. Aman dipanggil berkali-kali (tidak akan hapus data)."""
    Base.metadata.create_all(engine)


def save_snapshot_to_db(df: pd.DataFrame) -> int:
    """
    Simpan DataFrame hasil Phase 3 (clean_bazaar_snapshot) ke database.

    Returns:
        Jumlah baris yang berhasil disimpan.
    """
    df = df.copy()
    df["fetched_at"] = pd.to_datetime(df["fetched_at"])
    df.to_sql(BazaarSnapshot.__tablename__, engine, if_exists="append", index=False)
    return len(df)


def save_election_to_db(parsed: dict) -> None:
    """
    Phase 8 - simpan 1 snapshot mayor/election (hasil parse_election_snapshot) ke database.
    """
    with engine.begin() as conn:
        conn.execute(MayorSnapshot.__table__.insert().values(**parsed))


def count_rows() -> int:
    """Helper untuk cek jumlah total baris di database (dipakai untuk verifikasi/debug)."""
    with engine.connect() as conn:
        result = conn.exec_driver_sql(f"SELECT COUNT(*) FROM {BazaarSnapshot.__tablename__}")
        return result.scalar()


if __name__ == "__main__":
    # Test cepat manual: python -m src.database
    init_db()
    print(f"Database siap di: {config.DATABASE_URL}")
    print(f"Total baris saat ini: {count_rows()}")
