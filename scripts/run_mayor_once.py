"""
Phase 8 - Entry point untuk 1 siklus fetch data mayor/election.

Dipanggil oleh .github/workflows/fetch-mayor.yml, terpisah dari
run_once.py (Bazaar) karena datanya beda karakter: mayor jarang berubah
(real-life beberapa hari sekali), jadi dijadwalkan jauh lebih jarang -
tidak perlu tiap beberapa menit kayak Bazaar.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.collector import setup_logger
from src.database import init_db, save_election_to_db
from src.hypixel_client import HypixelAPIError, fetch_election
from src.mayor_data import parse_election_snapshot


def main():
    logger = setup_logger()
    init_db()

    try:
        raw_data = fetch_election()
        parsed = parse_election_snapshot(raw_data)
        save_election_to_db(parsed)
        logger.info(
            f"Mayor snapshot berhasil disimpan: mayor={parsed['mayor_name']}, "
            f"perks=[{parsed['perks']}], election_aktif={parsed['is_election_active']}"
        )
        sys.exit(0)
    except HypixelAPIError as e:
        logger.error(f"Gagal fetch mayor/election: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Gagal fetch mayor/election (error tak terduga): {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
