from datetime import datetime, timedelta, timezone
import json
import os
import re
import time
import requests


# ============================================================
# 1. CONFIGURATION
# ============================================================

API_BASE_URL = "https://v3.football.api-sports.io"

# ------------------------------------------------------------
# TEST MODE
# ------------------------------------------------------------

MAX_GAMES = 5

# API request တစ်ခါနဲ့တစ်ခါကြား delay
API_DELAY_SECONDS = 7

# L5 အတွက် လွန်ခဲ့တဲ့ ရက်ဘယ်လောက်အထိရှာမလဲ
# 120 days ဆိုရင် Champions League qualifier / recent matches
# တွေကို ရှာဖို့ အများအားဖြင့် လုံလောက်ပါတယ်။
HISTORY_DAYS = 120

# Free plan quota ကာကွယ်ရန်
MAX_HISTORY_REQUESTS = 10


# ============================================================
# 2. API KEY - ENVIRONMENT VARIABLE ONLY
# ============================================================

raw_keys = os.environ.get(
    "API_KEYS_POOL",
    ""
)

API_KEYS = [
    key.strip()
    for key in raw_keys.split(",")
    if key.strip()
]

if not API_KEYS:
    raise RuntimeError(
        "❌ API_KEYS_POOL is not configured.\n"
        "GitHub Actions Secrets ထဲမှာ API_KEYS_POOL ထည့်ပါ။"
    )


# လက်ရှိ test မှာ key တစ်ခုတည်းပဲ သုံးမယ်။
# Rate limit ကို bypass လုပ်ရန် key rotation မလုပ်ပါ။
API_KEY = API_KEYS[0]


# ============================================================
# 3. MYANMAR TIMEZONE
# ============================================================

MMT_TZ = timezone(
    timedelta(
        hours=6,
        minutes=30
    )
)

now_mmt = datetime.now(
    MMT_TZ
)


# ============================================================
# 4. 12:00 PM → NEXT DAY 12:00 PM WINDOW
# ============================================================

window_start = datetime(
    now_mmt.year,
    now_mmt.month,
    now_mmt.day,
    12,
    0,
    0,
    tzinfo=MMT_TZ
)

window_end = (
    window_start
    + timedelta(days=1)
)

date_today_str = window_start.strftime(
    "%Y-%m-%d"
)

date_tomorrow_str = window_end.strftime(
    "%Y-%m-%d"
)


# ============================================================
# 5. CHAMPIONS LEAGUE FILTER
# ============================================================

CHAMPIONS_LEAGUE_NAMES = {
    "uefa champions league",
    "champions league",
}


def is_champions_league(fixture):
    """
    UEFA Champions League ONLY.
    """

    league_name = (
        fixture
        .get("league", {})
        .get("name", "")
        .strip()
        .lower()
    )

    return league_name in CHAMPIONS_LEAGUE_NAMES


# ============================================================
# 6. BLACKLIST
# ============================================================

BLACKLIST_WORDS = [
    "women",
    "woman",
    "fem",
    "youth",
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
    "reserve",
    "reserves",
    "amateur",
    "academy",
]


def is_blacklisted_fixture(fixture):

    league_name = (
        fixture
        .get("league", {})
        .get("name", "")
        .lower()
    )

    home_name = (
        fixture
        .get("teams", {})
        .get("home", {})
        .get("name", "")
        .lower()
    )

    away_name = (
        fixture
        .get("teams", {})
        .get("away", {})
        .get("name", "")
        .lower()
    )

    combined = (
        f"{league_name} "
        f"{home_name} "
        f"{away_name}"
    )

    if any(
        word in combined
        for word in BLACKLIST_WORDS
    ):
        return True

    return False


# ============================================================
# 7. API REQUEST ENGINE
# ============================================================

