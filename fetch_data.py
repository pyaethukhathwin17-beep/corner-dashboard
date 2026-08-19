from datetime import datetime, timedelta, timezone
import json
import os
import time
import requests


# ============================================================
# 1. CONFIGURATION
# ============================================================

API_BASE_URL = "https://v3.football.api-sports.io"

# API-Football Free plan is limited to 100 requests/day.
# We deliberately keep this Champions League test small.
MAX_GAMES = 5

# Delay between API calls.
# 7 seconds is intentionally conservative.
API_DELAY = 7

# Historical window used for L5 calculation.
HISTORY_DAYS = 120

# We need both seasons because the 120-day window can cross
# two football seasons.
HISTORY_SEASONS = [2025, 2026]

# Myanmar Time
MMT_TZ = timezone(timedelta(hours=6, minutes=30))


# ============================================================
# 2. SECURE API KEY CONFIGURATION
# ============================================================

raw_keys = os.environ.get("API_KEYS_POOL", "").strip()

if not raw_keys:
    raise RuntimeError(
        "❌ API_KEYS_POOL is not configured.\n"
        "GitHub Actions Secrets ထဲမှာ API_KEYS_POOL ထည့်ပါ။"
    )

API_KEYS = [
    key.strip()
    for key in raw_keys.split(",")
    if key.strip()
]

if not API_KEYS:
    raise RuntimeError(
        "❌ API_KEYS_POOL is empty."
    )

current_key_index = 0

print("=" * 70)
print("🔑 API CONFIGURATION")
print("=" * 70)
print(f"Total API Keys Loaded : {len(API_KEYS)}")
print(f"Active API Key        : {API_KEYS[0][:8]}***")
print("=" * 70)


# ============================================================
# 3. DATE WINDOW
# ============================================================

now_mmt = datetime.now(MMT_TZ)

# Today 12:00 PM MMT
window_start = datetime(
    now_mmt.year,
    now_mmt.month,
    now_mmt.day,
    12,
    0,
    0,
    tzinfo=MMT_TZ,
)

# Next day 12:00 PM MMT
window_end = window_start + timedelta(days=1)

date_today_str = window_start.strftime("%Y-%m-%d")
date_tomorrow_str = window_end.strftime("%Y-%m-%d")

# Historical window
history_end_dt = window_start - timedelta(days=1)
history_start_dt = history_end_dt - timedelta(days=HISTORY_DAYS - 1)

history_from = history_start_dt.strftime("%Y-%m-%d")
history_to = history_end_dt.strftime("%Y-%m-%d")


# ============================================================
# 4. CHAMPIONS LEAGUE ONLY
# ============================================================

CHAMPIONS_LEAGUE_NAMES = {
    "uefa champions league",
    "champions league",
}


def is_champions_league(fixture):
    league_name = (
        fixture.get("league", {})
        .get("name", "")
        .strip()
        .lower()
    )

    return league_name in CHAMPIONS_LEAGUE_NAMES


# ============================================================
# 5. API REQUEST ENGINE
# ============================================================

