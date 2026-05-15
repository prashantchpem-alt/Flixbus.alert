import requests
import os
from datetime import datetime

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
TRAVEL_DATE = "2026-06-06"

URL = (
    "https://global.api.flixbus.com/search/service/v4/search"
    "?from_city_id=953&to_city_id=4655"
    f"&departure_date={TRAVEL_DATE}"
    "&pax=1&currency=INR&locale=en_IN&search_by=cities&include_after_midnight_rides=1"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "x-brand": "flixbus"
}

def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    )

def check_prices():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        data = r.json()
        trips = data.get("trips", [])

        if not trips:
            send_telegram("⚠️ FlixBus: No trips found for Delhi→Shimla on 6 June 2026.")
            return

        buses = []
        for trip in trips:
            for result in trip.get("results", {}).values():
                try:
                    departure = result["departure"]["date"]
                    arrival   = result["arrival"]["date"]
                    price     = result["price"]["total"]
                    status    = result.get("status", "available")

                    dep_time = datetime.fromisoformat(departure).strftime("%I:%M %p")
                    arr_time = datetime.fromisoformat(arrival).strftime("%I:%M %p")

                    buses.append({
                        "dep": dep_time,
                        "arr": arr_time,
                        "price": price,
                        "status": status
                    })
                except (KeyError, ValueError):
                    continue

        if not buses:
            send_telegram("⚠️ FlixBus: Could not parse any bus data. API may have changed.")
            return

        buses.sort(key=lambda x: x["dep"])

        today = datetime.now().strftime("%d %b %Y")
        lines = [
            f"🚌 <b>FlixBus: Delhi → Shimla</b>",
            f"📅 Travel Date: <b>6 June 2026</b>",
            f"🕖 Daily update — {today} 7:00 AM\n",
        ]

        for b in buses:
            if b["status"] != "available":
                flag = "🔴"
            elif b["price"] < 1000:
                flag = "🟢"
            else:
                flag = "🟡"
            lines.append(
                f"{flag} <b>{b['dep']}</b> → {b['arr']}   ₹<b>{b['price']}</b>  ({b['status']})"
            )

        min_price = min(b["price"] for b in buses)
        lines.append(f"\n💰 Lowest fare: <b>₹{min_price}</b>")

        if min_price < 1000:
            lines.append("🚨 <b>PRICE BELOW ₹1000 — Book now!</b>")

        lines.append("\n👉 <a href='https://www.flixbus.in'>Open FlixBus.in</a>")

        send_telegram("\n".join(lines))

    except Exception as e:
        send_telegram(f"❌ Error: {str(e)}")

check_prices()
