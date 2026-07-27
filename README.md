# Solana Screener — Alert Harian + Recap Mingguan

Sistem screening 2 bagian untuk token Solana kecil/baru, dengan filter
keamanan ketat:

1. **Alert Harian** — begitu ada token baru yang lolos filter, langsung
   dikirim ke Telegram saat itu juga (dicek 1x sehari)
2. **Recap Mingguan** — tiap Minggu, rekap semua token yang direkomendasikan
   minggu itu: berapa banyak, naik/turun berapa persen dibanding harga saat
   direkomendasikan

⚠️ **Disclaimer**: Ini alat bantu riset, bukan penasihat keuangan. Filter
keamanan mengurangi (bukan menghilangkan) risiko rug pull/scam. Recap
performa historis tidak menjamin hasil ke depan. Selalu lakukan analisa
sendiri sebelum membeli apa pun.

## ⚠️ Migrasi dari Versi Sebelumnya

Kalau repo kamu masih pakai versi lama (`crypto_screener.py` +
`weekly_screen.yml` tunggal), **hapus dulu** 2 file itu, lalu upload semua
file baru di bawah ini. Struktur akhirnya harus seperti ini:

```
nama-repo/
├── screener_common.py
├── daily_screener.py
├── weekly_recap.py
├── requirements.txt
├── data/
│   └── flagged_tokens.json
├── README.md
└── .github/
    └── workflows/
        ├── daily_screen.yml
        └── weekly_recap.yml
```

## Setup

Kalau kamu sudah pernah setup versi sebelumnya, **secret Telegram kamu
(`TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID`) tidak perlu diulang** — tetap
kepakai. Langsung ke langkah "Aktifkan Izin Tulis" di bawah.

### 1. Buat Bot Telegram (skip kalau sudah pernah)
Lihat langkah lengkap di percakapan sebelumnya, atau chat @BotFather →
`/newbot`.

### 2. Aktifkan Izin Tulis untuk GitHub Actions (WAJIB, langkah baru)

Karena sekarang script perlu menyimpan riwayat token yang direkomendasikan
ke dalam file `data/flagged_tokens.json` di repo, GitHub Actions perlu izin
menulis (bukan cuma baca):

1. Buka repo → **Settings** → **Actions** → **General**
2. Scroll ke bagian **Workflow permissions**
3. Pilih **"Read and write permissions"**
4. Tekan **Save**

Kalau langkah ini dilewati, workflow harian akan tetap kirim alert dengan
benar, tapi gagal menyimpan log-nya — dan recap mingguan jadi tidak akurat.

### 3. Upload Semua File
Upload semua file sesuai struktur folder di atas.

### 4. Selesai
- **Daily Solana Screener** jalan otomatis tiap hari jam 08:00 WIB
- **Weekly Recap** jalan otomatis tiap Minggu jam 08:00 WIB

Mau tes tanpa nunggu jadwal? Buka tab **Actions** → pilih workflow yang mau
dites → **Run workflow**.

## Cara Kerja

**Alert Harian** (`daily_screener.py`):
1. Ambil token Solana baru dari DexScreener
2. Skip token yang sudah pernah direkomendasikan sebelumnya (dicek dari log)
3. Saring pakai filter keamanan ketat
4. Kalau lolos dan ada sinyal momentum → kirim alert Telegram langsung +
   simpan ke `data/flagged_tokens.json` (harga saat itu dicatat sebagai
   harga acuan)

**Recap Mingguan** (`weekly_recap.py`):
1. Baca `data/flagged_tokens.json`, ambil yang direkomendasikan 7 hari
   terakhir
2. Cek harga token itu sekarang, bandingkan dengan harga saat direkomendasikan
3. Kirim ringkasan: jumlah token, berapa yang naik/turun, rata-rata performa

## Mengubah Kriteria Filter

Semua angka filter ada di `screener_common.py`:

```python
MIN_PAIR_AGE_DAYS = 7        # umur token minimum (hari)
MAX_PAIR_AGE_DAYS = 120      # umur token maksimum (hari)
MIN_LIQUIDITY_USD = 50_000   # likuiditas minimum (USD)
MIN_VOLUME_24H_USD = 20_000  # volume 24 jam minimum (USD)
MIN_TXNS_24H = 50            # jumlah transaksi 24 jam minimum
MIN_MARKET_CAP = 500_000     # market cap minimum (USD)
MAX_MARKET_CAP = 20_000_000  # market cap maksimum (USD)
MIN_LIQ_MCAP_RATIO = 0.05    # rasio likuiditas/market cap minimum
```

## Data Source

Semua data dari [DexScreener public API](https://docs.dexscreener.com/api/reference)
— gratis, tanpa API key.