def fetch_api(endpoint, description=""):
    """
    Central API request function.

    API key is NEVER hard-coded.
    It comes from GitHub Actions Secret:
        API_KEYS_POOL
    """

    global current_key_index

    if not API_KEYS:
        return {
            "success": False,
            "response": [],
            "errors": {"config": "No API keys available."},
        }

    active_key = API_KEYS[current_key_index]

    url = f"{API_BASE_URL}/{endpoint}"

    headers = {
        "x-apisports-key": active_key,
        "Accept": "application/json",
    }

    print("")
    print("-" * 60)
    print("🌐 API REQUEST")
    print("-" * 60)

    if description:
        print(f"Purpose  : {description}")

    print(f"Endpoint : {endpoint}")
    print(f"Key      : {active_key[:8]}***")

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

        print(f"HTTP Status : {response.status_code}")

        try:
            data = response.json()
        except Exception:
            print("❌ API returned invalid JSON.")
            return {
                "success": False,
                "response": [],
                "errors": {
                    "http": response.status_code,
                    "message": "Invalid JSON response",
                },
            }

        api_errors = data.get("errors", {})
        results = data.get("results", 0)
        response_data = data.get("response", [])

        print(f"API Results : {results}")
        print(f"API Errors  : {api_errors}")
        print(f"Response    : {len(response_data)} items")

        # API quota information, if returned.
        remaining = response.headers.get(
            "x-ratelimit-requests-remaining"
        )

        if remaining:
            print(f"Requests Remaining : {remaining}")

        if api_errors:
            print(f"❌ API ERROR: {api_errors}")

            return {
                "success": False,
                "response": [],
                "errors": api_errors,
            }

        if response.status_code != 200:
            print("❌ HTTP ERROR")

            return {
                "success": False,
                "response": [],
                "errors": {
                    "http_status": response.status_code
                },
            }

        print("✅ API DATA RECEIVED")

        return {
            "success": True,
            "response": response_data,
            "errors": {},
        }

    except requests.exceptions.Timeout:
        print("❌ API TIMEOUT")

        return {
            "success": False,
            "response": [],
            "errors": {"timeout": "Request timed out"},
        }

    except requests.exceptions.RequestException as e:
        print(f"❌ CONNECTION ERROR: {e}")

        return {
            "success": False,
            "response": [],
            "errors": {"connection": str(e)},
        }

    except Exception as e:
        print(f"❌ UNKNOWN ERROR: {e}")

        return {
            "success": False,
            "response": [],
            "errors": {"unknown": str(e)},
        }


# ============================================================
# 6. GET FIXTURES FOR A DATE
# ============================================================

def get_fixtures_by_date(date_string):
    endpoint = (
        f"fixtures?"
        f"date={date_string}"
        f"&timezone=Asia/Yangon"
    )

    return fetch_api(
        endpoint,
        description=f"Fixtures for {date_string}",
    )


# ============================================================
# 7. GET TEAM HISTORY BY SEASON
# ============================================================

def get_team_history_for_season(
    team_id,
    team_name,
    season,
):
    """
    IMPORTANT:

    Free plan does NOT allow:
        fixtures?team=ID&last=15

    So we use:
        fixtures?team=ID&season=YYYY&from=DATE&to=DATE

    Then filter locally in Python.
    """

    endpoint = (
        f"fixtures?"
        f"team={team_id}"
        f"&season={season}"
        f"&from={history_from}"
        f"&to={history_to}"
        f"&timezone=Asia/Yangon"
    )

    print("")
    print("=" * 60)
    print("📊 TEAM HISTORY REQUEST")
    print("=" * 60)
    print(f"Team   : {team_name}")
    print(f"Team ID: {team_id}")
    print(f"Season : {season}")
    print(f"From   : {history_from}")
    print(f"To     : {history_to}")
    print("Method : team + season + from/to")
    print("=" * 60)

    result = fetch_api(
        endpoint,
        description=f"{team_name} historical fixtures - season {season}",
    )

    return result


# ============================================================
# 8. GET LAST 5 HOME / AWAY MATCHES
# ============================================================

