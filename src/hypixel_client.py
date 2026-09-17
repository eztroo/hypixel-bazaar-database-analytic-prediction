"""
Phase 1 - Koneksi ke Hypixel API.
Phase 2 - Fetch seluruh Bazaar secara reliable (retry + validasi kelengkapan).
Phase 8 - Fetch data Mayor/Election.

Modul ini cuma bertugas ngambil data mentah dari Hypixel API dan
mengembalikannya sebagai dict Python. Tidak ada logic parsing/cleaning
di sini (itu tugas Phase 3/data_cleaner) - supaya tiap modul punya
tanggung jawab jelas.
"""

import time

import requests

from src import config


class HypixelAPIError(Exception):
    """Dilempar kalau request ke Hypixel API gagal atau responsnya tidak valid."""
    pass


def _fetch_json_once(url: str, timeout: int = 10) -> dict:
    """
    Satu kali percobaan fetch ke endpoint Hypixel API manapun yang berbentuk
    {"success": bool, ...}. Dipakai bareng oleh _fetch_bazaar_once() dan
    fetch_election() - supaya logic retry/error handling tidak duplikat.

    Raises:
        HypixelAPIError: kalau koneksi gagal, timeout, status bukan 200,
                          respons bukan JSON valid, atau "success" bernilai False.
    """
    headers = {}
    if config.HYPIXEL_API_KEY:
        # Endpoint bazaar & election sebenarnya keyless, tapi kalau key
        # tersedia kita sertakan saja - tidak ada ruginya.
        headers["API-Key"] = config.HYPIXEL_API_KEY

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout:
        raise HypixelAPIError(f"Request timeout setelah {timeout} detik.")
    except requests.exceptions.ConnectionError as e:
        raise HypixelAPIError(f"Gagal konek ke Hypixel API: {e}")

    if response.status_code != 200:
        raise HypixelAPIError(
            f"Hypixel API mengembalikan status {response.status_code}: {response.text[:200]}"
        )

    try:
        data = response.json()
    except ValueError:
        raise HypixelAPIError("Respons bukan JSON yang valid.")

    if not data.get("success", False):
        raise HypixelAPIError(f"API merespons success=False: {data}")

    return data


def _fetch_bazaar_once(timeout: int = 10) -> dict:
    """
    Phase 1 - satu kali percobaan fetch Bazaar, tanpa retry.
    Dipanggil oleh fetch_bazaar() di bawah (Phase 2), yang menambahkan
    retry + validasi kelengkapan data di atas function dasar ini.
    """
    return _fetch_json_once(config.BAZAAR_ENDPOINT, timeout=timeout)


def _validate_bazaar_data(data: dict) -> None:
    """
    Phase 2 - sanity check: pastikan jumlah produk yang dikembalikan wajar.
    Kalau API balikin data "sukses" tapi isinya cuma segelintir produk
    (misal karena glitch di server Hypixel), itu tetap harus dianggap gagal -
    data yang tidak lengkap lebih berbahaya daripada error yang jelas,
    karena bisa lolos tanpa disadari sampai tahap analisis nanti.
    """
    jumlah_produk = len(data.get("products", {}))
    if jumlah_produk < config.MIN_EXPECTED_PRODUCTS:
        raise HypixelAPIError(
            f"Jumlah produk mencurigakan: cuma {jumlah_produk} "
            f"(minimal diharapkan {config.MIN_EXPECTED_PRODUCTS}). "
            "Kemungkinan data dari API tidak lengkap/rusak."
        )


def fetch_bazaar(
    timeout: int = 10,
    retries: int = config.RETRY_ATTEMPTS,
    backoff_seconds: int = config.RETRY_BACKOFF_SECONDS,
) -> dict:
    """
    Phase 2 - Fetch Bazaar yang reliable: retry otomatis dengan exponential
    backoff kalau gagal, dan validasi jumlah produk sebelum data diterima.

    Ini function yang dipakai semua kode lain (collector, dll) - bukan
    _fetch_bazaar_once() secara langsung.

    Raises:
        HypixelAPIError: kalau semua percobaan retry habis dan tetap gagal,
                          atau data yang didapat gagal validasi.
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            data = _fetch_bazaar_once(timeout=timeout)
            _validate_bazaar_data(data)
            return data
        except HypixelAPIError as e:
            last_error = e
            if attempt < retries:
                wait = backoff_seconds * (2 ** (attempt - 1))  # 5s -> 10s -> 20s
                print(f"[WARN] Percobaan {attempt}/{retries} gagal: {e}")
                print(f"[WARN] Mencoba lagi dalam {wait} detik...")
                time.sleep(wait)

    raise HypixelAPIError(
        f"Gagal fetch Bazaar setelah {retries}x percobaan. Error terakhir: {last_error}"
    )


def fetch_election(
    timeout: int = 10,
    retries: int = config.RETRY_ATTEMPTS,
    backoff_seconds: int = config.RETRY_BACKOFF_SECONDS,
) -> dict:
    """
    Phase 8 - Fetch data mayor & election yang sedang aktif.
    Endpoint: resources/skyblock/election (keyless).

    Data ini jauh lebih jarang berubah dibanding Bazaar (real-life beberapa
    hari sekali) - makanya dipanggil dengan jadwal terpisah yang jauh lebih
    jarang (lihat .github/workflows/fetch-mayor.yml), bukan tiap 7 menit.

    Returns:
        dict mentah, kira-kira strukturnya:
        {
            "success": True,
            "mayor": {
                "name": "...",
                "perks": [{"name": "...", "description": "..."}, ...],
                "minister": {...}  # opsional, tidak selalu ada
            },
            "current": {...}  # cuma ada kalau lagi ada election berjalan
        }

    Raises:
        HypixelAPIError: kalau semua retry gagal, atau field "mayor" tidak ada
                          di respons (tanda data mencurigakan/rusak).
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            data = _fetch_json_once(config.ELECTION_ENDPOINT, timeout=timeout)
            if "mayor" not in data:
                raise HypixelAPIError(f"Field 'mayor' tidak ada di respons: {data}")
            return data
        except HypixelAPIError as e:
            last_error = e
            if attempt < retries:
                wait = backoff_seconds * (2 ** (attempt - 1))
                print(f"[WARN] Percobaan {attempt}/{retries} gagal: {e}")
                print(f"[WARN] Mencoba lagi dalam {wait} detik...")
                time.sleep(wait)

    raise HypixelAPIError(
        f"Gagal fetch election setelah {retries}x percobaan. Error terakhir: {last_error}"
    )


if __name__ == "__main__":
    # Test cepat manual: python -m src.hypixel_client
    data = fetch_bazaar()
    jumlah_produk = len(data.get("products", {}))
    print(f"Berhasil konek. Jumlah produk di Bazaar saat ini: {jumlah_produk}")
