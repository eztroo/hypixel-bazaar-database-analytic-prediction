"""
Entry point khusus untuk GitHub Actions (atau scheduler eksternal lain yang
sifatnya "trigger sekali, proses, lalu mati" - bukan proses yang hidup terus).

Beda dari src/collector.py (run_collector()) yang loop tanpa henti untuk
dijalankan lokal/VM - script ini cuma jalanin SATU siklus lalu keluar.
GitHub Actions yang bertanggung jawab menjadwalkan pemanggilan berulang
lewat cron di file workflow, bukan Python-nya yang loop.

Exit code 0 = sukses, 1 = gagal - supaya GitHub Actions bisa nampilin
status run (hijau/merah) dengan benar di tab Actions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.collector import run_single_cycle, setup_logger
from src.database import init_db


def main():
    logger = setup_logger()
    init_db()
    berhasil = run_single_cycle(logger)
    sys.exit(0 if berhasil else 1)


if __name__ == "__main__":
    main()