def get_l5(team_id, venue, team_name=""):
    """
    Collect both 2025 and 2026 season data.

    Then:
        1. Combine
        2. Remove duplicate fixture IDs
        3. Keep completed matches only
        4. Filter Home/Away locally
        5. Sort newest -> oldest
        6. Select last 5
    """

    all_matches = []
    seen_ids = set()

    season_errors = []

    for season in HISTORY_SEASONS:

        result = get_team_history_for_season(
            team_id=team_id,
            team_name=team_name,
            season=season,
        )

        if not result["success"]:
            season_errors.append(
                {
                    "season": season,
                    "errors": result["errors"],
                }
            )

        for fixture in result["response"]:

            fixture_id = (
                fixture.get("fixture", {})
                .get("id")
            )

            if not fixture_id:
                continue

            if fixture_id in seen_ids:
                continue

            seen_ids.add(fixture_id)
            all_matches.append(fixture)

        # Small delay between season calls.
        time.sleep(API_DELAY)

    # --------------------------------------------------------
    # Completed matches only
    # --------------------------------------------------------

    completed_statuses = {
        "FT",
        "AET",
        "PEN",
    }

    completed = []

    for fixture in all_matches:

        status = (
            fixture.get("fixture", {})
            .get("status", {})
            .get("short", "")
        )

        if status in completed_statuses:
            completed.append(fixture)

    # --------------------------------------------------------
    # Venue filtering
    # --------------------------------------------------------

    selected = []

    for fixture in completed:

        home_id = (
            fixture.get("teams", {})
            .get("home", {})
            .get("id")
        )

        away_id = (
            fixture.get("teams", {})
            .get("away", {})
            .get("id")
        )

        if venue == "HOME" and home_id == team_id:
            selected.append(fixture)

        elif venue == "AWAY" and away_id == team_id:
            selected.append(fixture)

    # --------------------------------------------------------
    # Sort newest first
    # --------------------------------------------------------

    selected.sort(
        key=lambda x: (
            x.get("fixture", {})
            .get("date", "")
        ),
        reverse=True,
    )

    selected = selected[:5]

    print("")
    print(
        f"📌 {team_name} ({venue}) "
        f"→ {len(selected)} usable matches"
    )

    if season_errors:
        print("⚠️ Season API errors:")
        for err in season_errors:
            print(
                f"   Season {err['season']}: "
                f"{err['errors']}"
            )

    # --------------------------------------------------------
    # We require exactly 5 matches for L5 model.
    # No fake fallback.
    # --------------------------------------------------------

    if len(selected) < 5:

        print(
            f"❌ {team_name}: "
            f"Only {len(selected)}/5 "
            f"{venue} matches available."
        )

        return {
            "status": "INSUFFICIENT_L5_DATA",
            "matches_found": len(selected),
            "over_pct": None,
            "under_pct": None,
            "btts_pct": None,
            "gf_avg": None,
            "ga_avg": None,
            "scorelines": [],
            "error": season_errors,
        }

    # ========================================================
    # CALCULATE STATS
    # ========================================================

    over_count = 0
    btts_count = 0

    gf_total = 0
    ga_total = 0

    scorelines = []

    for fixture in selected:

        goals = fixture.get("goals", {})

        home_goals = goals.get("home")
        away_goals = goals.get("away")

        if home_goals is None:
            home_goals = 0

        if away_goals is None:
            away_goals = 0

        total_goals = home_goals + away_goals

        # Over 2.5
        if total_goals >= 3:
            over_count += 1

        # BTTS
        if home_goals > 0 and away_goals > 0:
            btts_count += 1

        # Team GF / GA
        if venue == "HOME":
            gf = home_goals
            ga = away_goals
        else:
            gf = away_goals
            ga = home_goals

        gf_total += gf
        ga_total += ga

        scorelines.append(
            {
                "date": fixture["fixture"]["date"][:10],
                "home": fixture["teams"]["home"]["name"],
                "away": fixture["teams"]["away"]["name"],
                "gh": home_goals,
                "ga": away_goals,
                "tot": total_goals,
            }
        )

    n = len(selected)

    over_pct = round(
        (over_count / n) * 100,
        1,
    )

    under_pct = round(
        100 - over_pct,
        1,
    )

    btts_pct = round(
        (btts_count / n) * 100,
        1,
    )

    gf_avg = round(
        gf_total / n,
        2,
    )

    ga_avg = round(
        ga_total / n,
        2,
    )

    print("")
    print(
        f"✅ {team_name} ({venue}) L5 READY"
    )
    print(
        f"   Over 2.5 : {over_pct}%"
    )
    print(
        f"   Under 2.5: {under_pct}%"
    )
    print(
        f"   BTTS     : {btts_pct}%"
    )
    print(
        f"   GF Avg   : {gf_avg}"
    )
    print(
        f"   GA Avg   : {ga_avg}"
    )

    return {
        "status": "OK",
        "matches_found": n,
        "over_pct": over_pct,
        "under_pct": under_pct,
        "btts_pct": btts_pct,
        "gf_avg": gf_avg,
        "ga_avg": ga_avg,
        "scorelines": scorelines,
        "error": season_errors,
    }


# ============================================================
# 9. MODEL CALCULATION
# ============================================================

