from datetime import datetime, timedelta, timezone
import json
import os
import re
import time
import requests

# ============================================================
# 1. SECURE API KEY CONFIGURATION
# ============================================================
# GitHub Secrets (API_KEYS_POOL) မှ Key ကို ဦးစွာ ဖတ်မည်
raw_keys = os.environ.get("API_KEYS_POOL", "")

if raw_keys:
    API_KEYS = [
        k.strip().lower()
        for k in raw_keys.split(",")
        if k.strip() and len(k.strip()) == 32
    ]
else:
    # Secret မတွေ့ပါက လက်ကျန် Key ကို တိုက်ရိုက် သုံးမည်
    API_KEYS = ["1ead03cecd516cf48c41b93c7b15116d"]

current_key_index = 0
print(f"🔑 Active API Key in use: {API_KEYS[0][:8]}***")

# မြန်မာစံတော်ချိန် သတ်မှတ်ချက် (UTC+6:30)
MMT_TZ = timezone(timedelta(hours=6, minutes=30))
now_mmt = datetime.now(MMT_TZ)

# ယနေ့ နေ့လယ် ၁၂:၀၀ PM မှ နောက်နေ့ နေ့လယ် ၁၂:၀၀ PM အထိ (၂၄ နာရီ ဝင်းဒိုး)
window_start = datetime(
    now_mmt.year, now_mmt.month, now_mmt.day, 12, 0, 0, tzinfo=MMT_TZ
)
window_end = window_start + timedelta(days=1)

date_today_str = window_start.strftime("%Y-%m-%d")
date_tomorrow_str = window_end.strftime("%Y-%m-%d")

# ============================================================
# 2. FULL LEAGUE WHITELIST (TOP 5 LEAGUES + 25 NATIONS)
# ============================================================
ALLOWED_CONFIG = {
    "england": ["premier league", "championship"],
    "spain": ["la liga", "segunda division", "laliga 2"],
    "italy": ["serie a", "serie b"],
    "germany": ["bundesliga", "2. bundesliga"],
    "france": ["ligue 1", "ligue 2"],
    "argentina": ["liga profesional"],
    "australia": ["a-league"],
    "austria": ["bundesliga"],
    "belgium": ["pro league"],
    "brazil": ["serie a"],
    "chile": ["primera division", "primera división"],
    "china": ["super league"],
    "colombia": ["primera a"],
    "croatia": ["hnl"],
    "denmark": ["superliga"],
    "ecuador": ["liga pro"],
    "greece": ["super league"],
    "japan": ["j1 league"],
    "mexico": ["liga mx"],
    "netherlands": ["eredivisie"],
    "norway": ["eliteserien"],
    "peru": ["liga 1"],
    "poland": ["ekstraklasa"],
    "portugal": ["primeira liga"],
    "saudi arabia": ["saudi pro league", "pro league"],
    "scotland": ["premiership"],
    "sweden": ["allsvenskan"],
    "switzerland": ["super league"],
    "turkey": ["super lig", "süper lig"],
    "usa": ["mls", "major league soccer"],
}

BLACKLIST_WORDS = [
    "next pro",
    "mls next",
    "pro league 2",
    "challenger",
    "u14",
    "u15",
    "u16",
    "u17",
    "u18",
    "u19",
    "u20",
    "u21",
    "u22",
    "u23",
    "under-17",
    "under-18",
    "under-19",
    "under-21",
    "reserve",
    "reserves",
    "youth",
    "women",
    "fem",
    "amateur",
    "academy",
    "premier league 2",
    "eerste divisie",
    "liga portugal 2",
    "superettan",
    "j2 league",
    "j3 league",
    "russia",
    "russian",
]


def is_allowed(league_name, country_name, home_name, away_name):
    combined = f"{league_name} {country_name} {home_name} {away_name}".lower()
    if any(b in combined for b in BLACKLIST_WORDS):
        return False
    if re.search(r"\b(ii|iii|b|c|u\s?-?\d{2})\b", home_name.lower()) or re.search(
        r"\b(ii|iii|b|c|u\s?-?\d{2})\b", away_name.lower()
    ):
        return False
    l_low = league_name.lower()
    c_low = country_name.lower() if country_name else ""
    if "mls" in l_low or "major league soccer" in l_low:
        return True
    for c_key, valid_leagues in ALLOWED_CONFIG.items():
        if c_key in c_low or c_key in l_low:
            if any(vl in l_low for vl in valid_leagues):
                return True
    return False