def api_request(
    endpoint,
    delay=True
):
    """
    API-Football request.

    IMPORTANT:
    - No last parameter.
    - No fake fallback.
    - Full API error is returned.
    """

    url = (
        f"{API_BASE_URL}/"
        f"{endpoint}"
    )

    headers = {
        "x-apisports-key": API_KEY,
        "Accept": "application/json",
    }

    if delay:
        time.sleep(
            API_DELAY_SECONDS
        )

    print()
    print("-" * 60)
    print("🌐 API REQUEST")
    print("-" * 60)

    print(
        f"Endpoint : {endpoint}"
    )

    print(
        f"Key      : "
        f"{API_KEY[:8]}***"
    )

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

        print(
            f"HTTP Status : "
            f"{response.status_code}"
        )

        # ----------------------------------------------------
        # JSON parsing
        # ----------------------------------------------------

        try:

            data = response.json()

        except Exception:

            print(
                "❌ Response is not valid JSON."
            )

            print(
                response.text[:1000]
            )

            return {
                "ok": False,
                "response": [],
                "errors": {
                    "client": "INVALID_JSON"
                },
                "results": 0,
                "status_code": response.status_code,
            }

        errors = data.get(
            "errors",
            {}
        )

        results = data.get(
            "results",
            0
        )

        response_data = data.get(
            "response",
            []
        )

        print(
            f"API Results : {results}"
        )

        print(
            f"API Errors  : {errors}"
        )

        print(
            f"Response    : "
            f"{len(response_data)} items"
        )

        # ----------------------------------------------------
        # HTTP error
        # ----------------------------------------------------

        if response.status_code != 200:

            print(
                "❌ HTTP ERROR"
            )

            return {
                "ok": False,
                "response": [],
                "errors": errors,
                "results": results,
                "status_code": response.status_code,
            }

        # ----------------------------------------------------
        # API error
        # ----------------------------------------------------

        if errors:

            print(
                f"❌ API ERROR: {errors}"
            )

            return {
                "ok": False,
                "response": [],
                "errors": errors,
                "results": results,
                "status_code": response.status_code,
            }

        # ----------------------------------------------------
        # Empty response
        # ----------------------------------------------------

        if not response_data:

            print(
                "⚠️ API returned 0 items."
            )

            return {
                "ok": False,
                "response": [],
                "errors": {
                    "data": "EMPTY_RESPONSE"
                },
                "results": 0,
                "status_code": response.status_code,
            }

        print(
            "✅ API DATA RECEIVED"
        )

        return {
            "ok": True,
            "response": response_data,
            "errors": {},
            "results": results,
            "status_code": response.status_code,
        }

    except requests.exceptions.Timeout:

        print(
            "❌ REQUEST TIMEOUT"
        )

        return {
            "ok": False,
            "response": [],
            "errors": {
                "client": "TIMEOUT"
            },
            "results": 0,
            "status_code": None,
        }

    except requests.exceptions.ConnectionError:

        print(
            "❌ CONNECTION ERROR"
        )

        return {
            "ok": False,
            "response": [],
            "errors": {
                "client": "CONNECTION_ERROR"
            },
            "results": 0,
            "status_code": None,
        }

    except Exception as e:

        print(
            f"❌ UNKNOWN ERROR: {e}"
        )

        return {
            "ok": False,
            "response": [],
            "errors": {
                "client": str(e)
            },
            "results": 0,
            "status_code": None,
        }


# ============================================================
# 8. FETCH UPCOMING FIXTURES
# ============================================================

print()
print("=" * 70)
print("🔑 API CONFIGURATION")
print("=" * 70)

print(
    f"Total API Keys Loaded : "
    f"{len(API_KEYS)}"
)

print(
    f"Active API Key        : "
    f"{API_KEY[:8]}***"
)

print()
print("=" * 70)
print("🏆 CHAMPIONS LEAGUE TEST MODE")
print("=" * 70)

print(
    "Window:"
)

print(
    window_start.strftime(
        "%Y-%m-%d %I:%M %p"
    )
    + " MMT"
)

print(
    "to"
)

print(
    window_end.strftime(
        "%Y-%m-%d %I:%M %p"
    )
    + " MMT"
)

print()
print(
    "League Filter : "
    "UEFA Champions League ONLY"
)

print(
    f"Maximum Games : {MAX_GAMES}"
)

print(
    f"API Delay     : "
    f"{API_DELAY_SECONDS} seconds"
)

