from datetime import datetime, timedelta, timezone
import json
import os
import re
import time
import requests


# ============================================================
# 1. API KEY CONFIGURATION
# ============================================================

raw_keys = os.environ.get("API_KEYS_POOL", "")

if raw_keys:
    API_KEYS = [
        k.strip()
        for k in raw_keys.split(",")
        if k.strip() and len(k.strip()) == 32
    ]
else:
    # TEST ONLY
    API_KEYS = ["1ead03cecd516cf48c41b93c7b15116d"]

if not API_KEYS:
    raise RuntimeError("❌ No valid API key found.")

current_key_index = 0

print("=" * 70)
print("🔑 API CONFIGURATION")
print("=" * 70)
print(f"Total API Keys Loaded : {len(API_KEYS)}")
print(f"Active API Key        : {API_KEYS[0][:8]}***")
print("=" * 70)


# ============================================================
# 2. MYANMAR TIMEZONE
# ============================================================

MMT_TZ = timezone(timedelta(hours=6, minutes=30))

now_mmt = datetime.now(MMT_TZ)

# Today 12:00 PM
window_start = datetime(
    now_mmt.year,
    now_mmt.month,
    now_mmt.day,
    12,
    0,
    0,
    tzinfo=MMT_TZ
)

# Tomorrow 12:00 PM
window_end = window_start + timedelta(days=1)

date_today_str = window_start.strftime("%Y-%m-%d")
date_tomorrow_str = window_end.strftime("%Y-%m-%d")


# ============================================================
# 3. TEST MODE
# ============================================================

# IMPORTANT:
# Only UEFA Champions League
TEST_LEAGUE = "champions league"

# Maximum matches to evaluate
MAX_MATCHES = 5

# Delay between API calls
# Free API plan protection
API_DELAY = 7


# ============================================================
# 4. CHAMPIONS LEAGUE FILTER
# ============================================================

def is_champions_league(league_name, country_name, home_name, away_name):

    league = (league_name or "").lower().strip()
    country = (country_name or "").lower().strip()
    home = (home_name or "").lower().strip()
    away = (away_name or "").lower().strip()

    combined = f"{league} {country} {home} {away}"

    # --------------------------------------------------------
    # BLACKLIST
    # --------------------------------------------------------

    blacklist_words = [
        "women",
        "fem",
        "youth",
        "academy",
        "reserve",
        "reserves",
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
    ]

    if any(word in combined for word in blacklist_words):
        return False

    # --------------------------------------------------------
    # TEAM NAME RESERVE / B / C CHECK
    # --------------------------------------------------------

    if re.search(
        r"\b(ii|iii|b|c|u\s?-?\d{2})\b",
        home
    ):
        return False

    if re.search(
        r"\b(ii|iii|b|c|u\s?-?\d{2})\b",
        away
    ):
        return False

    # --------------------------------------------------------
    # CHAMPIONS LEAGUE ONLY
    # --------------------------------------------------------

    champions_keywords = [
        "uefa champions league",
        "champions league",
    ]

    return any(keyword in league for keyword in champions_keywords)


# ============================================================
# 5. API FETCH ENGINE
# ============================================================