# ============================================================
# 3. API FETCH ENGINE
# ============================================================
def fetch_api(endpoint):
    url = f"https://v3.football.api-sports.io/{endpoint}"
    active_key = API_KEYS[0]
    headers = {"x-apisports-key": active_key}

    try:
        res = requests.get(url, headers=headers, timeout=20)
        data = res.json()
        errors = data.get("errors", {})
        if errors:
            print(f"⚠️ API Response Error: {errors}")
            return []
        return data.get("response", [])
    except Exception as e:
        print(f"Connection Error on {endpoint}: {e}")
        return []


def get_l5(team_id, venue, team_name=""):
    fixtures = fetch_api(f"fixtures?team={team_id}&last=15")

    past_matches = [
        f
        for f in fixtures
        if f.get("fixture", {}).get("status", {}).get("short")
        in ["FT", "AET", "PEN"]
    ]

    selected = [
        f
        for f in past_matches
        if (venue == "HOME" and f["teams"]["home"]["id"] == team_id)
        or (venue == "AWAY" and f["teams"]["away"]["id"] == team_id)
    ]

    if len(selected) < 3:
        selected = past_matches[:5]
    else:
        selected = selected[:5]

    print(f"   └─ {team_name} ({venue}): Found {len(selected)} matches.")

    if not selected:
        return {
            "over_pct": 50,
            "under_pct": 50,
            "btts_pct": 50,
            "gf_avg": 1.0,
            "ga_avg": 1.0,
            "scorelines": [],
        }

    over_cnt, btts_cnt, gf_tot, ga_tot = 0, 0, 0, 0
    scorelines = []

    for f in selected:
        gh = (
            f["goals"]["home"]
            if f.get("goals") and f["goals"]["home"] is not None
            else 0
        )
        ga = (
            f["goals"]["away"]
            if f.get("goals") and f["goals"]["away"] is not None
            else 0
        )
        tot = gh + ga

        if tot >= 3:
            over_cnt += 1
        if gh > 0 and ga > 0:
            btts_cnt += 1

        is_h = f["teams"]["home"]["id"] == team_id
        gf = gh if is_h else ga
        ga_val = ga if is_h else gh
        gf_tot += gf
        ga_tot += ga_val

        scorelines.append({
            "date": f["fixture"]["date"][:10],
            "home": f["teams"]["home"]["name"],
            "away": f["teams"]["away"]["name"],
            "gh": gh,
            "ga": ga,
            "tot": tot,
        })

    n = len(selected)
    return {
        "over_pct": int((over_cnt / n) * 100),
        "under_pct": int(((n - over_cnt) / n) * 100),
        "btts_pct": int((btts_cnt / n) * 100),
        "gf_avg": round(gf_tot / n, 2),
        "ga_avg": round(ga_tot / n, 2),
        "scorelines": scorelines,
    }


# ============================================================
# 4. MAIN FETCH (12:00 PM TO NEXT DAY 12:00 PM MMT)
# ============================================================
print(
    f"Fetching fixtures from {window_start.strftime('%Y-%m-%d %I:%M %p')} MMT"
    f" to {window_end.strftime('%Y-%m-%d %I:%M %p')} MMT..."
)

raw_1 = fetch_api(f"fixtures?date={date_today_str}&timezone=Asia/Yangon")
time.sleep(7)
raw_2 = fetch_api(f"fixtures?date={date_tomorrow_str}&timezone=Asia/Yangon")
time.sleep(7)

combined_fixtures = raw_1 + raw_2
seen_ids = set()
upcoming_fixtures = []