print(
    f"History Range : "
    f"{HISTORY_DAYS} days"
)

print(
    "L5 Method     : "
    "DATE RANGE — NO last parameter"
)

print("=" * 70)


# ============================================================
# 9. TODAY FIXTURES
# ============================================================

print()
print(
    "📅 Fetching today's fixtures..."
)

today_result = api_request(
    f"fixtures?"
    f"date={date_today_str}"
    f"&timezone=Asia/Yangon",
    delay=False
)

raw_today = (
    today_result["response"]
    if today_result["ok"]
    else []
)


# ============================================================
# 10. TOMORROW FIXTURES
# ============================================================

print()
print(
    "📅 Fetching tomorrow's fixtures..."
)

tomorrow_result = api_request(
    f"fixtures?"
    f"date={date_tomorrow_str}"
    f"&timezone=Asia/Yangon"
)

raw_tomorrow = (
    tomorrow_result["response"]
    if tomorrow_result["ok"]
    else []
)


# ============================================================
# 11. COMBINE FIXTURES
# ============================================================

combined_fixtures = (
    raw_today
    + raw_tomorrow
)

print()
print(
    f"Raw fixtures received: "
    f"{len(combined_fixtures)}"
)


# ============================================================
# 12. SELECT CHAMPIONS LEAGUE FIXTURES
# ============================================================

seen_ids = set()

upcoming_fixtures = []

for fixture in combined_fixtures:

    fixture_id = (
        fixture
        .get("fixture", {})
        .get("id")
    )

    if not fixture_id:
        continue

    if fixture_id in seen_ids:
        continue

    seen_ids.add(
        fixture_id
    )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    status = (
        fixture
        .get("fixture", {})
        .get("status", {})
        .get("short", "")
    )

    if status not in [
        "NS",
        "TBD"
    ]:
        continue

    # --------------------------------------------------------
    # League filter
    # --------------------------------------------------------

    if not is_champions_league(
        fixture
    ):
        continue

    # --------------------------------------------------------
    # Blacklist
    # --------------------------------------------------------

    if is_blacklisted_fixture(
        fixture
    ):
        continue

    # --------------------------------------------------------
    # Fixture datetime
    # --------------------------------------------------------

    fixture_time = (
        fixture
        .get("fixture", {})
        .get("date")
    )

    if not fixture_time:
        continue

    try:

        fixture_dt = (
            datetime.fromisoformat(
                fixture_time
            )
        )

    except Exception:

        continue

    # --------------------------------------------------------
    # MMT window
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


# Sort by kickoff
upcoming_fixtures.sort(
    key=lambda x:
        x["fixture"]["date"]
)

# Maximum test matches
upcoming_fixtures = (
    upcoming_fixtures[:MAX_GAMES]
)


# ============================================================
# 13. PRINT SELECTED FIXTURES
# ============================================================

print()
print("=" * 70)
print("🏆 CHAMPIONS LEAGUE FIXTURES FOUND")
print("=" * 70)

print(
    "Total Champions League "
    f"matches selected: "
    f"{len(upcoming_fixtures)}"
)

for index, fixture in enumerate(
    upcoming_fixtures,
    start=1
):

    home = (
        fixture["teams"]["home"]["name"]
    )

    away = (
        fixture["teams"]["away"]["name"]
    )

    date_time = (
        fixture["fixture"]["date"]
    )

    print(
        f"{index}. "
        f"{home} vs {away} | "
        f"{date_time}"
    )

print("=" * 70)


# ============================================================
# 14. HISTORY CACHE
# ============================================================

# Same team ကို တစ်ကြိမ်ထက်ပိုပြီး request မလုပ်ရန်
history_cache = {}

history_request_count = 0


# ============================================================
# 15. GET TEAM HISTORY
# ============================================================

