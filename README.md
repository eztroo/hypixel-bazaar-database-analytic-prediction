# Hypixel SkyBlock Bazaar Price Predictor

Skripsi: Analisis dan Prediksi Pergerakan Harga pada Virtual Economy Hypixel SkyBlock
Menggunakan Data Historis Bazaar dan Faktor In-Game.

> Proyek ini tidak berafiliasi atau didukung oleh Hypixel.

## Status
Phase 0 — Setup Environment.

## Struktur Project
```
hypixel-skyblock-predictor/
├── src/            -> kode inti (config, nanti api client, parser, dll di phase berikutnya)
├── scripts/        -> script yang dijalankan manual (verifikasi setup, dll)
├── data/
│   ├── raw/         -> data mentah hasil fetch (Phase 4)
│   └── processed/   -> data yang sudah dibersihkan (Phase 3)
├── logs/            -> log dari automatic collector (Phase 5)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup (Phase 0)

1. Buat virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

2. Install dependency:
   ```bash
   pip install -r requirements.txt
   ```

3. Siapkan API key:
   - Buka https://developer.hypixel.net/dashboard/ -> **Create App** -> pilih **Personal API Key** (key ini tidak expire, beda dengan default key dari `/api` in-game yang expire 3 hari)
   - Salin `.env.example` menjadi `.env`
   - Isi `HYPIXEL_API_KEY` dengan key kamu
   (Catatan: khusus endpoint Bazaar sebenarnya tidak wajib key karena endpoint-nya keyless, tapi key tetap disiapkan untuk Phase 8 - mayor/event data yang kemungkinan butuh endpoint lain)

4. Verifikasi setup:
   ```bash
   python scripts/verify_setup.py
   ```
   Semua pengecekan harus `[OK]` sebelum lanjut ke Phase 1.

## Kepatuhan Kebijakan API
- Satu project = satu aplikasi terdaftar di Hypixel Developer Portal
- Menggunakan endpoint publik `/v2/skyblock/bazaar` untuk data pasar (bukan data pemain individual)
- Fetch seluruh produk dalam satu request (bukan per-item) untuk efisiensi & mematuhi anjuran caching
- Scheduler (Phase 5) perlu dijaga tetap aktif — aplikasi API dianggap tidak aktif jika tidak ada request sama sekali selama 28 hari

## Roadmap Phase
- [x] Phase 0 — Setup Environment
- [ ] Phase 1 — Connect ke Hypixel API
- [ ] Phase 2 — Fetch seluruh Bazaar
- [ ] Phase 3 — Parse & clean data
- [ ] Phase 4 — Save raw data
- [ ] Phase 5 — Automatic data collector
- [ ] Phase 6 — Database
- [ ] Phase 7 — Historical data ingestion
- [ ] Phase 8 — Mayor / Event data
- [ ] Phase 9 — Data validation
- [ ] Phase 10 — EDA
- [ ] Phase 11 — Feature engineering
- [ ] Phase 12 — ML
