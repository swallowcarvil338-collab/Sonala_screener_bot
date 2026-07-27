"""
Shared constants and DexScreener API helpers used by both
daily_screener.py and weekly_recap.py.
"""

import os
import time
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ---------------- Strict safety thresholds ----------------
MIN_PAIR_AGE_DAYS = 7
MAX_PAIR_AGE_DAYS = 120
MIN_LIQUIDITY_USD = 50_000
MIN_VOLUME_24H_USD = 20_000
MIN_TXNS_24H = 50
MIN_MARKET_CAP = 500_000
MAX_MARKET_CAP = 20_000_000
MIN_LIQ_MCAP_RATIO = 0.05

DEX_BASE = "https://api.dexscreener.com"
REQUEST_DELAY_SEC = 0.35  # be polite to the free public API


def get_latest_solana_token_addresses():
    """Pull the newest token profiles across chains, keep Solana only."""
    url = f"{DEX_BASE}/token-profiles/latest/v1"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []
    return [d["tokenAddress"] for d in data if d.get("chainId") == "solana" and d.get("tokenAddress")]


def get_best_pair(token_address):
    """Get the highest-liquidity Solana pair for a token address."""
    url = f"{DEX_BASE}/latest/dex/tokens/{token_address}"
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        return None
    data = r.json()
    pairs = data.get("pairs") or []
    sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
    if not sol_pairs:
        return None
    return max(sol_pairs, key=lambda p: (p.get("liquidity") or {}).get("usd", 0) or 0)


def passes_safety_filters(pair):
    liq = (pair.get("liquidity") or {}).get("usd", 0) or 0
    vol24 = (pair.get("volume") or {}).get("h24", 0) or 0
    txns24 = pair.get("txns", {}).get("h24", {}) or {}
    total_txns = (txns24.get("buys", 0) or 0) + (txns24.get("sells", 0) or 0)
    mcap = pair.get("marketCap") or pair.get("fdv") or 0
    created_at = pair.get("pairCreatedAt")

    if not created_at:
        return False
    age_days = (time.time() * 1000 - created_at) / (1000 * 60 * 60 * 24)

    if not (MIN_PAIR_AGE_DAYS <= age_days <= MAX_PAIR_AGE_DAYS):
        return False
    if liq < MIN_LIQUIDITY_USD:
        return False
    if vol24 < MIN_VOLUME_24H_USD:
        return False
    if total_txns < MIN_TXNS_24H:
        return False
    if not (MIN_MARKET_CAP <= mcap <= MAX_MARKET_CAP):
        return False
    if mcap > 0 and (liq / mcap) < MIN_LIQ_MCAP_RATIO:
        return False
    return True


def opportunity_score(pair):
    change24 = (pair.get("priceChange") or {}).get("h24", 0) or 0
    change6 = (pair.get("priceChange") or {}).get("h6", 0) or 0
    vol24 = (pair.get("volume") or {}).get("h24", 0) or 0
    vol6 = (pair.get("volume") or {}).get("h6", 0) or 0

    score = 0
    reasons = []
    if 0 < change24 < 80:
        score += 1
        reasons.append(f"harga +{change24:.1f}% (24 jam), belum parabolik")
    if change6 > 0:
        score += 1
        reasons.append("momentum 6 jam terakhir positif")
    if vol24 > 0 and vol6 > 0 and (vol6 * 4) > vol24 * 1.2:
        score += 1
        reasons.append("volume jam terakhir naik lebih cepat dari rata-rata")
    return score, reasons


def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum diset. Pesan tidak dikirim.")
        print(message)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }, timeout=15)
    if resp.status_code != 200:
        print("Gagal kirim ke Telegram:", resp.status_code, resp.text)