def calculate_model(home_stats, away_stats):
    """
    Heuristic pre-match model.

    IMPORTANT:
    This is NOT a calibrated bookmaker probability.

    It is a scoring model based on:
        - L5 Over 2.5
        - L5 BTTS
        - Goals For
        - Goals Against

    Only calculate if both teams have valid L5 data.
    """

    if (
        home_stats.get("status") != "OK"
        or away_stats.get("status") != "OK"
    ):
        return {
            "signal": "DATA_UNAVAILABLE",
            "prob": None,
            "edge": None,
            "over_prob": None,
            "under_prob": None,
        }

    # --------------------------------------------------------
    # OVER SCORE
    # --------------------------------------------------------

    avg_over_pct = (
        home_stats["over_pct"]
        + away_stats["over_pct"]
    ) / 2

    avg_btts_pct = (
        home_stats["btts_pct"]
        + away_stats["btts_pct"]
    ) / 2

    # GF component
    gf_component = min(
        100,
        (
            (
                home_stats["gf_avg"]
                + away_stats["gf_avg"]
            )
            / 4.0
        )
        * 100,
    )

    # GA component
    ga_component = min(
        100,
        (
            (
                home_stats["ga_avg"]
                + away_stats["ga_avg"]
            )
            / 3.2
        )
        * 100,
    )

    over_prob = (
        avg_over_pct * 0.40
        + avg_btts_pct * 0.20
        + gf_component * 0.20
        + ga_component * 0.20
    )

    over_prob = round(
        max(0, min(100, over_prob)),
        1,
    )

    # Complementary heuristic for Under.
    under_prob = round(
        100 - over_prob,
        1,
    )

    # --------------------------------------------------------
    # EDGE
    # --------------------------------------------------------

    over_edge = round(
        over_prob - 60,
        1,
    )

    under_edge = round(
        under_prob - 60,
        1,
    )

    # --------------------------------------------------------
    # TARGET CONDITIONS
    # --------------------------------------------------------

    is_over = (
        home_stats["over_pct"] >= 60
        and away_stats["over_pct"] >= 60

        and home_stats["btts_pct"] >= 60
        and away_stats["btts_pct"] >= 60

        and home_stats["gf_avg"] > 1.5
        and home_stats["ga_avg"] > 1.0

        and away_stats["gf_avg"] > 1.0
        and away_stats["ga_avg"] > 1.0
    )

    is_under = (
        home_stats["under_pct"] >= 60
        and away_stats["under_pct"] >= 60

        and home_stats["btts_pct"] <= 50
        and away_stats["btts_pct"] <= 50

        and home_stats["gf_avg"] < 1.3
        and home_stats["ga_avg"] < 1.0

        and away_stats["gf_avg"] < 1.1
        and away_stats["ga_avg"] < 1.2
    )

    # --------------------------------------------------------
    # FINAL SIGNAL
    # --------------------------------------------------------

    if is_over and over_edge >= 5:
        signal = "OVER_2_5"
        final_prob = over_prob
        final_edge = over_edge

    elif is_under and under_edge >= 5:
        signal = "UNDER_2_5"
        final_prob = under_prob
        final_edge = under_edge

    else:
        signal = "NEUTRAL"

        # Show the stronger side's probability.
        if over_prob >= under_prob:
            final_prob = over_prob
            final_edge = over_edge
        else:
            final_prob = under_prob
            final_edge = under_edge

    return {
        "signal": signal,
        "prob": final_prob,
        "edge": final_edge,
        "over_prob": over_prob,
        "under_prob": under_prob,
    }


# ============================================================
# 10. MAIN PROGRAM
# ============================================================

print("")
print("=" * 70)
print("🏆 CHAMPIONS LEAGUE TEST MODE")
print("=" * 70)

print("Window:")
print(
    window_start.strftime(
        "%Y-%m-%d %I:%M %p"
    )
    + " MMT"
)

print("to")

print(
    window_end.strftime(
        "%Y-%m-%d %I:%M %p"
    )
    + " MMT"
)

print("")
print("League Filter : UEFA Champions League ONLY")
print(f"Maximum Games : {MAX_GAMES}")
print(f"API Delay     : {API_DELAY} seconds")
print(f"History Range : {HISTORY_DAYS} days")
print(
    f"History Seasons : {HISTORY_SEASONS}"
)
print(
    "L5 Method     : team + season + from/to"
)

print("=" * 70)


# ============================================================
# 11. FETCH TODAY
# ============================================================

print("")
print("📅 Fetching today's fixtures...")

today_result = get_fixtures_by_date(
    date_today_str
)

time.sleep(API_DELAY)


# ============================================================
# 12. FETCH TOMORROW
# ============================================================

