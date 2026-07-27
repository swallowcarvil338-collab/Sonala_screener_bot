"""
Weekly Recap
------------
Runs once a week. Reads data/flagged_tokens.json, looks at tokens flagged in
the last 7 days, checks their current price, and sends a performance recap
to Telegram (gain/loss since being flagged).

IMPORTANT: Past performance in this recap does not predict future results.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone

from screener_common import get_best_pair, send_telegram, REQUEST_DELAY_SEC

LOG_PATH = os.path.join(os.path.dirname(__file__), "data", "flagged_tokens.json")


def load_flagged():
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def format_recap(results):
    if not results:
        return "📊 *Recap Mingguan*\n\nTidak ada token yang direkomendasikan minggu ini."

    gains = [r["change_pct"] for r in results if r["change_pct"] is not None]
    avg = sum(gains) / len(gains) if gains else 0
    winners = len([g for g in gains if g > 0])
    losers = len([g for g in gains if g <= 0])

    lines = [
        "📊 *Recap Mingguan*",
        f"Total token direkomendasikan minggu ini: *{len(results)}*",
        f"Naik: {winners} | Turun/Stagnan: {losers} | Rata-rata: {avg:+.1f}%\n",
    ]
    ranked = sorted(
        results,
        key=lambda x: (x["change_pct"] if x["change_pct"] is not None else -999),
        reverse=True,
    )
    for r in ranked:
        chg = r["change_pct"]
        chg_txt = f"{chg:+.1f}%" if chg is not None else "data tidak tersedia"
        lines.append(f"*{r['symbol']}* — {chg_txt} sejak direkomendasikan ({r['flagged_date']})")
    lines.append("\n_Data historis, bukan jaminan performa ke depan._")
    return "\n".join(lines)


def main():
    flagged = load_flagged()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    recent = [e for e in flagged if e.get("flagged_date", "") >= cutoff]

    print(f"{len(recent)} token direkomendasikan dalam 7 hari terakhir.")
    results = []
    for e in recent:
        pair = get_best_pair(e["address"])
        time.sleep(REQUEST_DELAY_SEC)
        change_pct = None
        if pair:
            current_price = float(pair.get("priceUsd") or 0)
            entry_price = e.get("price_at_flag") or 0
            if entry_price > 0 and current_price > 0:
                change_pct = ((current_price - entry_price) / entry_price) * 100
        results.append({
            "symbol": e.get("symbol", "?"),
            "flagged_date": e.get("flagged_date", "?"),
            "change_pct": change_pct,
        })

    send_telegram(format_recap(results))


if __name__ == "__main__":
    main()
