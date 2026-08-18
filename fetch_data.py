from datetime import datetime, timedelta, timezone
import json
import os
import re
import time
import requests

# ============================================================
# 1. MULTI-API KEYS CONFIGURATION (KEY ROTATION)
# ============================================================
API_KEYS = [
    "e243943e4a085a7f6c3c58bf85a8b3d3",  # Key 1
    "1ead03cecd516cf48c41b93c7b15116d",  # Key 2
]
current_key_index = 0

MMT_TIMEZONE = timezone(timedelta(hours=6, minutes=30))
today_str = datetime.now(MMT_TIMEZONE).strftime("%Y-%m-%d")

# ============================================================
# 2. FULL WHITELIST LEAGUES (TOP 5 LEAGUES + 25 NATIONS)
# ============================================================
ALLOWED_CONFIG = {
    # Top 5 European Leagues (Tier 1 & Tier 2)
    "england": ["premier league", "championship"],
    "spain": ["la liga", "segunda division", "laliga 2"],
    "italy": ["serie a", "serie b"],
    "germany": ["bundesliga", "2. bundesliga"],
    "france": ["ligue 1", "ligue 2"],
    # Original 25 Leagues
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
# 3. API FETCH ENGINE WITH AUTO-ROTATION
# ============================================================
def get_current_key():
    global current_key_index
    return API_KEYS[current_key_index % len(API_KEYS)]


def rotate_key():
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"🔄 Switched to API Key: {get_current_key()[:8]}***")


def fetch_api(endpoint):
    url = f"https://v3.football.api-sports.io/{endpoint}"

    for _ in range(len(API_KEYS)):
        active_key = get_current_key()
        headers = {"x-apisports-key": active_key}
        try:
            res = requests.get(url, headers=headers, timeout=15)
            data = res.json()

            errors = data.get("errors", {})
            if errors and (
                isinstance(errors, dict)
                and any("requests" in str(v).lower() for v in errors.values())
            ):
                print(f"⚠️ Limit reached for key {active_key[:8]}... Rotating.")
                rotate_key()
                continue

            return data.get("response", [])
        except Exception as e:
            print(f"Error fetching {endpoint}: {e}")
            rotate_key()

    return []


def get_l5(team_id, venue):
    fixtures = fetch_api(f"fixtures?team={team_id}&last=20&status=FT")
    selected = [
        f
        for f in fixtures
        if (venue == "HOME" and f["teams"]["home"]["id"] == team_id)
        or (venue == "AWAY" and f["teams"]["away"]["id"] == team_id)
    ]

    # Fallback: ရာသီအစပိုင်း ၃ ပွဲမပြည့်ပါက အရင်နှစ်အပါအဝင် နောက်ဆုံး ၅ ပွဲကို ယူမည်
    if len(selected) < 3:
        selected = fixtures[:5]
    else:
        selected = selected[:5]

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
        gh = f["goals"]["home"] or 0
        ga = f["goals"]["away"] or 0
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
# 4. MAIN EXECUTION
# ============================================================
print(
    f"[{today_str}] Fetching Today's Fixtures (Total Keys Available: {len(API_KEYS)})..."
)
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

# Key ၂ ခုဖြင့် ၂၀၀ Calls ရရှိသဖြင့် ပွဲစဉ် ၆၀ အထိ ဆွဲယူခွင့်ပြုထားသည်
max_matches = 60
allowed_fixtures = allowed_fixtures[:max_matches]
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
    time.sleep(6.5)

    a_stats = get_l5(a_id, "AWAY")
    time.sleep(6.5)

    # 5-Star Rule Conditions
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

# Save Output
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

print(f"Done! Successfully evaluated {len(evaluated_matches)} matches.")