print("")
print("📅 Fetching tomorrow's fixtures...")

tomorrow_result = get_fixtures_by_date(
    date_tomorrow_str
)

time.sleep(API_DELAY)


raw_today = today_result["response"]
raw_tomorrow = tomorrow_result["response"]

combined_fixtures = (
    raw_today
    + raw_tomorrow
)

print("")
print(
    f"Raw fixtures received: "
    f"{len(combined_fixtures)}"
)


# ============================================================
# 13. FILTER CHAMPIONS LEAGUE
# ============================================================

seen_fixture_ids = set()
upcoming_fixtures = []

for fixture in combined_fixtures:

    fixture_id = (
        fixture.get("fixture", {})
        .get("id")
    )

    if not fixture_id:
        continue

    if fixture_id in seen_fixture_ids:
        continue

    seen_fixture_ids.add(fixture_id)

    # --------------------------------------------------------
    # Champions League ONLY
    # --------------------------------------------------------

    if not is_champions_league(fixture):
        continue

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    status_short = (
        fixture.get("fixture", {})
        .get("status", {})
        .get("short", "")
    )

    if status_short not in {
        "NS",
        "TBD",
    }:
        continue

    # --------------------------------------------------------
    # Match datetime
    # --------------------------------------------------------

    fixture_date_string = (
        fixture.get("fixture", {})
        .get("date")
    )

    if not fixture_date_string:
        continue

    try:
        fixture_dt = datetime.fromisoformat(
            fixture_date_string
        )
    except Exception:
        continue

    # --------------------------------------------------------
    # 12 PM -> next day 12 PM
    # --------------------------------------------------------

    if not (
        window_start
        <= fixture_dt
        <= window_end
    ):
        continue

    upcoming_fixtures.append(
        fixture
    )


# Sort chronologically
upcoming_fixtures.sort(
    key=lambda x: (
        x.get("fixture", {})
        .get("date", "")
    )
)

# Maximum 5
upcoming_fixtures = upcoming_fixtures[
    :MAX_GAMES
]


# ============================================================
# 14. DISPLAY SELECTED FIXTURES
# ============================================================

print("")
print("=" * 70)
print("🏆 CHAMPIONS LEAGUE FIXTURES FOUND")
print("=" * 70)

print(
    "Total Champions League matches selected: "
    f"{len(upcoming_fixtures)}"
)

for index, fixture in enumerate(
    upcoming_fixtures,
    start=1,
):

    home_name = (
        fixture["teams"]["home"]["name"]
    )

    away_name = (
        fixture["teams"]["away"]["name"]
    )

    fixture_date = (
        fixture["fixture"]["date"]
    )

    print(
        f"{index}. "
        f"{home_name} vs {away_name} | "
        f"{fixture_date}"
    )

print("=" * 70)


# ============================================================
# 15. EVALUATE MATCHES
# ============================================================

evaluated_matches = []