def get_team_history(
    team_id,
    team_name
):

    global history_request_count

    # --------------------------------------------------------
    # Cache
    # --------------------------------------------------------

    if team_id in history_cache:

        print(
            f"♻️ Using cached history: "
            f"{team_name}"
        )

        return history_cache[
            team_id
        ]


    # --------------------------------------------------------
    # Quota protection
    # --------------------------------------------------------

    if (
        history_request_count
        >= MAX_HISTORY_REQUESTS
    ):

        print(
            "❌ Maximum history "
            "request limit reached."
        )

        result = {
            "available": False,
            "reason": "LOCAL_REQUEST_LIMIT",
            "matches": [],
        }

        history_cache[
            team_id
        ] = result

        return result


    # --------------------------------------------------------
    # Date range
    # --------------------------------------------------------

    history_end = (
        window_start
        - timedelta(
            days=1
        )
    )

    history_start = (
        history_end
        - timedelta(
            days=HISTORY_DAYS
        )
    )

    from_date = (
        history_start.strftime(
            "%Y-%m-%d"
        )
    )

    to_date = (
        history_end.strftime(
            "%Y-%m-%d"
        )
    )


    # --------------------------------------------------------
    # IMPORTANT:
    # NO last=15
    #
    # Free plan restriction ကိုရှောင်ရန်
    # date range သုံးထားသည်။
    # --------------------------------------------------------

    endpoint = (
        "fixtures?"
        f"team={team_id}"
        f"&from={from_date}"
        f"&to={to_date}"
        f"&timezone=Asia/Yangon"
    )


    print()
    print("=" * 60)
    print("📊 TEAM HISTORY REQUEST")
    print("=" * 60)

    print(
        f"Team   : {team_name}"
    )

    print(
        f"Team ID: {team_id}"
    )

    print(
        f"From   : {from_date}"
    )

    print(
        f"To     : {to_date}"
    )

    print(
        "Method : from/to "
        "(NO last parameter)"
    )


    history_request_count += 1

    result = api_request(
        endpoint
    )


    # --------------------------------------------------------
    # API failure
    # --------------------------------------------------------

    if not result["ok"]:

        api_reason = result.get(
            "errors",
            {}
        )

        data = {
            "available": False,
            "reason": (
                "API_ERROR"
            ),
            "errors": api_reason,
            "matches": [],
        }

        history_cache[
            team_id
        ] = data

        print(
            f"❌ {team_name}: "
            f"No fixture data received."
        )

        return data


    matches = result[
        "response"
    ]


    # --------------------------------------------------------
    # Finished matches only
    # --------------------------------------------------------

    finished = []

    for fixture in matches:

        status = (
            fixture
            .get("fixture", {})
            .get("status", {})
            .get("short", "")
        )

        if status not in [
            "FT",
            "AET",
            "PEN"
        ]:
            continue

        finished.append(
            fixture
        )


    # Newest first
    finished.sort(
        key=lambda x:
            x["fixture"]["date"],
        reverse=True
    )


    data = {
        "available": True,
        "reason": "OK",
        "matches": finished,
    }

    history_cache[
        team_id
    ] = data


    print(
        f"✅ {team_name}: "
        f"{len(finished)} finished "
        f"matches found."
    )

    return data


# ============================================================
# 16. SELECT L5 BY VENUE
# ============================================================

