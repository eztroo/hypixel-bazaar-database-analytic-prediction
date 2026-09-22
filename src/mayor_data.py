"""
Phase 8 - Mayor / Event Data.

Beda dari Bazaar, data mayor ini tidak perlu logic cleaning rumit (tidak ada
kasus "item tidak aktif" dsb) - cukup di-parse jadi bentuk flat yang gampang
di-query nanti pas Phase 11 (feature engineering), misal "mayor apa yang
aktif saat snapshot Bazaar jam sekian diambil".

Struktur respons API (dari dokumentasi tidak resmi/community):
{
  "mayor": {
      "name": "...", "perks": [...],
      "election": {"year": N, "candidates": [{"name", "votes"}, ...]}  # election SEBELUMNYA, yang menentukan mayor saat ini
  },
  "current": {"year": N+1, "candidates": [{"name", "votes"}, ...]}  # election yang sedang/akan berjalan
}
"votes" di "current" bisa 0 kalau voting belum dibuka (kandidat baru diumumkan),
jadi status "election aktif" dicek dari ada tidaknya vote masuk, bukan cuma
keberadaan field "current" saja (field ini kemungkinan selalu ada).
"""

import json
from datetime import datetime, timezone


def _leading_candidate(candidates: list) -> tuple:
    """
    Dari daftar kandidat (list of {"name", "votes"}), cari yang vote-nya
    tertinggi, dan hitung selisih (margin) ke posisi kedua.

    Returns:
        (nama_kandidat_teratas, jumlah_vote_teratas, margin_ke_posisi_2)
        Semua None kalau daftar kosong.
    """
    if not candidates:
        return None, None, None

    sorted_candidates = sorted(candidates, key=lambda c: c.get("votes", 0) or 0, reverse=True)
    top = sorted_candidates[0]
    top_votes = top.get("votes", 0) or 0
    runner_up_votes = sorted_candidates[1].get("votes", 0) or 0 if len(sorted_candidates) > 1 else 0

    return top.get("name"), top_votes, top_votes - runner_up_votes


def parse_election_snapshot(raw_data: dict, fetched_at: datetime = None) -> dict:
    """
    Ubah dict mentah dari endpoint election jadi bentuk flat siap simpan ke DB.

    Args:
        raw_data: dict mentah hasil fetch_election()
        fetched_at: waktu fetch. Default waktu sekarang kalau tidak diisi.

    Returns:
        dict flat siap dimasukkan ke tabel mayor_snapshots.
    """
    if fetched_at is None:
        fetched_at = datetime.now(timezone.utc)

    mayor = raw_data.get("mayor", {}) or {}
    mayor_name = mayor.get("name")

    perks = mayor.get("perks", []) or []
    perk_names = ", ".join(p.get("name", "") for p in perks if p.get("name"))

    # Election sebelumnya (yang menentukan mayor saat ini) - dari mayor.election
    prev_election = mayor.get("election", {}) or {}
    prev_candidates = prev_election.get("candidates", []) or []
    _, prev_winner_votes, prev_win_margin = _leading_candidate(prev_candidates)

    # Election yang sedang/akan berjalan - dari field "current"
    current_election = raw_data.get("current", {}) or {}
    current_candidates = current_election.get("candidates", []) or []
    leading_candidate, leading_votes, leading_margin = _leading_candidate(current_candidates)

    total_current_votes = sum((c.get("votes", 0) or 0) for c in current_candidates)
    is_election_active = total_current_votes > 0  # ada vote masuk = voting sedang berjalan

    return {
        "fetched_at": fetched_at,
        "mayor_name": mayor_name,
        "perks": perk_names,
        "is_election_active": is_election_active,
        "leading_candidate": leading_candidate,
        "leading_candidate_votes": leading_votes,
        "leading_candidate_margin": leading_margin,
        "prev_election_winner_votes": prev_winner_votes,
        "prev_election_win_margin": prev_win_margin,
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
    if parsed["is_election_active"]:
        print(f"Kandidat unggul: {parsed['leading_candidate']} "
              f"({parsed['leading_candidate_votes']} vote, unggul {parsed['leading_candidate_margin']})")
