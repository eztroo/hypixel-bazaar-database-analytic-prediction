"""
Phase 3 - Parse & Clean Data.

Dua tanggung jawab modul ini:
1. parse_bazaar_snapshot()  -> ubah dict mentah dari Hypixel API jadi DataFrame
2. clean_bazaar_snapshot()  -> validasi tipe data, tangani nilai kosong/aneh,
                                dan beri label (bukan hapus) untuk item yang
                                tidak aktif diperdagangkan.

Prinsip: tahap ini TIDAK menghapus baris data apapun. Item dengan harga/volume
0 tetap disimpan, cuma diberi flag is_tradeable=False - supaya insight soal
"kapan item ini aktif/tidak aktif" tidak hilang. Keputusan exclude dari
modeling baru diambil nanti di Phase 9 (data validation), setelah kita bisa
lihat pola dari banyak snapshot, bukan cuma satu.
"""

from datetime import datetime, timezone

import pandas as pd

# Kolom yang kita ambil dari quick_status tiap produk.
QUICK_STATUS_FIELDS = [
    "buyPrice",
    "sellPrice",
    "buyVolume",
    "sellVolume",
    "buyMovingWeek",
    "sellMovingWeek",
    "buyOrders",
    "sellOrders",
]


def parse_bazaar_snapshot(raw_data: dict, fetched_at: datetime = None) -> pd.DataFrame:
    """
    Ubah dict mentah dari Hypixel API jadi DataFrame, 1 baris = 1 produk
    pada 1 waktu fetch. Tidak ada validasi/cleaning di sini - murni parsing.

    Args:
        raw_data: dict mentah hasil fetch_bazaar()
        fetched_at: waktu fetch. Kalau tidak diisi, pakai waktu saat ini -
                    tapi sebaiknya diisi dan dipakai bersama dengan
                    save_raw_response() supaya timestamp-nya konsisten
                    antara file JSON mentah dan CSV processed.
    """
    if fetched_at is None:
        fetched_at = datetime.now(timezone.utc)
    fetched_at_str = fetched_at.isoformat()
    last_updated = raw_data.get("lastUpdated")

    rows = []
    for product_id, product_data in raw_data.get("products", {}).items():
        quick_status = product_data.get("quick_status", {}) or {}
        row = {
            "product_id": product_id,
            "fetched_at": fetched_at_str,
            "api_last_updated": last_updated,
        }
        for field in QUICK_STATUS_FIELDS:
            row[field] = quick_status.get(field)
        rows.append(row)

    return pd.DataFrame(rows)


def clean_bazaar_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validasi & bersihkan DataFrame hasil parse_bazaar_snapshot().

    Yang dilakukan:
    - Pastikan product_id tidak ada yang kosong (baris begini dibuang -
      ini beda kasus dari "harga 0", ini data yang benar-benar rusak/tidak
      bisa diidentifikasi produk apa)
    - Kolom numerik dipaksa jadi tipe numerik, nilai yang gagal dikonversi
      jadi NaN lalu diisi 0 (field ini di API memang defaultnya 0 kalau
      tidak ada aktivitas, bukan "data hilang")
    - Tambah kolom is_tradeable: True kalau item punya minimal 1 indikator
      aktivitas (harga atau volume atau order > 0)
    """
    df = df.copy()

    # 1. Buang baris tanpa product_id - ini data rusak, bukan "item tidak aktif"
    before = len(df)
    df = df[df["product_id"].notna() & (df["product_id"] != "")]
    dropped = before - len(df)
    if dropped > 0:
        print(f"[WARN] {dropped} baris dibuang karena product_id kosong/rusak.")

    # 2. Paksa kolom numerik jadi numerik, isi 0 kalau gagal/kosong
    for field in QUICK_STATUS_FIELDS:
        df[field] = pd.to_numeric(df[field], errors="coerce").fillna(0)

    # 3. Label item yang tidak aktif diperdagangkan, JANGAN dibuang
    activity_columns = ["buyPrice", "sellPrice", "buyVolume", "sellVolume", "buyOrders", "sellOrders"]
    df["is_tradeable"] = (df[activity_columns] > 0).any(axis=1)

    jumlah_tidak_aktif = (~df["is_tradeable"]).sum()
    print(f"[INFO] {jumlah_tidak_aktif} dari {len(df)} produk tidak aktif diperdagangkan pada snapshot ini.")

    return df


if __name__ == "__main__":
    # Test cepat manual pakai data asli: python -m src.data_cleaner
    from src.hypixel_client import fetch_bazaar

    raw = fetch_bazaar()
    df = parse_bazaar_snapshot(raw)
    df_clean = clean_bazaar_snapshot(df)
    print(df_clean.head())
    print(f"\nTotal baris: {len(df_clean)}, kolom: {list(df_clean.columns)}")