def get_l5(
    team_id,
    venue,
    team_name
):

    history = get_team_history(
        team_id,
        team_name
    )

    if not history.get(
        "available",
        False
    ):

        return {
            "available": False,
            "reason": history.get(
                "reason",
                "API_DATA_UNAVAILABLE"
            ),
            "errors": history.get(
                "errors",
                {}
            ),
            "over_pct": None,
            "under_pct": None,
            "btts_pct": None,
            "gf_avg": None,
            "ga_avg": None,
            "scorelines": [],
        }


    matches = history.get(
        "matches",
        []
    )


    # --------------------------------------------------------
    # Venue filter
    # --------------------------------------------------------

    selected = []

    for fixture in matches:

        home_id = (
            fixture["teams"]
            ["home"]["id"]
        )

        away_id = (
            fixture["teams"]
            ["away"]["id"]
        )

        if (
            venue == "HOME"
            and home_id == team_id
        ):

            selected.append(
                fixture
            )

        elif (
            venue == "AWAY"
            and away_id == team_id
        ):

            selected.append(
                fixture
            )


        if len(selected) >= 5:
            break


    # --------------------------------------------------------
    # Not enough venue-specific matches
    # --------------------------------------------------------

    if len(selected) < 5:

        print(
            f"⚠️ {team_name}: "
            f"Only {len(selected)} "
            f"{venue} matches found "
            f"in {HISTORY_DAYS} days."
        )

        return {
            "available": False,
            "reason": (
                "INSUFFICIENT_L5_DATA"
            ),
            "errors": {},
            "over_pct": None,
            "under_pct": None,
            "btts_pct": None,
            "gf_avg": None,
            "ga_avg": None,
            "scorelines": [],
        }


    # ========================================================
    # CALCULATE STATISTICS
    # ========================================================

    over_count = 0
    btts_count = 0

    gf_total = 0
    ga_total = 0

    scorelines = []


    for fixture in selected:

        goals = fixture.get(
            "goals",
            {}
        )

        home_goals = goals.get(
            "home"
        )

        away_goals = goals.get(
            "away"
        )

        # Missing goals = invalid record
        if (
            home_goals is None
            or away_goals is None
        ):
            continue


        total_goals = (
            home_goals
            + away_goals
        )


        # ----------------------------------------------------
        # Over 2.5
        # ----------------------------------------------------

        if total_goals >= 3:

            over_count += 1


        # ----------------------------------------------------
        # BTTS
        # ----------------------------------------------------

        if (
            home_goals > 0
            and away_goals > 0
        ):

            btts_count += 1


        # ----------------------------------------------------
        # GF / GA
        # ----------------------------------------------------

        home_id = (
            fixture["teams"]
            ["home"]["id"]
        )


        if home_id == team_id:

            gf = home_goals
            ga = away_goals

        else:

            gf = away_goals
            ga = home_goals


        gf_total += gf
        ga_total += ga


        # ----------------------------------------------------
        # Scoreline
        # ----------------------------------------------------

        scorelines.append(
            {
                "date":
                    fixture[
                        "fixture"
                    ][
                        "date"
                    ][:10],

                "home":
                    fixture[
                        "teams"
                    ][
                        "home"
                    ][
                        "name"
                    ],

                "away":
                    fixture[
                        "teams"
                    ][
                        "away"
                    ][
                        "name"
                    ],

                "gh":
                    home_goals,

                "ga":
                    away_goals,

                "tot":
                    total_goals,
            }
        )


    # --------------------------------------------------------
    # Valid sample count
    # --------------------------------------------------------

    n = len(
        scorelines
    )


    if n < 5:

        return {
            "available": False,
            "reason": (
                "INSUFFICIENT_VALID_MATCHES"
            ),
            "errors": {},
            "over_pct": None,
            "under_pct": None,
            "btts_pct": None,
            "gf_avg": None,
            "ga_avg": None,
            "scorelines": scorelines,
        }


    # ========================================================
    # RETURN REAL DATA
    # ========================================================

    stats = {

        "available": True,

        "reason": "OK",

        "matches_used": n,

        "over_pct":
            int(
                (
                    over_count
                    / n
                )
                * 100
            ),

        "under_pct":
            int(
                (
                    (
                        n
                        - over_count
                    )
                    / n
                )
                * 100
            ),

        "btts_pct":
            int(
                (
                    btts_count
                    / n
                )
                * 100
            ),

        "gf_avg":
            round(
                gf_total
                / n,
                2
            ),

        "ga_avg":
            round(
                ga_total
                / n,
                2
            ),

        "scorelines":
            scorelines,
    }


    print(
        f"✅ {team_name} "
        f"({venue}) L5 READY"
    )

    print(
        f"   Over 2.5 : "
        f"{stats['over_pct']}%"
    )

    print(
        f"   Under 2.5: "
        f"{stats['under_pct']}%"
    )

    print(
        f"   BTTS     : "
        f"{stats['btts_pct']}%"
    )

    print(
        f"   GF Avg   : "
        f"{stats['gf_avg']}"
    )

    print(
        f"   GA Avg   : "
        f"{stats['ga_avg']}"
    )

    return stats


# ============================================================
# 17. MODEL CALCULATION
# ============================================================