def fetch_api(endpoint):

    global current_key_index

    url = f"https://v3.football.api-sports.io/{endpoint}"

    active_key = API_KEYS[current_key_index]

    headers = {
        "x-apisports-key": active_key,
        "Accept": "application/json",
    }

    print()
    print("------------------------------------------------------------")
    print("🌐 API REQUEST")
    print("------------------------------------------------------------")
    print(f"Endpoint : {endpoint}")
    print(f"Key      : {active_key[:8]}***")

    try:

        res = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        print(f"HTTP Status : {res.status_code}")

        # ----------------------------------------------------
        # Try JSON
        # ----------------------------------------------------

        try:
            data = res.json()
        except ValueError:

            print("❌ API returned invalid JSON.")
            print("Raw response:")
            print(res.text[:500])

            return []

        # ----------------------------------------------------
        # API Errors
        # ----------------------------------------------------

        errors = data.get("errors", {})
        results = data.get("results", 0)
        response = data.get("response", [])

        print(f"API Results : {results}")
        print(f"API Errors  : {errors}")
        print(f"Response    : {len(response)} items")

        # ----------------------------------------------------
        # HTTP ERROR
        # ----------------------------------------------------

        if res.status_code != 200:

            print("❌ HTTP ERROR")

            # If rate limited, rotate key
            if res.status_code == 429:

                print("⚠️ RATE LIMIT DETECTED")

                if len(API_KEYS) > 1:

                    current_key_index = (
                        current_key_index + 1
                    ) % len(API_KEYS)

                    print(
                        "🔄 Switching API key to:",
                        API_KEYS[current_key_index][:8] + "***"
                    )

                else:

                    print(
                        "⚠️ Only one API key available."
                    )

            return []

        # ----------------------------------------------------
        # API ERROR OBJECT
        # ----------------------------------------------------

        if errors:

            print("❌ API ERROR:", errors)

            return []

        # ----------------------------------------------------
        # EMPTY RESPONSE
        # ----------------------------------------------------

        if not response:

            print("⚠️ API returned ZERO data.")

            return []

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        print("✅ API DATA RECEIVED")

        return response

    except requests.exceptions.Timeout:

        print("❌ API REQUEST TIMEOUT")

        return []

    except requests.exceptions.ConnectionError:

        print("❌ API CONNECTION ERROR")

        return []

    except requests.exceptions.RequestException as e:

        print("❌ REQUEST ERROR:", e)

        return []

    except Exception as e:

        print("❌ UNKNOWN API ERROR:", e)

        return []


# ============================================================
# 6. GET LAST 5 HOME / AWAY MATCHES
# ============================================================

