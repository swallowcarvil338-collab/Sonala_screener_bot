"""
Daily Solana Screener
----------------------
Runs once a day. Finds newly-listed Solana tokens that pass strict safety
filters and haven't been flagged before, sends an immediate Telegram alert
for each, and logs them to data/flagged_tokens.json so weekly_recap.py can
report on their performance later.

IMPORTANT: This is a research shortlist only, NOT a buy signal or financial
advice.
"""

import json
import os
import time
from datetime import datetime, timezone

from screener_common import (
    get_latest_solana_token_addresses,
    get_best_pair,
    passes_safety_filters,
    opportunity_score,
    send_telegram,
    REQUEST_DELAY_SEC,
)

LOG_PATH = os.path.join(os.path.dirname(__file__), "data", "flagged_tokens.json")


def load_flagged():
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_flagged(entries):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2)


def format_alert(pair, reasons):
    symbol = (pair.get("baseToken") or {}).get("symbol", "?")
    url = pair.get("url", "")
    liq = (pair.get("liquidity") or {}).get("usd", 0) or 0
    vol = (pair.get("volume") or {}).get("h24", 0) or 0
    mcap = pair.get("marketCap") or pair.get("fdv") or 0
    chg = (pair.get("priceChange") or {}).get("h24", 0) or 0
    reason_txt = "; ".join(reasons) if reasons else "lolos filter keamanan dasar"
    return (
        f"🆕 *Token Baru Lolos Filter*\n\n"
        f"*{symbol}* ({chg:+.1f}% / 24h)\n"
        f"Liq: ${liq:,.0f} | Vol 24h: ${vol:,.0f} | MCap: ${mcap:,.0f}\n"
        f"Alasan: {reason_txt}\n"
        f"{url}\n\n"
        f"_Shortlist riset — bukan sinyal beli._"
    )


def main():
    flagged = load_flagged()
    flagged_addresses = {e["address"] for e in flagged}

    print("Mengambil daftar token Solana terbaru dari DexScreener...")
    addresses = get_latest_solana_token_addresses()
    print(f"Ditemukan {len(addresses)} token profile baru (semua chain, difilter ke Solana).")

    new_flags = 0
    for addr in addresses:
        if addr in flagged_addresses:
            continue
        pair = get_best_pair(addr)
        time.sleep(REQUEST_DELAY_SEC)
        if not pair:
            continue
        if not passes_safety_filters(pair):
            continue

        score, reasons = opportunity_score(pair)
        if score == 0:
            continue  # lolos filter keamanan tapi belum ada sinyal momentum

        price = float(pair.get("priceUsd") or 0)
        entry = {
            "address": addr,
            "symbol": (pair.get("baseToken") or {}).get("symbol", "?"),
            "flagged_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "price_at_flag": price,
            "liquidity_at_flag": (pair.get("liquidity") or {}).get("usd", 0) or 0,
            "url": pair.get("url", ""),
        }
        flagged.append(entry)
        flagged_addresses.add(addr)
        new_flags += 1

        send_telegram(format_alert(pair, reasons))
        time.sleep(1)

    save_flagged(flagged)
    print(f"{new_flags} token baru direkomendasikan hari ini. Total log sepanjang waktu: {len(flagged)}.")

    if new_flags == 0:
        send_telegram(
            f"✅ Screening harian selesai — belum ada token yang lolos filter ketat hari ini.\n"
            f"_(Dicek: {len(addresses)} token profile baru)_"
        )


if __name__ == "__main__":
    main()
        