for f in combined_fixtures:
    f_id = f["fixture"]["id"]
    if f_id in seen_ids:
        continue
    seen_ids.add(f_id)

    status_short = f["fixture"]["status"]["short"]
    if status_short not in ["NS", "TBD"]:
        continue

    f_time_str = f["fixture"]["date"]
    f_dt = datetime.fromisoformat(f_time_str)

    if window_start <= f_dt <= window_end:
        if is_allowed(
            f["league"]["name"],
            f["league"].get("country", ""),
            f["teams"]["home"]["name"],
            f["teams"]["away"]["name"],
        ):
            upcoming_fixtures.append(f)

# Single Key ဖြစ်၍ Quota ကာကွယ်ရန် ပွဲစဉ် ၃၀ အထိ ကန့်သတ်ထားသည်
upcoming_fixtures = upcoming_fixtures[:30]
print(f"Total Fixtures to Process: {len(upcoming_fixtures)}")

evaluated_matches = []
for idx, fix in enumerate(upcoming_fixtures):
    h_id = fix["teams"]["home"]["id"]
    a_id = fix["teams"]["away"]["id"]
    h_name = fix["teams"]["home"]["name"]
    a_name = fix["teams"]["away"]["name"]

    print(
        f"Evaluating ({idx+1}/{len(upcoming_fixtures)}): {h_name} vs {a_name}..."
    )

    h_stats = get_l5(h_id, "HOME", h_name)
    time.sleep(7)

    a_stats = get_l5(a_id, "AWAY", a_name)
    time.sleep(7)

    # 5-Star Target Rule
    is_over = (
        h_stats["over_pct"] >= 60
        and a_stats["over_pct"] >= 60
        and h_stats["btts_pct"] >= 60
        and a_stats["btts_pct"] >= 60
        and h_stats["gf_avg"] > 1.5
        and h_stats["ga_avg"] > 1.0
        and a_stats["gf_avg"] > 1.0
        and a_stats["ga_avg"] > 1.0
    )

    is_under = (
        h_stats["under_pct"] >= 60
        and a_stats["under_pct"] >= 60
        and h_stats["btts_pct"] <= 50
        and a_stats["btts_pct"] <= 50
        and h_stats["gf_avg"] < 1.3
        and h_stats["ga_avg"] < 1.0
        and a_stats["gf_avg"] < 1.1
        and a_stats["ga_avg"] < 1.2
    )

    over_prob = round(
        ((h_stats["over_pct"] + a_stats["over_pct"]) / 2 * 0.40)
        + ((h_stats["btts_pct"] + a_stats["btts_pct"]) / 2 * 0.20)
        + (min(100, (h_stats["gf_avg"] + a_stats["gf_avg"]) / 4.0 * 100) * 0.20)
        + (min(100, (h_stats["ga_avg"] + a_stats["ga_avg"]) / 3.2 * 100) * 0.20),
        1,
    )
    over_edge = round(over_prob - 60, 1)

    signal = (
        "OVER_2_5"
        if (is_over and over_edge >= 5)
        else "UNDER_2_5"
        if is_under
        else "NEUTRAL"
    )

    f_date_display = fix["fixture"]["date"][:10]
    f_time_display = fix["fixture"]["date"][11:16]

    evaluated_matches.append({
        "fixture_id": fix["fixture"]["id"],
        "league": fix["league"]["name"],
        "country": fix["league"].get("country", ""),
        "home": h_name,
        "away": a_name,
        "date": f_date_display,
        "time": f_time_display,
        "status": fix["fixture"]["status"]["short"],
        "signal": signal,
        "prob": over_prob,
        "edge": over_edge,
        "h_stats": h_stats,
        "a_stats": a_stats,
    })

# 5 Star ပွဲများကို ထိပ်ဆုံးသို့ စီစဉ်ခြင်း
evaluated_matches.sort(
    key=lambda x: (
        0
        if x["signal"] == "OVER_2_5"
        else 1
        if x["signal"] == "UNDER_2_5"
        else 2,
        x["time"],
    )
)

with open("matches_data.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "window_range": (
                f"{window_start.strftime('%d %b %I:%M %p')} - "
                f"{window_end.strftime('%d %b %I:%M %p')} MMT"
            ),
            "total_matches": len(evaluated_matches),
            "matches": evaluated_matches,
        },
        f,
        indent=2,
        ensure_ascii=False,
    )

print(
    f"Done! Successfully evaluated {len(evaluated_matches)} upcoming matches."
)
