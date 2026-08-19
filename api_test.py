import os
import requests

API_KEY = os.environ.get("API_KEYS_POOL", "").split(",")[0].strip()

if not API_KEY:
    raise RuntimeError("API_KEYS_POOL is missing")

BASE_URL = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": API_KEY
}


def test_api(name, endpoint):
    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)
    print("Endpoint:", endpoint)

    try:
        r = requests.get(
            f"{BASE_URL}/{endpoint}",
            headers=headers,
            timeout=20
        )

        data = r.json()

        print("HTTP Status:", r.status_code)
        print("Results:", data.get("results"))
        print("Errors:", data.get("errors"))
        print("Paging:", data.get("paging"))

        if data.get("response"):
            print("✅ DATA RECEIVED")

            # ပထမဆုံး fixture ၂ ခုလောက်ပဲ ပြမယ်
            for item in data["response"][:2]:
                fixture = item.get("fixture", {})
                teams = item.get("teams", {})
                goals = item.get("goals", {})

                print(
                    fixture.get("date"),
                    "|",
                    teams.get("home", {}).get("name"),
                    "vs",
                    teams.get("away", {}).get("name"),
                    "|",
                    goals.get("home"),
                    "-",
                    goals.get("away")
                )

        else:
            print("❌ NO DATA")

    except Exception as e:
        print("❌ CONNECTION ERROR:", e)


# ============================================================
# TEST 1
# Celtic — Season 2024
# ============================================================

test_api(
    "TEST 1 — CELTIC SEASON 2024",
    "fixtures?team=247&season=2024"
)


# ============================================================
# TEST 2
# Celtic — Season 2024 + Date Range
# ============================================================

test_api(
    "TEST 2 — CELTIC 2024 DATE RANGE",
    "fixtures?team=247&season=2024&from=2024-01-01&to=2024-12-31"
)


# ============================================================
# TEST 3
# Celtic vs LASK — H2H
# ============================================================

test_api(
    "TEST 3 — CELTIC vs LASK H2H",
    "fixtures/headtohead?h2h=247-1026"
)