def calculate_model(
    home_stats,
    away_stats
):

    # --------------------------------------------------------
    # Do NOT calculate if data unavailable
    # --------------------------------------------------------

    if not (
        home_stats.get(
            "available",
            False
        )
        and
        away_stats.get(
            "available",
            False
        )
    ):

        return {
            "signal":
                "DATA_UNAVAILABLE",

            "prob":
                None,

            "edge":
                None,
        }


    # ========================================================
    # 5-STAR OVER RULE
    # ========================================================

    is_over = (

        home_stats[
            "over_pct"
        ] >= 60

        and

        away_stats[
            "over_pct"
        ] >= 60

        and

        home_stats[
            "btts_pct"
        ] >= 60

        and

        away_stats[
            "btts_pct"
        ] >= 60

        and

        home_stats[
            "gf_avg"
        ] > 1.5

        and

        home_stats[
            "ga_avg"
        ] > 1.0

        and

        away_stats[
            "gf_avg"
        ] > 1.0

        and

        away_stats[
            "ga_avg"
        ] > 1.0
    )


    # ========================================================
    # 5-STAR UNDER RULE
    # ========================================================

    is_under = (

        home_stats[
            "under_pct"
        ] >= 60

        and

        away_stats[
            "under_pct"
        ] >= 60

        and

        home_stats[
            "btts_pct"
        ] <= 50

        and

        away_stats[
            "btts_pct"
        ] <= 50

        and

        home_stats[
            "gf_avg"
        ] < 1.3

        and

        home_stats[
            "ga_avg"
        ] < 1.0

        and

        away_stats[
            "gf_avg"
        ] < 1.1

        and

        away_stats[
            "ga_avg"
        ] < 1.2
    )


    # ========================================================
    # OVER PROBABILITY
    # ========================================================

    avg_over = (
        home_stats["over_pct"]
        +
        away_stats["over_pct"]
    ) / 2


    avg_btts = (
        home_stats["btts_pct"]
        +
        away_stats["btts_pct"]
    ) / 2


    avg_gf = (
        home_stats["gf_avg"]
        +
        away_stats["gf_avg"]
    )


    avg_ga = (
        home_stats["ga_avg"]
        +
        away_stats["ga_avg"]
    )


    gf_component = min(
        100,
        (
            avg_gf
            / 4.0
        )
        * 100
    )


    ga_component = min(
        100,
        (
            avg_ga
            / 3.2
        )
        * 100
    )


    over_prob = round(

        (
            avg_over
            * 0.40
        )

        +

        (
            avg_btts
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


    over_edge = round(
        over_prob
        - 60,
        1
    )


    # ========================================================
    # SIGNAL
    # ========================================================

    if (
        is_over
        and
        over_edge >= 5
    ):

        signal = (
            "OVER_2_5"
        )

    elif is_under:

        signal = (
            "UNDER_2_5"
        )

    else:

        signal = (
            "NEUTRAL"
        )


    return {
        "signal":
            signal,

        "prob":
            over_prob,

        "edge":
            over_edge,
    }


# ============================================================
# 18. MAIN EVALUATION
# ============================================================

evaluated_matches = []


for index, fixture in enumerate(
    upcoming_fixtures,
    start=1
):

    home_id = (
        fixture["teams"]
        ["home"]["id"]
    )

    away_id = (
        fixture["teams"]
        ["away"]["id"]
    )

    home_name = (
        fixture["teams"]
        ["home"]["name"]
    )

    away_name = (
        fixture["teams"]
        ["away"]["name"]
    )


    print()
    print("#" * 70)

    print(
        f"🎯 EVALUATING MATCH "
        f"{index}/"
        f"{len(upcoming_fixtures)}"
    )

    print("#" * 70)

    print()
    print(
        f"⚽ {home_name} "
        f"vs "
        f"{away_name}"
    )


    # --------------------------------------------------------
    # HOME L5
    # --------------------------------------------------------

    home_stats = get_l5(
        home_id,
        "HOME",
        home_name
    )


    # --------------------------------------------------------
    # AWAY L5
    # --------------------------------------------------------

    away_stats = get_l5(
        away_id,
        "AWAY",
        away_name
    )


    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model = calculate_model(
        home_stats,
        away_stats
    )


    # --------------------------------------------------------
    # Model result
    # --------------------------------------------------------

    if (
        model["signal"]
        == "DATA_UNAVAILABLE"
    ):

        print()
        print(
            "⚠️ MODEL SKIPPED"
        )

        print(
            "Reason:"
        )

        print(
            "Home: "
            f"{home_stats.get('reason')}"
        )

        print(
            "Away: "
            f"{away_stats.get('reason')}"
        )

    else:

        print()
        print(
            "🎯 MODEL RESULT"
        )

        print(
            f"Signal      : "
            f"{model['signal']}"
        )

        print(
            f"Probability : "
            f"{model['prob']}%"
        )

        print(
            f"Edge        : "
            f"{model['edge']:+.1f}%"
        )


    # ========================================================
    # SAVE RESULT
    # ========================================================

    fixture_date = (
        fixture["fixture"]["date"]
    )

    fixture_dt = (
        datetime.fromisoformat(
            fixture_date
        )
    )


    evaluated_matches.append(
        {
            "fixture_id":
                fixture[
                    "fixture"
                ][
                    "id"
                ],

            "league":
                fixture[
                    "league"
                ][
                    "name"
                ],

            "country":
                fixture[
                    "league"
                ].get(
                    "country",
                    ""
                ),

            "home":
                home_name,

            "away":
                away_name,

            "date":
                fixture_dt.strftime(
                    "%Y-%m-%d"
                ),

            "time":
                fixture_dt.strftime(
                    "%H:%M"
                ),

            "status":
                fixture[
                    "fixture"
                ][
                    "status"
                ][
                    "short"
                ],

            "signal":
                model[
                    "signal"
                ],

            "prob":
                model[
                    "prob"
                ],

            "edge":
                model[
                    "edge"
                ],

            "h_stats":
                home_stats,

            "a_stats":
                away_stats,
        }
    )


# ============================================================
# 19. SORT RESULTS
# ============================================================

signal_priority = {
    "OVER_2_5": 0,
    "UNDER_2_5": 1,
    "NEUTRAL": 2,
    "DATA_UNAVAILABLE": 3,
}


evaluated_matches.sort(
    key=lambda item: (
        signal_priority.get(
            item["signal"],
            99
        ),
        item["date"],
        item["time"],
    )
)


# ============================================================
# 20. SAVE JSON
# ============================================================

output_data = {

    "updated_at":
        now_mmt.strftime(
            "%Y-%m-%d %I:%M %p MMT"
        ),

    "window_start":
        window_start.isoformat(),

    "window_end":
        window_end.isoformat(),

    "window_range":
        (
            f"{window_start.strftime('%d %b %I:%M %p')}"
            f" - "
            f"{window_end.strftime('%d %b %I:%M %p')}"
            f" MMT"
        ),

    "mode":
        "CHAMPIONS_LEAGUE_TEST",

    "league_filter":
        "UEFA Champions League ONLY",

    "history_method":
        "fixtures?team=ID&from=DATE&to=DATE",

    "last_parameter_used":
        False,

    "history_days":
        HISTORY_DAYS,

    "max_games":
        MAX_GAMES,

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
# 21. FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("✅ TEST COMPLETE")
print("=" * 70)

print(
    "Champions League matches "
    f"evaluated: "
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
        "Home Data : "
        f"{match['h_stats'].get('reason')}"
    )

    print(
        "Away Data : "
        f"{match['a_stats'].get('reason')}"
    )

    print(
        "-" * 70
    )


print()
print(
    "💾 Saved to: "
    "matches_data.json"
)

print()
print(
    "🔎 IMPORTANT:"
)

print(
    "This version DOES NOT use "
    "fixtures?team=ID&last=15."
)

print(
    "L5 data is collected using "
    "from/to date range and filtered "
    "locally in Python."
)

print(
    "No fake 50% fallback values "
    "are generated."
)

print(
    "If historical data is insufficient, "
    "the model returns DATA_UNAVAILABLE."
)
