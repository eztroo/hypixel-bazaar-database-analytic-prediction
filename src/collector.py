"""
Phase 5 - Automatic Data Collector.

Menjalankan pipeline Phase 1-4 (fetch -> save raw -> parse -> clean -> save
processed) secara berulang dengan interval tertentu, TANPA BERHENTI walau
ada siklus yang gagal.

Prinsip penting: satu siklus gagal (network error, API down sesaat, dll)
TIDAK boleh menghentikan seluruh program. Ini krusial karena collector ini
akan jalan tanpa diawasi selama berbulan-bulan - kalau 1x gagal langsung
crash total, bisa kehilangan data berhari-hari tanpa ada yang sadar.
"""

import logging
import time
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler

from src import config
from src.data_cleaner import clean_bazaar_snapshot, parse_bazaar_snapshot
from src.data_storage import save_processed_snapshot, save_raw_response
from src.database import init_db, save_snapshot_to_db
from src.hypixel_client import HypixelAPIError, fetch_bazaar


def setup_logger() -> logging.Logger:
    """
    Logger yang nulis ke console DAN ke file log harian (auto-rotate tiap
    tengah malam), supaya histori collector tetap bisa dicek walau sudah
    jalan berbulan-bulan tanpa perlu 1 file raksasa.
    """
    logger = logging.getLogger("collector")
    logger.setLevel(logging.INFO)

    if logger.handlers:  # hindari duplikat handler kalau function ini dipanggil berkali-kali
        return logger

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = TimedRotatingFileHandler(
        config.LOGS_DIR / "collector.log",
        when="midnight",
        backupCount=90,  # simpan log 90 hari terakhir, cukup untuk 1 semester
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def run_single_cycle(logger: logging.Logger) -> bool:
    """
    Jalankan 1 siklus penuh: fetch -> save raw -> parse -> clean -> save processed.

    Returns:
        True kalau siklus berhasil, False kalau gagal (sudah di-log di dalam,
        pemanggil tidak perlu raise/crash - cukup lanjut ke siklus berikutnya).
    """
    try:
        raw_data = fetch_bazaar()
        fetched_at = datetime.now(timezone.utc)

        raw_path = save_raw_response(raw_data, fetched_at)

        df = parse_bazaar_snapshot(raw_data, fetched_at)
        df_clean = clean_bazaar_snapshot(df)
        processed_path = save_processed_snapshot(df_clean, fetched_at)
        jumlah_disimpan_db = save_snapshot_to_db(df_clean)

        jumlah_tidak_aktif = (~df_clean["is_tradeable"]).sum()
        logger.info(
            f"Siklus berhasil: {len(df_clean)} produk disimpan "
            f"({jumlah_tidak_aktif} tidak aktif) -> {processed_path.name}, "
            f"{raw_path.name}, dan {jumlah_disimpan_db} baris ke database"
        )
        return True

    except HypixelAPIError as e:
        logger.error(f"Siklus gagal (API error): {e}")
        return False

    except Exception as e:
        # Sengaja tangkap Exception generic di sini juga (bukan cuma HypixelAPIError) -
        # kalau ada bug tak terduga di parsing/cleaning/save, collector tetap harus
        # lanjut jalan di siklus berikutnya, bukan mati total.
        logger.exception(f"Siklus gagal (error tak terduga): {e}")
        return False


def run_collector():
    """
    Loop utama - jalan terus sampai dihentikan manual (Ctrl+C) atau proses di-kill.
    """
    logger = setup_logger()
    init_db()
    logger.info(f"Collector dimulai. Interval: {config.FETCH_INTERVAL_SECONDS} detik.")

    cycle_count = 0
    success_count = 0

    try:
        while True:
            cycle_count += 1
            cycle_start = time.monotonic()

            berhasil = run_single_cycle(logger)
            if berhasil:
                success_count += 1

            elapsed = time.monotonic() - cycle_start
            sisa_waktu = max(0, config.FETCH_INTERVAL_SECONDS - elapsed)

            logger.info(
                f"Statistik: {success_count}/{cycle_count} siklus berhasil sejak collector jalan. "
                f"Tidur {sisa_waktu:.0f} detik sebelum siklus berikutnya."
            )
            time.sleep(sisa_waktu)

    except KeyboardInterrupt:
        logger.info(f"Collector dihentikan manual. Total: {success_count}/{cycle_count} siklus berhasil.")


if __name__ == "__main__":
    run_collector()
