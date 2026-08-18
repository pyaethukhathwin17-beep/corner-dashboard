from datetime import datetime, timedelta, timezone
import json
import os
import re
import time
import requests

# ============================================================
# API CONFIGURATION (ANTI-BAN PROTECTED)
# ============================================================
API_KEY = os.getenv(
    "API_KEY", "e243943e4a085a7f6c3c58bf85a8b3d3"
).strip().lower()

MMT_TIMEZONE = timezone(timedelta(hours=6, minutes=30))
today_str = datetime.now(MMT_TIMEZONE).strftime("%Y-%m-%d")

# ============================================================
# LEAGUE WHITELIST & BLACKLIST
# ============================================================
ALLOWED_CONFIG = {
    "england": ["premier league", "championship"],
    "spain": ["la liga", "segunda division", "laliga 2"],
    "france": ["ligue 1", "ligue 2"],
    "germany": ["bundesliga", "2. bundesliga"],
    "italy": ["serie a", "serie b"],
    "argentina": ["liga profesional", "primera division"],
    "australia": ["a-league"],
    "austria": ["bundesliga"],
    "belgium": ["pro league", "first division a"],
    "brazil": ["serie a"],
    "chile": ["primera division"],
    "china": ["super league"],
    "colombia": ["primera a"],
    "croatia": ["hnl", "1. hnl"],
    "denmark": ["superliga"],
    "ecuador": ["liga pro"],
    "greece": ["super league"],
    "japan": ["j1 league"],
    "mexico": ["liga mx"],
    "netherlands": ["eredivisie"],
    "norway": ["eliteserien"],
    "peru": ["liga 1"],
    "poland": ["ekstraklasa"],
    "portugal": ["primeira liga", "liga portugal"],
    "saudi arabia": ["saudi pro league", "pro league"],
    "scotland": ["premiership", "scottish premiership"],
    "sweden": ["allsvenskan"],
    "switzerland": ["super league"],
    "turkey": ["super lig", "süper lig"],
    "usa": ["major league soccer"],
    "world": [
        "uefa champions league",
        "uefa europa league",
        "uefa conference league",
        "uefa nations league",
        "copa libertadores",
        "copa sudamericana",
    ],
}

BLACKLIST_WORDS = [
    "next pro",
    "mls next",
    "pro league 2",
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
    if "major league soccer" in l_low or l_low == "mls":
        return True
    for c_key, valid_leagues in ALLOWED_CONFIG.items():
        if c_key in c_low or c_key in l_low:
            if any(vl in l_low for vl in valid_leagues):
                return True
    for wl in ALLOWED_CONFIG["world"]:
        if wl in l_low:
            return True
    return False


# ============================================================
# API FETCH ENGINE (RATE-LIMITED)
# ============================================================
def fetch_api(endpoint):
    url = f"https://v3.football.api-sports.io/{endpoint}"
    headers = {"x-apisports-key": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        return data.get("response", [])
    except Exception as e:
        print(f"Error fetching {endpoint}: {e}")
        return []


def get_l5(team_id, venue):
    fixtures = fetch_api(f"fixtures?team={team_id}&last=30&status=FT")
    selected = []
    for f in fixtures:
        if venue == "HOME" and f["teams"]["home"]["id"] == team_id:
            selected.append(f)
        elif venue == "AWAY" and f["teams"]["away"]["id"] == team_id:
            selected.append(f)
        if len(selected) == 5:
            break
    if len(selected) < 5:
        return None

    over_cnt = 0
    btts_cnt = 0
    gf_tot = 0
    ga_tot = 0
    scorelines = []

    for f in selected:
        gh = f["goals"]["home"] or 0
        ga = f["goals"]["away"] or 0
        tot = gh + ga
        if tot >= 3:
            over_cnt += 1
        if gh > 0 and ga > 0:
            btts_cnt += 1
        gf = gh if venue == "HOME" else ga
        ga_val = ga if venue == "HOME" else gh
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

    return {
        "over_pct": int((over_cnt / 5.0) * 100),
        "under_pct": int(((5 - over_cnt) / 5.0) * 100),
        "btts_pct": int((btts_cnt / 5.0) * 100),
        "gf_avg": round(gf_tot / 5.0, 2),
        "ga_avg": round(ga_tot / 5.0, 2),
        "scorelines": scorelines,
    }


# ============================================================
# MAIN EXECUTION
# ============================================================
print(f"[{today_str}] Fetching Today's Fixtures...")
raw_fixtures = fetch_api(f"fixtures?date={today_str}&timezone=Asia/Yangon")
time.sleep(6.5)

allowed_fixtures = [
    f
    for f in raw_fixtures
    if is_allowed(
        f["league"]["name"],
        f["league"].get("country", ""),
        f["teams"]["home"]["name"],
        f["teams"]["away"]["name"],
    )
]

# Daily Quota Cap (အများဆုံး ၄၀ ပွဲသာ ကန့်သတ်ယူပြီး နေ့စဉ် ၁၀၀ Limit မပြည့်စေရန် ထိန်းခြင်း)
allowed_fixtures = allowed_fixtures[:40]
print(f"Processing {len(allowed_fixtures)} Whitelist Fixtures...")

evaluated_matches = []
for idx, fix in enumerate(allowed_fixtures):
    h_id = fix["teams"]["home"]["id"]
    a_id = fix["teams"]["away"]["id"]
    h_name = fix["teams"]["home"]["name"]
    a_name = fix["teams"]["away"]["name"]

    print(
        f"Evaluating ({idx+1}/{len(allowed_fixtures)}): {h_name} vs {a_name}..."
    )

    h_stats = get_l5(h_id, "HOME")
    time.sleep(6.5)  # 6.5s delay to keep under 10 req/min

    a_stats = get_l5(a_id, "AWAY")
    time.sleep(6.5)

    if not h_stats or not a_stats:
        continue

    # Strict Criteria
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

    evaluated_matches.append({
        "fixture_id": fix["fixture"]["id"],
        "league": fix["league"]["name"],
        "country": fix["league"].get("country", ""),
        "home": h_name,
        "away": a_name,
        "time": fix["fixture"]["date"][11:16],
        "status": fix["fixture"]["status"]["short"],
        "score_h": fix["goals"]["home"],
        "score_a": fix["goals"]["away"],
        "signal": signal,
        "prob": over_prob,
        "edge": over_edge,
        "h_stats": h_stats,
        "a_stats": a_stats,
    })

# Save to JSON
with open("matches_data.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "updated_at": today_str,
            "total_matches": len(evaluated_matches),
            "matches": evaluated_matches,
        },
        f,
        indent=2,
        ensure_ascii=False,
    )

print(f"Done! Successfully generated matches_data.json with {len(evaluated_matches)} matches.")
