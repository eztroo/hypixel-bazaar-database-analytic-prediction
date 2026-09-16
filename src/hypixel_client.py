"""
Phase 1 - Koneksi ke Hypixel API.
Phase 2 - Fetch seluruh Bazaar secara reliable (retry + validasi kelengkapan).

Modul ini cuma bertugas ngambil data mentah dari endpoint Bazaar dan
mengembalikannya sebagai dict Python. Tidak ada logic parsing/cleaning
di sini (itu tugas Phase 3) - supaya tiap modul punya tanggung jawab jelas.
"""

import time

import requests

from src import config


class HypixelAPIError(Exception):
    """Dilempar kalau request ke Hypixel API gagal atau responsnya tidak valid."""
    pass


def _fetch_bazaar_once(timeout: int = 10) -> dict:
    """
    Phase 1 - satu kali percobaan fetch, tanpa retry.
    Dipanggil oleh fetch_bazaar() di bawah (Phase 2), yang menambahkan
    retry + validasi kelengkapan data di atas function dasar ini.

    Returns:
        dict mentah dari Hypixel API, contoh struktur:
        {
            "success": True,
            "lastUpdated": 1234567890123,
            "products": {
                "ENCHANTED_COAL": {
                    "product_id": "ENCHANTED_COAL",
                    "quick_status": {...},
                    "sell_summary": [...],
                    "buy_summary": [...]
                },
                ...
            }
        }

    Raises:
        HypixelAPIError: kalau koneksi gagal, timeout, status bukan 200,
                          atau field "success" dari API bernilai False.
    """
    headers = {}
    if config.HYPIXEL_API_KEY:
        # Endpoint bazaar sebenarnya keyless, tapi kalau key tersedia kita
        # sertakan saja - tidak ada ruginya dan siap dipakai untuk endpoint lain nanti.
        headers["API-Key"] = config.HYPIXEL_API_KEY

    try:
        response = requests.get(config.BAZAAR_ENDPOINT, headers=headers, timeout=timeout)
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

    Ini function yang dipakai semua kode lain (demo script, dan nanti
    Phase 4/5) - bukan _fetch_bazaar_once() secara langsung.

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


if __name__ == "__main__":
    # Test cepat manual: python -m src.hypixel_client
    data = fetch_bazaar()
    jumlah_produk = len(data.get("products", {}))
    print(f"Berhasil konek. Jumlah produk di Bazaar saat ini: {jumlah_produk}")
