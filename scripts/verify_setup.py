"""
Phase 0 - Verifikasi environment.
Jalankan: python scripts/verify_setup.py

Script ini mengecek:
1. Versi Python
2. Dependency inti sudah terinstall
3. File .env ada dan bisa dibaca
4. Folder data/logs sudah tersedia
"""

import sys
from pathlib import Path

# Supaya bisa import src/ walau script dijalankan dari mana saja
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def check_python_version():
    version = sys.version_info
    ok = version >= (3, 10)
    print(f"[{'OK' if ok else 'FAIL'}] Python version: {version.major}.{version.minor}.{version.micro}")
    return ok


def check_dependencies():
    required = ["requests", "dotenv", "pandas"]
    all_ok = True
    for pkg in required:
        try:
            __import__(pkg)
            print(f"[OK] Package terinstall: {pkg}")
        except ImportError:
            print(f"[FAIL] Package belum terinstall: {pkg} -> jalankan: pip install -r requirements.txt")
            all_ok = False
    return all_ok


def check_env_file():
    from src import config

    env_path = config.BASE_DIR / ".env"
    if not env_path.exists():
        print(f"[FAIL] File .env belum ada di {env_path}. Salin dari .env.example lalu isi HYPIXEL_API_KEY.")
        return False
    print(f"[OK] File .env ditemukan di {env_path}")

    if config.HYPIXEL_API_KEY:
        masked = config.HYPIXEL_API_KEY[:4] + "..." + config.HYPIXEL_API_KEY[-4:]
        print(f"[OK] HYPIXEL_API_KEY terbaca ({masked})")
    else:
        print("[INFO] HYPIXEL_API_KEY kosong — tidak masalah untuk endpoint Bazaar (keyless), "
              "tapi wajib diisi sebelum Phase 8 (mayor/event data).")
    return True


def check_folders():
    from src import config

    folders = [config.DATA_RAW_DIR, config.DATA_PROCESSED_DIR, config.LOGS_DIR]
    all_ok = True
    for folder in folders:
        if folder.exists():
            print(f"[OK] Folder tersedia: {folder}")
        else:
            print(f"[FAIL] Folder tidak ditemukan: {folder}")
            all_ok = False
    return all_ok


def main():
    print("=== Phase 0: Verifikasi Environment ===\n")
    results = [
        check_python_version(),
        check_dependencies(),
        check_env_file(),
        check_folders(),
    ]
    print("\n=== Ringkasan ===")
    if all(results):
        print("Semua pengecekan lolos. Siap lanjut ke Phase 1 (Connect ke Hypixel API).")
    else:
        print("Ada yang perlu diperbaiki dulu sebelum lanjut ke Phase 1 (lihat [FAIL] di atas).")


if __name__ == "__main__":
    main()