def get_l5(team_id, venue, team_name=""):

    print()
    print("=" * 60)
    print(f"📊 L5 DATA REQUEST")
    print("=" * 60)
    print(f"Team   : {team_name}")
    print(f"Team ID: {team_id}")
    print(f"Venue  : {venue}")

    fixtures = fetch_api(
        f"fixtures?team={team_id}&last=15"
    )

    # --------------------------------------------------------
    # If API returned no data
    # --------------------------------------------------------

    if not fixtures:

        print(
            f"❌ {team_name}: No fixture data received."
        )

        return {
            "available": False,
            "reason": "API_DATA_UNAVAILABLE",
            "matches_found": 0,
            "over_pct": None,
            "under_pct": None,
            "btts_pct": None,
            "gf_avg": None,
            "ga_avg": None,
            "scorelines": [],
        }

    # --------------------------------------------------------
    # Completed matches only
    # --------------------------------------------------------

    completed_statuses = [
        "FT",
        "AET",
        "PEN"
    ]

    past_matches = [
        f
        for f in fixtures
        if f.get("fixture", {})
        .get("status", {})
        .get("short") in completed_statuses
    ]

    print(
        f"Completed fixtures received: {len(past_matches)}"
    )

    # --------------------------------------------------------
    # Home / Away filtering
    # --------------------------------------------------------

    selected = []

    for f in past_matches:

        home_id = f.get("teams", {}).get(
            "home", {}
        ).get("id")

        away_id = f.get("teams", {}).get(
            "away", {}
        ).get("id")

        if venue == "HOME" and home_id == team_id:
            selected.append(f)

        elif venue == "AWAY" and away_id == team_id:
            selected.append(f)

    # --------------------------------------------------------
    # Take last 5
    # --------------------------------------------------------

    selected = selected[:5]

    print(
        f"Selected {venue} matches: {len(selected)}"
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # DO NOT return fake 50% data.
    # --------------------------------------------------------

    if len(selected) < 5:

        print(
            f"⚠️ WARNING: Only {len(selected)} "
            f"{venue} matches available."
        )

    if not selected:

        print(
            f"❌ No usable {venue} matches."
        )

        return {
            "available": False,
            "reason": "NO_HOME_AWAY_MATCHES",
            "matches_found": 0,
            "over_pct": None,
            "under_pct": None,
            "btts_pct": None,
            "gf_avg": None,
            "ga_avg": None,
            "scorelines": [],
        }

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    over_cnt = 0
    btts_cnt = 0

    gf_tot = 0
    ga_tot = 0

    scorelines = []

    for f in selected:

        goals = f.get("goals", {})

        gh = goals.get("home")

        ga = goals.get("away")

        if gh is None:
            gh = 0

        if ga is None:
            ga = 0

        total_goals = gh + ga

        # Over 2.5
        if total_goals >= 3:
            over_cnt += 1

        # BTTS
        if gh > 0 and ga > 0:
            btts_cnt += 1

        # Team GF / GA
        is_home_team = (
            f["teams"]["home"]["id"] == team_id
        )

        if is_home_team:

            gf = gh
            ga_value = ga

        else:

            gf = ga
            ga_value = gh

        gf_tot += gf
        ga_tot += ga_value

        scorelines.append({
            "date": f["fixture"]["date"][:10],
            "home": f["teams"]["home"]["name"],
            "away": f["teams"]["away"]["name"],
            "gh": gh,
            "ga": ga,
            "total": total_goals,
        })

    n = len(selected)

    over_pct = round(
        (over_cnt / n) * 100
    )

    under_pct = round(
        ((n - over_cnt) / n) * 100
    )

    btts_pct = round(
        (btts_cnt / n) * 100
    )

    gf_avg = round(
        gf_tot / n,
        2
    )

    ga_avg = round(
        ga_tot / n,
        2
    )

    print()
    print("📈 CALCULATED STATS")
    print(f"Over 2.5 : {over_pct}%")
    print(f"Under 2.5: {under_pct}%")
    print(f"BTTS     : {btts_pct}%")
    print(f"GF Avg   : {gf_avg}")
    print(f"GA Avg   : {ga_avg}")

    return {
        "available": True,
        "reason": "OK",
        "matches_found": n,
        "over_pct": over_pct,
        "under_pct": under_pct,
        "btts_pct": btts_pct,
        "gf_avg": gf_avg,
        "ga_avg": ga_avg,
        "scorelines": scorelines,
    }


# ============================================================
# 7. FETCH TODAY + TOMORROW FIXTURES
# ============================================================

print()
print("=" * 70)
print("🏆 CHAMPIONS LEAGUE TEST MODE")
print("=" * 70)

print(
    "Window:"
)

print(
    f"{window_start.strftime('%Y-%m-%d %I:%M %p')} MMT"
)

print(
    "to"
)

print(
    f"{window_end.strftime('%Y-%m-%d %I:%M %p')} MMT"
)

print()
print("League Filter : UEFA Champions League ONLY")
print(f"Maximum Games : {MAX_MATCHES}")
print(f"API Delay     : {API_DELAY} seconds")
print("=" * 70)


# ============================================================
# TODAY FIXTURES
# ============================================================

print()
print("📅 Fetching today's fixtures...")

raw_today = fetch_api(
    f"fixtures?date={date_today_str}&timezone=Asia/Yangon"
)

time.sleep(API_DELAY)


# ============================================================
# TOMORROW FIXTURES
# ============================================================

print()
print("📅 Fetching tomorrow's fixtures...")

raw_tomorrow = fetch_api(
    f"fixtures?date={date_tomorrow_str}&timezone=Asia/Yangon"
)

time.sleep(API_DELAY)


# ============================================================
# COMBINE
# ============================================================

combined_fixtures = (
    raw_today +
    raw_tomorrow
)

print()
print(
    f"Raw fixtures received: {len(combined_fixtures)}"
)


# ============================================================
# FILTER CHAMPIONS LEAGUE
# ============================================================

seen_ids = set()

upcoming_fixtures = []


for f in combined_fixtures:

    fixture = f.get("fixture", {})

    f_id = fixture.get("id")

    if not f_id:
        continue

    if f_id in seen_ids:
        continue

    seen_ids.add(f_id)

    status_short = (
        fixture
        .get("status", {})
        .get("short")
    )

    # Upcoming only
    if status_short not in [
        "NS",
        "TBD"
    ]:
        continue

    f_time_str = fixture.get("date")

    if not f_time_str:
        continue

    try:

        f_dt = datetime.fromisoformat(
            f_time_str
        )

    except Exception:

        print(
            "⚠️ Invalid fixture datetime:",
            f_time_str
        )

        continue

    # Time window
    if not (
        window_start <= f_dt <= window_end
    ):
        continue

    league_name = f.get(
        "league",
        {}
    ).get("name", "")

    country_name = f.get(
        "league",
        {}
    ).get("country", "")

    home_name = f.get(
        "teams",
        {}
    ).get("home", {}).get(
        "name", ""
    )

    away_name = f.get(
        "teams",
        {}
    ).get("away", {}).get(
        "name", ""
    )

    # Champions League ONLY
    if not is_champions_league(
        league_name,
        country_name,
        home_name,
        away_name
    ):
        continue

    upcoming_fixtures.append(f)


# ============================================================
# LIMIT MATCHES
# ============================================================

upcoming_fixtures = upcoming_fixtures[
    :MAX_MATCHES
]


print()
print("=" * 70)
print("🏆 CHAMPIONS LEAGUE FIXTURES FOUND")
print("=" * 70)

print(
    f"Total Champions League matches selected: "
    f"{len(upcoming_fixtures)}"
)

for i, f in enumerate(
    upcoming_fixtures,
    start=1
):

    print(
        f"{i}. "
        f"{f['teams']['home']['name']} "
        f"vs "
        f"{f['teams']['away']['name']} "
        f"| "
        f"{f['fixture']['date']}"
    )

print("=" * 70)


# ============================================================
# 8. EVALUATE MATCHES
# ============================================================

evaluated_matches = []


for idx, fix in enumerate(
    upcoming_fixtures
):

    print()
    print()
    print("#" * 70)
    print(
        f"🎯 EVALUATING MATCH "
        f"{idx + 1}/{len(upcoming_fixtures)}"
    )
    print("#" * 70)

    h_id = (
        fix["teams"]["home"]["id"]
    )

    a_id = (
        fix["teams"]["away"]["id"]
    )

    h_name = (
        fix["teams"]["home"]["name"]
    )

    a_name = (
        fix["teams"]["away"]["name"]
    )

    # --------------------------------------------------------
    # HOME L5
    # --------------------------------------------------------

    h_stats = get_l5(
        h_id,
        "HOME",
        h_name
    )

    time.sleep(API_DELAY)

    # --------------------------------------------------------
    # AWAY L5
    # --------------------------------------------------------

    a_stats = get_l5(
        a_id,
        "AWAY",
        a_name
    )

    time.sleep(API_DELAY)

    # ========================================================
    # DATA AVAILABILITY CHECK
    # ========================================================

    if (
        not h_stats["available"]
        or
        not a_stats["available"]
    ):

        print()
        print(
            "⚠️ MODEL SKIPPED"
        )

        print(
            "Reason:"
        )

        if not h_stats["available"]:
            print(
                f"Home: {h_stats['reason']}"
            )

        if not a_stats["available"]:
            print(
                f"Away: {a_stats['reason']}"
            )

        signal = "DATA_UNAVAILABLE"

        over_prob = None
        over_edge = None

    else:

        # ====================================================
        # OVER 2.5 RULE
        # ====================================================

        is_over = (

            h_stats["over_pct"] >= 60

            and

            a_stats["over_pct"] >= 60

            and

            h_stats["btts_pct"] >= 60

            and

            a_stats["btts_pct"] >= 60

            and

            h_stats["gf_avg"] > 1.5

            and

            h_stats["ga_avg"] > 1.0

            and

            a_stats["gf_avg"] > 1.0

            and

            a_stats["ga_avg"] > 1.0

        )

        # ====================================================
        # UNDER 2.5 RULE
        # ====================================================

        is_under = (

            h_stats["under_pct"] >= 60

            and

            a_stats["under_pct"] >= 60

            and

            h_stats["btts_pct"] <= 50

            and

            a_stats["btts_pct"] <= 50

            and

            h_stats["gf_avg"] < 1.3

            and

            h_stats["ga_avg"] < 1.0

            and

            a_stats["gf_avg"] < 1.1

            and

            a_stats["ga_avg"] < 1.2

        )

        # ====================================================
        # MODEL PROBABILITY
        # ====================================================

        avg_over_pct = (
            h_stats["over_pct"]
            +
            a_stats["over_pct"]
        ) / 2

        avg_btts_pct = (
            h_stats["btts_pct"]
            +
            a_stats["btts_pct"]
        ) / 2

        gf_component = min(
            100,
            (
                h_stats["gf_avg"]
                +
                a_stats["gf_avg"]
            )
            / 4.0
            * 100
        )

        ga_component = min(
            100,
            (
                h_stats["ga_avg"]
                +
                a_stats["ga_avg"]
            )
            / 3.2
            * 100
        )

        over_prob = round(

            (
                avg_over_pct
                * 0.40
            )

            +

            (
                avg_btts_pct
                * 0.20
            )

            +

            (
                gf_component
                * 0.20
            )

            +

            (
                ga_component
                * 0.20
            ),

            1
        )

        # ====================================================
        # MODEL EDGE
        # ====================================================

        # Reference probability:
        # 60% = baseline threshold
        over_edge = round(
            over_prob - 60,
            1
        )

        # ====================================================
        # SIGNAL
        # ====================================================

        if (
            is_over
            and
            over_edge >= 5
        ):

            signal = "OVER_2_5"

        elif is_under:

            signal = "UNDER_2_5"

        else:

            signal = "NEUTRAL"

        # ====================================================
        # PRINT MODEL RESULT
        # ====================================================

        print()
        print("=" * 60)
        print("🤖 MODEL RESULT")
        print("=" * 60)

        print(
            f"Over Probability : {over_prob}%"
        )

        print(
            f"Model Edge       : {over_edge}%"
        )

        print(
            f"Signal            : {signal}"
        )

        print("=" * 60)


    # ========================================================
    # MATCH TIME
    # ========================================================

    f_date_display = (
        fix["fixture"]["date"][:10]
    )

    f_time_display = (
        fix["fixture"]["date"][11:16]
    )


    # ========================================================
    # SAVE RESULT
    # ========================================================

    evaluated_matches.append({

        "fixture_id":
            fix["fixture"]["id"],

        "league":
            fix["league"]["name"],

        "country":
            fix["league"].get(
                "country",
                ""
            ),

        "home":
            h_name,

        "away":
            a_name,

        "date":
            f_date_display,

        "time":
            f_time_display,

        "status":
            fix["fixture"]["status"]["short"],

        "signal":
            signal,

        "prob":
            over_prob,

        "edge":
            over_edge,

        "data_status": {

            "home":
                h_stats["reason"],

            "away":
                a_stats["reason"],

        },

        "h_stats":
            h_stats,

        "a_stats":
            a_stats,

    })


# ============================================================
# 9. SORT RESULTS
# ============================================================

evaluated_matches.sort(

    key=lambda x: (

        0
        if x["signal"] == "OVER_2_5"

        else 1
        if x["signal"] == "UNDER_2_5"

        else 2
        if x["signal"] == "NEUTRAL"

        else 3,

        x["time"]

    )
)


# ============================================================
# 10. SAVE JSON
# ============================================================

output_data = {

    "test_mode":
        True,

    "league_filter":
        "UEFA Champions League ONLY",

    "window_range": (

        f"{window_start.strftime('%d %b %I:%M %p')}"
        f" - "
        f"{window_end.strftime('%d %b %I:%M %p')}"
        f" MMT"

    ),

    "total_matches":
        len(evaluated_matches),

    "matches":
        evaluated_matches,

}


with open(
    "matches_data.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output_data,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# 11. FINAL SUMMARY
# ============================================================

print()
print()
print("=" * 70)
print("✅ TEST COMPLETE")
print("=" * 70)

print(
    f"Champions League matches evaluated: "
    f"{len(evaluated_matches)}"
)

print()

for match in evaluated_matches:

    print(
        f"{match['home']} "
        f"vs "
        f"{match['away']}"
    )

    print(
        f"Signal : {match['signal']}"
    )

    print(
        f"Probability : {match['prob']}"
    )

    print(
        f"Edge : {match['edge']}"
    )

    print(
        f"Home Data : "
        f"{match['data_status']['home']}"
    )

    print(
        f"Away Data : "
        f"{match['data_status']['away']}"
    )

    print("-" * 70)


print()
print(
    "💾 Saved to: matches_data.json"
)

print()
print(
    "🔎 IMPORTANT:"
)

print(
    "If you see 50% everywhere now,"
)

print(
    "that is NOT a fake fallback anymore."
)

print(
    "The new version does NOT generate 50% defaults."
)

print(
    "Check the API DEBUG section above "
    "for HTTP Status / Results / Errors."
)

print("=" * 70)
