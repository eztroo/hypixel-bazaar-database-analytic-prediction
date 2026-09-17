"""
Phase 8 - Mayor / Event Data.

Beda dari Bazaar, data mayor ini tidak perlu logic cleaning rumit (tidak ada
kasus "item tidak aktif" dsb) - cukup di-parse jadi bentuk flat yang gampang
di-query nanti pas Phase 11 (feature engineering), misal "mayor apa yang
aktif saat snapshot Bazaar jam sekian diambil".
"""

import json
from datetime import datetime, timezone


def parse_election_snapshot(raw_data: dict, fetched_at: datetime = None) -> dict:
    """
    Ubah dict mentah dari endpoint election jadi bentuk flat siap simpan ke DB.

    Args:
        raw_data: dict mentah hasil fetch_election()
        fetched_at: waktu fetch. Default waktu sekarang kalau tidak diisi.

    Returns:
        dict flat: {fetched_at, mayor_name, perks, is_election_active, raw_json}
    """
    if fetched_at is None:
        fetched_at = datetime.now(timezone.utc)

    mayor = raw_data.get("mayor", {}) or {}
    mayor_name = mayor.get("name")

    perks = mayor.get("perks", []) or []
    perk_names = ", ".join(p.get("name", "") for p in perks if p.get("name"))

    # Field "current" cuma muncul di respons API kalau lagi ada election
    # yang sedang berjalan (bukan mayor yang sedang menjabat) - jadi
    # keberadaan field ini sendiri sudah cukup jadi penanda.
    is_election_active = "current" in raw_data

    return {
        "fetched_at": fetched_at,
        "mayor_name": mayor_name,
        "perks": perk_names,
        "is_election_active": is_election_active,
        "raw_json": json.dumps(raw_data),
    }


if __name__ == "__main__":
    # Test cepat manual: python -m src.mayor_data
    from src.hypixel_client import fetch_election

    raw = fetch_election()
    parsed = parse_election_snapshot(raw)
    print(f"Mayor saat ini: {parsed['mayor_name']}")
    print(f"Perks aktif: {parsed['perks']}")
    print(f"Sedang ada election: {parsed['is_election_active']}")