for index, fixture in enumerate(
    upcoming_fixtures,
    start=1,
):

    home_team = fixture["teams"]["home"]
    away_team = fixture["teams"]["away"]

    home_id = home_team["id"]
    away_id = away_team["id"]

    home_name = home_team["name"]
    away_name = away_team["name"]

    league_name = (
        fixture["league"]["name"]
    )

    country_name = (
        fixture["league"].get(
            "country",
            "",
        )
    )

    fixture_date = (
        fixture["fixture"]["date"]
    )

    fixture_status = (
        fixture["fixture"]["status"]
        .get("short", "")
    )

    print("")
    print("#" * 70)
    print(
        f"🎯 EVALUATING MATCH "
        f"{index}/{len(upcoming_fixtures)}"
    )
    print("#" * 70)

    print("")
    print(
        f"⚽ {home_name} vs {away_name}"
    )

    # --------------------------------------------------------
    # HOME L5
    # --------------------------------------------------------

    home_stats = get_l5(
        team_id=home_id,
        venue="HOME",
        team_name=home_name,
    )

    # --------------------------------------------------------
    # AWAY L5
    # --------------------------------------------------------

    away_stats = get_l5(
        team_id=away_id,
        venue="AWAY",
        team_name=away_name,
    )

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model = calculate_model(
        home_stats,
        away_stats,
    )

    if model["signal"] == "DATA_UNAVAILABLE":

        print("")
        print("⚠️ MODEL SKIPPED")
        print(
            f"Home: {home_stats['status']}"
        )
        print(
            f"Away: {away_stats['status']}"
        )

    else:

        print("")
        print("=" * 60)
        print("🧠 MODEL RESULT")
        print("=" * 60)

        print(
            f"Signal       : {model['signal']}"
        )

        print(
            f"Over 2.5 Prob: "
            f"{model['over_prob']}%"
        )

        print(
            f"Under 2.5 Prob: "
            f"{model['under_prob']}%"
        )

        print(
            f"Final Prob   : "
            f"{model['prob']}%"
        )

        print(
            f"Edge         : "
            f"{model['edge']:+.1f}%"
        )

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    fixture_date_display = (
        fixture_date[:10]
    )

    fixture_time_display = (
        fixture_date[11:16]
    )

    evaluated_matches.append(
        {
            "fixture_id": fixture["fixture"]["id"],

            "league": league_name,
            "country": country_name,

            "home": home_name,
            "away": away_name,

            "date": fixture_date_display,
            "time": fixture_time_display,

            "status": fixture_status,

            "signal": model["signal"],

            "prob": model["prob"],
            "edge": model["edge"],

            "over_prob": model["over_prob"],
            "under_prob": model["under_prob"],

            "h_stats": home_stats,
            "a_stats": away_stats,
        }
    )


# ============================================================
# 16. SORT RESULTS
# ============================================================

signal_priority = {
    "OVER_2_5": 0,
    "UNDER_2_5": 1,
    "NEUTRAL": 2,
    "DATA_UNAVAILABLE": 3,
}

evaluated_matches.sort(
    key=lambda x: (
        signal_priority.get(
            x["signal"],
            99,
        ),
        x["time"],
    )
)


# ============================================================
# 17. SAVE JSON FOR STREAMLIT
# ============================================================

output_data = {
    "updated_at": datetime.now(
        MMT_TZ
    ).strftime(
        "%Y-%m-%d %I:%M %p MMT"
    ),

    "mode": "CHAMPIONS_LEAGUE_ONLY",

    "window_start": window_start.isoformat(),
    "window_end": window_end.isoformat(),

    "history_range": {
        "from": history_from,
        "to": history_to,
        "days": HISTORY_DAYS,
        "seasons": HISTORY_SEASONS,
    },

    "total_matches": len(
        evaluated_matches
    ),

    "matches": evaluated_matches,
}


with open(
    "matches_data.json",
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        output_data,
        file,
        indent=2,
        ensure_ascii=False,
    )


# ============================================================
# 18. FINAL SUMMARY
# ============================================================

print("")
print("=" * 70)
print("✅ TEST COMPLETE")
print("=" * 70)

print(
    "Champions League matches evaluated: "
    f"{len(evaluated_matches)}"
)

print("")

for match in evaluated_matches:

    print(
        f"{match['home']} vs "
        f"{match['away']}"
    )

    print(
        f"Signal : "
        f"{match['signal']}"
    )

    print(
        f"Probability : "
        f"{match['prob']}"
    )

    print(
        f"Edge : "
        f"{match['edge']}"
    )

    print(
        f"Over Prob : "
        f"{match['over_prob']}"
    )

    print(
        f"Under Prob : "
        f"{match['under_prob']}"
    )

    print(
        f"Home Data : "
        f"{match['h_stats']['status']}"
    )

    print(
        f"Away Data : "
        f"{match['a_stats']['status']}"
    )

    print("-" * 70)


print("")
print(
    "💾 Saved to: matches_data.json"
)

print("")
print("🔎 IMPORTANT:")
print(
    "• Champions League ONLY test mode"
)
print(
    "• No fixtures?team=ID&last=15"
)
print(
    "• Historical data uses "
    "team + season + from/to"
)
print(
    "• Seasons tested: "
    f"{HISTORY_SEASONS}"
)
print(
    "• No fake 50% fallback"
)
print(
    "• L5 requires 5 valid Home/Away matches"
)
print(
    "• Probability/Edge calculated only "
    "when both teams have valid L5 data"
)
print(
    "• API key is loaded only from "
    "API_KEYS_POOL GitHub Secret"
)
print("=" * 70)
