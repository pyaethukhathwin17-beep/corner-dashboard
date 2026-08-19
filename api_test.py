import os
import requests
from datetime import datetime

API_KEY = os.environ.get("API_KEYS_POOL", "").split(",")[0].strip()

if not API_KEY:
    raise RuntimeError("API_KEYS_POOL is missing")

URL = "https://v3.football.api-sports.io/fixtures"

params = {
    "team": 247,
    "season": 2024,
}

headers = {
    "x-apisports-key": API_KEY
}

print("=" * 70)
print("Celtic 2024 → LOCAL L5 HOME/AWAY TEST")
print("=" * 70)

response = requests.get(
    URL,
    headers=headers,
    params=params,
    timeout=30
)

data = response.json()

print("HTTP Status:", response.status_code)
print("Results:", data.get("results"))
print("Errors:", data.get("errors"))

fixtures = data.get("response", [])

finished = []

for f in fixtures:

    status = f.get("fixture", {}).get("status", {}).get("short")

    if status not in ["FT", "AET", "PEN"]:
        continue

    date = f.get("fixture", {}).get("date")

    home_id = f.get("teams", {}).get("home", {}).get("id")
    away_id = f.get("teams", {}).get("away", {}).get("id")

    goals_home = f.get("goals", {}).get("home")
    goals_away = f.get("goals", {}).get("away")

    if goals_home is None or goals_away is None:
        continue

    finished.append({
        "date": date,
        "home_id": home_id,
        "away_id": away_id,
        "home": f["teams"]["home"]["name"],
        "away": f["teams"]["away"]["name"],
        "gh": goals_home,
        "ga": goals_away,
    })

# Newest first
finished.sort(
    key=lambda x: x["date"],
    reverse=True
)

# ------------------------------------------------------------
# CELTIC HOME
# ------------------------------------------------------------

celtic_home = [
    f for f in finished
    if f["home_id"] == 247
][:5]

# ------------------------------------------------------------
# CELTIC AWAY
# ------------------------------------------------------------

celtic_away = [
    f for f in finished
    if f["away_id"] == 247
][:5]


def print_matches(title, matches):

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    if not matches:
        print("NO DATA")
        return

    for i, m in enumerate(matches, 1):

        total = m["gh"] + m["ga"]

        print(
            f"{i}. "
            f"{m['date'][:10]} | "
            f"{m['home']} "
            f"{m['gh']} - {m['ga']} "
            f"{m['away']} | "
            f"Total Goals: {total}"
        )


print_matches(
    "🏠 CELTIC LAST 5 HOME",
    celtic_home
)

print_matches(
    "✈️ CELTIC LAST 5 AWAY",
    celtic_away
)

# ------------------------------------------------------------
# BASIC STATS
# ------------------------------------------------------------

def calculate_stats(matches):

    if len(matches) == 0:
        return

    over = 0
    btts = 0
    gf = 0
    ga = 0

    for m in matches:

        total = m["gh"] + m["ga"]

        if total >= 3:
            over += 1

        if m["gh"] > 0 and m["ga"] > 0:
            btts += 1

        if m["home_id"] == 247:
            gf += m["gh"]
            ga += m["ga"]
        else:
            gf += m["ga"]
            ga += m["gh"]

    n = len(matches)

    print("\n" + "-" * 70)
    print("STATISTICS")
    print("-" * 70)

    print("Matches :", n)
    print("Over 2.5:", round(over / n * 100, 1), "%")
    print("Under 2.5:", round((n - over) / n * 100, 1), "%")
    print("BTTS:", round(btts / n * 100, 1), "%")
    print("GF Avg:", round(gf / n, 2))
    print("GA Avg:", round(ga / n, 2))


print("\n🏠 HOME STATISTICS")
calculate_stats(celtic_home)

print("\n✈️ AWAY STATISTICS")
calculate_stats(celtic_away)

print("\n" + "=" * 70)
print("✅ TEST COMPLETE")
print("=" * 70)
