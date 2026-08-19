import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests


# ============================================================
# PRE-MATCH OVER/UNDER INTELLIGENCE PRO
# ============================================================
#
# IMPORTANT:
# - No xG API calls
# - No fake fallback probability
# - Home/Away L5 only
# - Over 2.5 requires BOTH Home BTTS >= 60 AND Away BTTS >= 60
# - Under 2.5 requires BOTH Home BTTS < 50 AND Away BTTS < 50
# - API hard stop at 80 calls/run
# - API also stops when remaining daily quota <= 20
# - History is cached
# ============================================================


# ============================================================
# 1. API CONFIGURATION
# ============================================================

API_BASE = "https://v3.football.api-sports.io"

# ------------------------------------------------------------
# FREE PLAN SAFETY
# ------------------------------------------------------------
#
# API-SPORTS Free:
# 100 requests/day
#
# We intentionally stop BEFORE exhausting the quota.
#
# Maximum calls from this script in one run:
# 80
#
# If API reports only 20 or fewer requests remaining:
# STOP immediately.
# ------------------------------------------------------------

MAX_API_CALLS_PER_RUN = 80
MIN_REMAINING_QUOTA = 20

# API-SPORTS Free plan is 10 requests/minute.
# 7 seconds between real API requests keeps us safely below that.
API_DELAY_SECONDS = 7


# ============================================================
# 2. MATCH WINDOW
# ============================================================

# Number of calendar days to scan starting from today.
#
# 2 means:
#   today + tomorrow
#
# 3 means:
#   today + tomorrow + day after tomorrow
#
# Weekend scanning is easier with 3.
LOOKAHEAD_DAYS = 3


# Maximum matches sent into model evaluation.
#
# 20 matches can normally fit comfortably under the 80-call
# safety budget because team histories are cached by team+season.
#
# If 20 matches contain 40 unique teams:
#   1 fixture request
#   + up to 40 history requests
#   = ~41 calls
#
# So 20 is intentionally conservative.
MAX_MATCHES = 20


# ============================================================
# 3. HISTORICAL SEASON
# ============================================================
#
# Your testing proved:
#
# season=2024
# works on the Free plan.
#
# API error for 2025/2026:
# "Free plans do not have access to this season,
#  try from 2022 to 2024."
#
# Therefore:
# 2024 is used as historical proxy.
#
# IMPORTANT:
# This is NOT current 2026 form.
# ============================================================

HISTORY_SEASON = 2024


# ============================================================
# 4. FILES
# ============================================================

CACHE_FILE = "team_history_cache.json"
OUTPUT_FILE = "matches_data.json"


# ============================================================
# 5. TIMEZONE
# ============================================================

MMT_TZ = timezone(
    timedelta(hours=6, minutes=30)
)


# ============================================================
# 6. LEAGUE FILTER
# ============================================================
#
# IMPORTANT:
# These are API-FOOTBALL V3 league IDs.
#
# We do NOT call /leagues just to discover IDs.
# That saves API requests.
# ============================================================


LEAGUES = {

    # --------------------------------------------------------
    # COUNTRIES / LEAGUES FROM YOUR LIST
    # --------------------------------------------------------

    128: "Argentina - Liga Profesional",

    188: "Australia - A-League",

    218: "Austria - Bundesliga",

    144: "Belgium - Pro League",

    71: "Brazil - Serie A",

    265: "Chile - Primera División",

    169: "China - Super League",

    239: "Colombia - Primera A",

    210: "Croatia - HNL",

    119: "Denmark - Superliga",

    242: "Ecuador - Liga Pro",

    197: "Greece - Super League",

    98: "Japan - J1 League",

    262: "Mexico - Liga MX",

    88: "Netherlands - Eredivisie",

    103: "Norway - Eliteserien",

    281: "Peru - Liga 1",

    106: "Poland - Ekstraklasa",

    94: "Portugal - Primeira Liga",

    307: "Saudi Arabia - Saudi Pro League",

    179: "Scotland - Premiership",

    113: "Sweden - Allsvenskan",

    207: "Switzerland - Super League",

    203: "Turkey - Süper Lig",

    253: "USA - MLS",


    # --------------------------------------------------------
    # ENGLAND
    # --------------------------------------------------------

    39: "England - Premier League",
    40: "England - Championship",


    # --------------------------------------------------------
    # SPAIN
    # --------------------------------------------------------

    140: "Spain - La Liga",
    141: "Spain - La Liga 2",


    # --------------------------------------------------------
    # FRANCE
    # --------------------------------------------------------

    61: "France - Ligue 1",
    62: "France - Ligue 2",


    # --------------------------------------------------------
    # GERMANY
    # --------------------------------------------------------

    78: "Germany - Bundesliga",
    79: "Germany - 2. Bundesliga",


    # --------------------------------------------------------
    # ITALY
    # --------------------------------------------------------

    135: "Italy - Serie A",
    136: "Italy - Serie B",


    # --------------------------------------------------------
    # UEFA EUROPEAN CUPS
    # --------------------------------------------------------

    2: "UEFA Champions League",
    3: "UEFA Europa League",
    848: "UEFA Conference League",


    # --------------------------------------------------------
    # MAJOR DOMESTIC CUPS
    # --------------------------------------------------------

    45: "England - FA Cup",
    143: "Spain - Copa del Rey",
    66: "France - Coupe de France",
    81: "Germany - DFB Pokal",
    137: "Italy - Coppa Italia",

}


TARGET_LEAGUE_IDS = set(
    LEAGUES.keys()
)


# ============================================================
# 7. API KEY
# ============================================================

raw_keys = os.environ.get(
    "API_KEYS_POOL",
    ""
).strip()


if not raw_keys:

    raise RuntimeError(
        "\n"
        "❌ API_KEYS_POOL is not configured.\n\n"
        "GitHub Repository → Settings → Secrets and variables\n"
        "→ Actions → New repository secret\n\n"
        "Name:\n"
        "API_KEYS_POOL\n\n"
        "Value:\n"
        "YOUR_API_KEY\n"
    )


API_KEYS = [
    key.strip()
    for key in raw_keys.split(",")
    if key.strip()
]


if not API_KEYS:

    raise RuntimeError(
        "❌ No valid API key found."
    )


# ------------------------------------------------------------
# IMPORTANT:
# We do NOT rotate keys simply to bypass quota.
#
# The pool is kept only for controlled failover.
# The global 80-call safety limit still applies.
# ------------------------------------------------------------

current_key_index = 0


print("=" * 72)
print("🔐 API CONFIGURATION")
print("=" * 72)

print(
    f"API Keys Loaded : {len(API_KEYS)}"
)

print(
    "Keys are NOT printed."
)

print(
    f"Hard Run Limit  : {MAX_API_CALLS_PER_RUN} calls"
)

print(
    f"Quota Stop      : remaining <= {MIN_REMAINING_QUOTA}"
)

print("=" * 72)


# ============================================================
# 8. API STATE
# ============================================================

api_calls_this_run = 0
remaining_quota = None
minute_remaining = None


# ============================================================
# 9. ACTIVE KEY
# ============================================================

def get_active_key():

    return API_KEYS[
        current_key_index
    ]


# ============================================================
# 10. API REQUEST
# ============================================================

def api_request(
    endpoint,
    params=None,
    purpose=""
):

    global api_calls_this_run
    global current_key_index
    global remaining_quota
    global minute_remaining


    # --------------------------------------------------------
    # HARD 80 CALL STOP
    # --------------------------------------------------------

    if api_calls_this_run >= MAX_API_CALLS_PER_RUN:

        print("\n" + "🛑" * 20)
        print("🛑 API SAFETY STOP")
        print(
            f"Run reached "
            f"{MAX_API_CALLS_PER_RUN} API calls."
        )
        print("🛑 No further API request will be made.")
        print("🛑" * 20)

        return None


    # --------------------------------------------------------
    # DAILY QUOTA SAFETY
    # --------------------------------------------------------

    if (
        remaining_quota is not None
        and remaining_quota <= MIN_REMAINING_QUOTA
    ):

        print("\n" + "🛑" * 20)
        print("🛑 DAILY QUOTA SAFETY STOP")
        print(
            f"Remaining quota = "
            f"{remaining_quota}"
        )
        print(
            f"Safety reserve = "
            f"{MIN_REMAINING_QUOTA}"
        )
        print("🛑 No further API request will be made.")
        print("🛑" * 20)

        return None


    url = f"{API_BASE}/{endpoint}"


    headers = {
        "x-apisports-key": get_active_key()
    }


    # --------------------------------------------------------
    # DELAY
    # --------------------------------------------------------

    if api_calls_this_run > 0:

        print(
            f"\n⏳ Waiting "
            f"{API_DELAY_SECONDS}s "
            f"before next API request..."
        )

        time.sleep(
            API_DELAY_SECONDS
        )


    # --------------------------------------------------------
    # REQUEST COUNTER
    # --------------------------------------------------------

    api_calls_this_run += 1


    print("\n" + "-" * 72)
    print("🌐 API REQUEST")
    print("-" * 72)

    if purpose:

        print(
            f"Purpose : {purpose}"
        )

    print(
        f"Endpoint: {endpoint}"
    )

    print(
        f"Call #{api_calls_this_run}"
        f"/{MAX_API_CALLS_PER_RUN}"
    )


    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
        )


        # ----------------------------------------------------
        # DAILY QUOTA HEADER
        # ----------------------------------------------------

        daily_header_names = [
            "x-ratelimit-requests-remaining",
            "X-RateLimit-Requests-Remaining",
        ]


        for header_name in daily_header_names:

            value = response.headers.get(
                header_name
            )

            if value is not None:

                try:

                    remaining_quota = int(
                        value
                    )

                except ValueError:

                    pass

                break


        # ----------------------------------------------------
        # MINUTE RATE HEADER
        # ----------------------------------------------------

        minute_header_names = [
            "X-RateLimit-Remaining",
            "x-ratelimit-remaining",
        ]


        for header_name in minute_header_names:

            value = response.headers.get(
                header_name
            )

            if value is not None:

                try:

                    minute_remaining = int(
                        value
                    )

                except ValueError:

                    pass

                break


        print(
            f"HTTP Status: "
            f"{response.status_code}"
        )


        if remaining_quota is not None:

            print(
                f"Daily Remaining: "
                f"{remaining_quota}"
            )


        if minute_remaining is not None:

            print(
                f"Minute Remaining: "
                f"{minute_remaining}"
            )


        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------

        if response.status_code == 429:

            print(
                "🛑 HTTP 429 RATE LIMIT"
            )

            print(
                "🛑 Stopping this run."
            )

            return None


        # ----------------------------------------------------
        # AUTH / PERMISSION
        # ----------------------------------------------------

        if response.status_code in [
            401,
            403
        ]:

            print(
                "❌ Authentication / permission error."
            )

            return None


        # ----------------------------------------------------
        # OTHER HTTP ERRORS
        # ----------------------------------------------------

        if response.status_code != 200:

            print(
                "❌ HTTP ERROR"
            )

            return None


        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        try:

            data = response.json()

        except Exception:

            print(
                "❌ Invalid JSON response."
            )

            return None


        errors = data.get(
            "errors",
            {}
        )

        results = data.get(
            "results",
            0
        )


        print(
            f"API Results: "
            f"{results}"
        )

        print(
            f"API Errors : "
            f"{errors}"
        )


        # ----------------------------------------------------
        # API ERROR
        # ----------------------------------------------------

        if errors:

            print(
                "❌ API returned errors."
            )

            return None


        print(
            "✅ API DATA RECEIVED"
        )


        # ----------------------------------------------------
        # EXTRA SAFETY AFTER REQUEST
        # ----------------------------------------------------

        if (
            remaining_quota is not None
            and remaining_quota
            <= MIN_REMAINING_QUOTA
        ):

            print(
                "\n⚠️ Daily quota reserve reached."
            )

            print(
                f"Remaining: "
                f"{remaining_quota}"
            )

            print(
                "No additional API calls will be made."
            )


        return data


    except requests.RequestException as exc:

        print(
            f"❌ CONNECTION ERROR: "
            f"{exc}"
        )

        return None


# ============================================================
# 11. CACHE
# ============================================================

def load_cache():

    if not os.path.exists(
        CACHE_FILE
    ):

        return {}


    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )


        if isinstance(
            data,
            dict
        ):

            return data


    except Exception as exc:

        print(
            f"⚠️ Cache read error: "
            f"{exc}"
        )


    return {}


def save_cache(cache):

    try:

        with open(
            CACHE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                cache,
                file,
                indent=2,
                ensure_ascii=False
            )


        print(
            f"💾 Cache saved: "
            f"{CACHE_FILE}"
        )


    except Exception as exc:

        print(
            f"⚠️ Cache save error: "
            f"{exc}"
        )


history_cache = load_cache()


# ============================================================
# 12. CURRENT TIME
# ============================================================

now_mmt = datetime.now(
    MMT_TZ
)


# ------------------------------------------------------------
# Scan from today 00:00 MMT
# through LOOKAHEAD_DAYS
# ------------------------------------------------------------

window_start = datetime(
    now_mmt.year,
    now_mmt.month,
    now_mmt.day,
    0,
    0,
    0,
    tzinfo=MMT_TZ
)


window_end = (
    window_start
    + timedelta(
        days=LOOKAHEAD_DAYS
    )
)


date_from = window_start.strftime(
    "%Y-%m-%d"
)

date_to = (
    window_end
    - timedelta(days=1)
).strftime(
    "%Y-%m-%d"
)


# ============================================================
# 13. FETCH FIXTURES — ONE API CALL
# ============================================================
#
# IMPORTANT OPTIMIZATION:
#
# Old:
#   today's fixtures = 1 call
#   tomorrow's fixtures = 1 call
#
# New:
#   date range = 1 call
#
# This saves one API request every run.
# ============================================================

print("\n" + "=" * 72)
print("📅 FIXTURE SCAN")
print("=" * 72)

print(
    f"From : {date_from}"
)

print(
    f"To   : {date_to}"
)

print(
    f"Lookahead days: "
    f"{LOOKAHEAD_DAYS}"
)

print(
    f"Target leagues: "
    f"{len(TARGET_LEAGUE_IDS)}"
)

print("=" * 72)


fixture_data = api_request(
    "fixtures",
    params={
        "from": date_from,
        "to": date_to,
        "timezone": "Asia/Yangon",
    },
    purpose=(
        "Upcoming fixtures "
        f"{date_from} to {date_to}"
    ),
)


if fixture_data is None:

    print(
        "❌ Fixture request failed."
    )

    all_fixtures = []

else:

    all_fixtures = (
        fixture_data.get(
            "response",
            []
        )
    )


print(
    f"\nRaw fixtures received: "
    f"{len(all_fixtures)}"
)


# ============================================================
# 14. SELECT TARGET LEAGUES
# ============================================================

selected_fixtures = []

seen_ids = set()


for fixture in all_fixtures:

    fixture_data_item = fixture.get(
        "fixture",
        {}
    )

    league_data = fixture.get(
        "league",
        {}
    )

    teams_data = fixture.get(
        "teams",
        {}
    )


    fixture_id = fixture_data_item.get(
        "id"
    )


    if not fixture_id:

        continue


    if fixture_id in seen_ids:

        continue


    seen_ids.add(
        fixture_id
    )


    # --------------------------------------------------------
    # LEAGUE FILTER
    # --------------------------------------------------------

    league_id = league_data.get(
        "id"
    )


    if league_id not in TARGET_LEAGUE_IDS:

        continue


    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = (
        fixture_data_item
        .get("status", {})
        .get("short")
    )


    if status not in [
        "NS",
        "TBD"
    ]:

        continue


    # --------------------------------------------------------
    # FIXTURE DATE
    # --------------------------------------------------------

    fixture_date = (
        fixture_data_item
        .get("date")
    )


    if not fixture_date:

        continue


    try:

        fixture_dt = (
            datetime
            .fromisoformat(
                fixture_date
            )
        )

    except Exception:

        continue


    if fixture_dt.tzinfo is None:

        fixture_dt = (
            fixture_dt
            .replace(
                tzinfo=timezone.utc
            )
        )


    # --------------------------------------------------------
    # EXACT WINDOW
    # --------------------------------------------------------

    if not (
        window_start
        <= fixture_dt
        < window_end
    ):

        continue


    # --------------------------------------------------------
    # TEAMS
    # --------------------------------------------------------

    home = teams_data.get(
        "home",
        {}
    )

    away = teams_data.get(
        "away",
        {}
    )


    if not home.get("id"):

        continue


    if not away.get("id"):

        continue


    selected_fixtures.append(
        fixture
    )


# ============================================================
# 15. SORT TARGET MATCHES
# ============================================================

selected_fixtures.sort(
    key=lambda x:
        x["fixture"]["date"]
)


# ------------------------------------------------------------
# Limit number of matches.
#
# The purpose is to keep history API usage under control.
# ------------------------------------------------------------

selected_fixtures = (
    selected_fixtures[
        :MAX_MATCHES
    ]
)


print("\n" + "=" * 72)
print("🏆 TARGET FIXTURES")
print("=" * 72)

print(
    f"Selected matches: "
    f"{len(selected_fixtures)}"
)

print("=" * 72)


for index, fixture in enumerate(
    selected_fixtures,
    1
):

    league_id = (
        fixture["league"]["id"]
    )

    league_name = (
        fixture["league"]["name"]
    )

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
        f"{index:02d}. "
        f"[{league_id}] "
        f"{league_name} | "
        f"{home_name} vs {away_name} | "
        f"{fixture_date}"
    )


# ============================================================
# 16. TEAM HISTORY
# ============================================================

def get_team_history(
    team_id,
    team_name,
    venue
):

    # --------------------------------------------------------
    # FULL TEAM SEASON CACHE
    #
    # One API response contains both HOME and AWAY matches.
    #
    # Therefore:
    #
    # Team history API call = once per team/season
    #
    # NOT once per venue.
    # --------------------------------------------------------

    cache_key = (
        f"{team_id}_{HISTORY_SEASON}"
    )


    # --------------------------------------------------------
    # CACHE HIT
    # --------------------------------------------------------

    if cache_key in history_cache:

        print("\n" + "=" * 72)
        print("📦 USING CACHED TEAM HISTORY")
        print("=" * 72)

        print(
            f"Team   : {team_name}"
        )

        print(
            f"Team ID: {team_id}"
        )

        print(
            f"Season : {HISTORY_SEASON}"
        )

        fixtures = (
            history_cache[
                cache_key
            ]
        )


    # --------------------------------------------------------
    # API REQUEST
    # --------------------------------------------------------

    else:

        print("\n" + "=" * 72)
        print("📊 TEAM HISTORY REQUEST")
        print("=" * 72)

        print(
            f"Team   : {team_name}"
        )

        print(
            f"Team ID: {team_id}"
        )

        print(
            f"Season : {HISTORY_SEASON}"
        )

        print(
            "Method : team + season"
        )


        data = api_request(
            "fixtures",
            params={
                "team": team_id,
                "season": HISTORY_SEASON,
            },
            purpose=(
                f"{team_name} "
                f"historical fixtures "
                f"season {HISTORY_SEASON}"
            ),
        )


        if data is None:

            return {
                "status": "API_ERROR",
                "available": False,
                "reason": "API_ERROR",
                "matches": [],
                "over_pct": None,
                "under_pct": None,
                "btts_pct": None,
                "gf_avg": None,
                "ga_avg": None,
                "sample_size": 0,
            }


        fixtures = (
            data.get(
                "response",
                []
            )
        )


        history_cache[
            cache_key
        ] = fixtures


        save_cache(
            history_cache
        )


    # ========================================================
    # FILTER FINISHED MATCHES
    # ========================================================

    finished = []


    for fixture in fixtures:

        status = (
            fixture
            .get("fixture", {})
            .get("status", {})
            .get("short")
        )


        if status not in [
            "FT",
            "AET",
            "PEN"
        ]:

            continue


        home = (
            fixture
            .get("teams", {})
            .get("home", {})
        )

        away = (
            fixture
            .get("teams", {})
            .get("away", {})
        )


        goals = fixture.get(
            "goals",
            {}
        )


        home_id = home.get(
            "id"
        )

        away_id = away.get(
            "id"
        )


        home_goals = goals.get(
            "home"
        )

        away_goals = goals.get(
            "away"
        )


        if (
            home_goals is None
            or
            away_goals is None
        ):

            continue


        # ----------------------------------------------------
        # VENUE FILTER
        # ----------------------------------------------------

        if venue == "HOME":

            if home_id != team_id:

                continue


        elif venue == "AWAY":

            if away_id != team_id:

                continue


        finished.append(
            {
                "date": (
                    fixture
                    .get("fixture", {})
                    .get("date", "")
                ),

                "home": home.get(
                    "name",
                    "Unknown"
                ),

                "away": away.get(
                    "name",
                    "Unknown"
                ),

                "home_id": home_id,

                "away_id": away_id,

                "gh": int(
                    home_goals
                ),

                "ga": int(
                    away_goals
                ),
            }
        )


    # --------------------------------------------------------
    # NEWEST FIRST
    # --------------------------------------------------------

    finished.sort(
        key=lambda x:
            x["date"],
        reverse=True
    )


    selected = finished[:5]


    # ========================================================
    # NOT ENOUGH DATA
    # ========================================================

    if len(selected) < 5:

        print(
            f"⚠️ {team_name} "
            f"({venue}) → "
            f"{len(selected)}/5"
        )


        return {
            "status": "INSUFFICIENT_L5_DATA",
            "available": False,
            "reason": (
                "INSUFFICIENT_L5_DATA"
            ),
            "matches": selected,
            "over_pct": None,
            "under_pct": None,
            "btts_pct": None,
            "gf_avg": None,
            "ga_avg": None,
            "sample_size": len(selected),
        }


    # ========================================================
    # CALCULATE STATS
    # ========================================================

    over_count = 0
    btts_count = 0

    gf_total = 0
    ga_total = 0

    scorelines = []


    for match in selected:

        total_goals = (
            match["gh"]
            +
            match["ga"]
        )


        # ----------------------------------------------------
        # OVER 2.5
        # ----------------------------------------------------

        if total_goals >= 3:

            over_count += 1


        # ----------------------------------------------------
        # BTTS
        # ----------------------------------------------------

        if (
            match["gh"] > 0
            and
            match["ga"] > 0
        ):

            btts_count += 1


        # ----------------------------------------------------
        # TEAM GF / GA
        # ----------------------------------------------------

        if (
            match["home_id"]
            == team_id
        ):

            gf_total += (
                match["gh"]
            )

            ga_total += (
                match["ga"]
            )

        else:

            gf_total += (
                match["ga"]
            )

            ga_total += (
                match["gh"]
            )


        # ----------------------------------------------------
        # SCORELINE
        # ----------------------------------------------------

        scorelines.append(
            {
                "date":
                    match["date"][:10],

                "home":
                    match["home"],

                "away":
                    match["away"],

                "gh":
                    match["gh"],

                "ga":
                    match["ga"],

                "tot":
                    total_goals,
            }
        )


    count = len(
        selected
    )


    return {
        "status":
            "PROXY_2024_25",

        "available":
            True,

        "reason":
            "PROXY_2024_25",

        "data_source":
            "API-SPORTS 2024 season "
            "(historical proxy; "
            "NOT current 2026 form)",

        "sample_size":
            count,

        "over_pct":
            round(
                over_count
                / count
                * 100,
                1
            ),

        "under_pct":
            round(
                (
                    count
                    -
                    over_count
                )
                / count
                * 100,
                1
            ),

        "btts_pct":
            round(
                btts_count
                / count
                * 100,
                1
            ),

        "gf_avg":
            round(
                gf_total
                / count,
                2
            ),

        "ga_avg":
            round(
                ga_total
                / count,
                2
            ),

        "scorelines":
            scorelines,
    }


# ============================================================
# 17. MODEL
# ============================================================
#
# NO xG
#
# OVER 2.5 REQUIREMENTS
#
# Home L5 O2.5 >= 60
# Away L5 O2.5 >= 60
#
# Home GF > 1.5
# Home GA > 1.0
#
# Away GF > 1.0
# Away GA > 1.0
#
# Home BTTS >= 60
# Away BTTS >= 60
#
# Model Edge >= 5
#
#
# UNDER 2.5 REQUIREMENTS
#
# Home L5 U2.5 >= 60
# Away L5 U2.5 >= 60
#
# Home GF < 1.3
# Home GA < 1.0
#
# Away GF < 1.1
# Away GA < 1.2
#
# Home BTTS < 50
# Away BTTS < 50
#
# Model Edge >= 5
# ============================================================


def calculate_model(
    home_stats,
    away_stats
):

    # ========================================================
    # DATA CHECK
    # ========================================================

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

            "probability":
                None,

            "edge":
                None,

            "model_status":
                "INSUFFICIENT_DATA",
        }


    if (
        home_stats.get(
            "sample_size",
            0
        ) < 5
        or
        away_stats.get(
            "sample_size",
            0
        ) < 5
    ):

        return {
            "signal":
                "DATA_UNAVAILABLE",

            "probability":
                None,

            "edge":
                None,

            "model_status":
                "INSUFFICIENT_L5_DATA",
        }


    # ========================================================
    # COMMON VALUES
    # ========================================================

    home_over = (
        home_stats["over_pct"]
    )

    away_over = (
        away_stats["over_pct"]
    )

    home_under = (
        home_stats["under_pct"]
    )

    away_under = (
        away_stats["under_pct"]
    )

    home_btts = (
        home_stats["btts_pct"]
    )

    away_btts = (
        away_stats["btts_pct"]
    )


    # ========================================================
    # GOAL ENVIRONMENT
    # ========================================================

    combined_gf = (
        home_stats["gf_avg"]
        +
        away_stats["gf_avg"]
    )

    combined_ga = (
        home_stats["ga_avg"]
        +
        away_stats["ga_avg"]
    )


    total_goal_environment = (
        combined_gf
        +
        combined_ga
    )


    # ========================================================
    # OVER PROBABILITY SCORE
    # ========================================================
    #
    # This is NOT bookmaker probability.
    #
    # It is a model score based only on available
    # historical variables.
    #
    # No xG.
    # ========================================================

    over_goal_score = min(
        100,
        (
            total_goal_environment
            / 5.5
            * 100
        )
    )


    over_probability = (
        home_over * 0.30
        +
        away_over * 0.30
        +
        home_btts * 0.10
        +
        away_btts * 0.10
        +
        over_goal_score * 0.20
    )


    over_probability = round(
        max(
            0,
            min(
                100,
                over_probability
            )
        ),
        1
    )


    # ========================================================
    # UNDER PROBABILITY SCORE
    # ========================================================

    under_goal_score = max(
        0,
        min(
            100,
            100
            -
            (
                total_goal_environment
                / 5.5
                * 100
            )
        )
    )


    under_btts_score = (
        (
            100
            -
            home_btts
        )
        +
        (
            100
            -
            away_btts
        )
    ) / 2


    under_probability = (
        home_under * 0.30
        +
        away_under * 0.30
        +
        under_btts_score * 0.20
        +
        under_goal_score * 0.20
    )


    under_probability = round(
        max(
            0,
            min(
                100,
                under_probability
            )
        ),
        1
    )


    # ========================================================
    # EDGES
    # ========================================================

    over_edge = round(
        over_probability
        - 60,
        1
    )


    under_edge = round(
        under_probability
        - 60,
        1
    )


    # ========================================================
    # STRICT OVER CONDITIONS
    # ========================================================

    strong_over = (

        # Home + Away L5 O2.5
        home_over >= 60
        and
        away_over >= 60

        # Home attack
        and
        home_stats["gf_avg"] > 1.5

        # Home defensive openness
        and
        home_stats["ga_avg"] > 1.0

        # Away attack
        and
        away_stats["gf_avg"] > 1.0

        # Away defensive openness
        and
        away_stats["ga_avg"] > 1.0

        # BOTH BTTS must be >= 60
        and
        home_btts >= 60
        and
        away_btts >= 60

        # Model edge
        and
        over_edge >= 5
    )


    # ========================================================
    # STRICT UNDER CONDITIONS
    # ========================================================

    strong_under = (

        # Home + Away L5 U2.5
        home_under >= 60
        and
        away_under >= 60

        # Home GF
        and
        home_stats["gf_avg"] < 1.3

        # Home GA
        and
        home_stats["ga_avg"] < 1.0

        # Away GF
        and
        away_stats["gf_avg"] < 1.1

        # Away GA
        and
        away_stats["ga_avg"] < 1.2

        # BOTH BTTS must be < 50
        and
        home_btts < 50
        and
        away_btts < 50

        # Model edge
        and
        under_edge >= 5
    )


    # ========================================================
    # SIGNAL DECISION
    # ========================================================

    if strong_over:

        return {
            "signal":
                "OVER_2_5",

            "probability":
                over_probability,

            "edge":
                over_edge,

            "model_status":
                "STRICT_OVER_MODEL",
        }


    if strong_under:

        return {
            "signal":
                "UNDER_2_5",

            "probability":
                under_probability,

            "edge":
                under_edge,

            "model_status":
                "STRICT_UNDER_MODEL",
        }


    # ========================================================
    # NEUTRAL
    # ========================================================

    # Show whichever probability is stronger,
    # but DO NOT turn it into a target signal.
    #
    # This is important.
    #
    # A match can have 70% model score but fail one
    # critical rule. It remains NEUTRAL.
    # ========================================================

    if (
        over_probability
        >=
        under_probability
    ):

        neutral_probability = (
            over_probability
        )

        neutral_edge = (
            over_edge
        )

    else:

        neutral_probability = (
            under_probability
        )

        neutral_edge = (
            under_edge
        )


    return {
        "signal":
            "NEUTRAL",

        "probability":
            neutral_probability,

        "edge":
            neutral_edge,

        "model_status":
            "STRICT_RULES_NOT_MET",
    }


# ============================================================
# 18. EVALUATION
# ============================================================

evaluated_matches = []


# ------------------------------------------------------------
# Unique teams
# ------------------------------------------------------------

unique_teams = set()


for fixture in selected_fixtures:

    unique_teams.add(
        fixture["teams"]["home"]["id"]
    )

    unique_teams.add(
        fixture["teams"]["away"]["id"]
    )


print("\n" + "=" * 72)
print("📊 API USAGE PLAN")
print("=" * 72)

print(
    f"Selected matches : "
    f"{len(selected_fixtures)}"
)

print(
    f"Unique teams     : "
    f"{len(unique_teams)}"
)

print(
    f"Hard API limit   : "
    f"{MAX_API_CALLS_PER_RUN}"
)

print(
    f"Reserve quota    : "
    f"{MIN_REMAINING_QUOTA}"
)

print(
    "Team histories are cached."
)

print(
    "One team/season history = one API request."
)

print("=" * 72)


# ============================================================
# 19. TEAM HISTORY MEMORY
# ============================================================

team_history_memory = {}


# ============================================================
# 20. MATCH EVALUATION
# ============================================================

for index, fixture in enumerate(
    selected_fixtures,
    1
):

    home_id = (
        fixture["teams"]["home"]["id"]
    )

    away_id = (
        fixture["teams"]["away"]["id"]
    )

    home_name = (
        fixture["teams"]["home"]["name"]
    )

    away_name = (
        fixture["teams"]["away"]["name"]
    )

    league_id = (
        fixture["league"]["id"]
    )

    league_name = (
        fixture["league"]["name"]
    )


    print("\n" + "#" * 72)

    print(
        f"🎯 EVALUATING MATCH "
        f"{index}/"
        f"{len(selected_fixtures)}"
    )

    print("#" * 72)


    print(
        f"\n🏆 {league_name}"
    )

    print(
        f"⚽ {home_name} "
        f"vs "
        f"{away_name}"
    )


    # ========================================================
    # STOP IF HARD LIMIT REACHED
    # ========================================================

    if (
        api_calls_this_run
        >=
        MAX_API_CALLS_PER_RUN
    ):

        print(
            "\n🛑 80-call safety limit reached."
        )

        break


    # ========================================================
    # HOME HISTORY
    # ========================================================

    home_cache_key = (
        f"{home_id}_HOME_{HISTORY_SEASON}"
    )


    if (
        home_cache_key
        not in
        team_history_memory
    ):

        # ----------------------------------------------------
        # Full team history is cached under team_id + season.
        # ----------------------------------------------------

        team_history_memory[
            home_cache_key
        ] = get_team_history(
            home_id,
            home_name,
            "HOME"
        )


    home_stats = (
        team_history_memory[
            home_cache_key
        ]
    )


    # ========================================================
    # AWAY HISTORY
    # ========================================================

    away_cache_key = (
        f"{away_id}_AWAY_{HISTORY_SEASON}"
    )


    if (
        away_cache_key
        not in
        team_history_memory
    ):

        team_history_memory[
            away_cache_key
        ] = get_team_history(
            away_id,
            away_name,
            "AWAY"
        )


    away_stats = (
        team_history_memory[
            away_cache_key
        ]
    )


    # ========================================================
    # MODEL
    # ========================================================

    model = calculate_model(
        home_stats,
        away_stats
    )


    print("\n" + "-" * 72)
    print("🎯 MODEL RESULT")
    print("-" * 72)

    print(
        f"Signal      : "
        f"{model['signal']}"
    )

    print(
        f"Probability : "
        f"{model['probability']}"
    )

    print(
        f"Edge        : "
        f"{model['edge']}"
    )

    print(
        f"Model Status: "
        f"{model['model_status']}"
    )


    # ========================================================
    # DATE / TIME
    # ========================================================

    fixture_date = (
        fixture["fixture"]["date"]
    )


    try:

        local_dt = (
            datetime
            .fromisoformat(
                fixture_date
            )
            .astimezone(
                MMT_TZ
            )
        )


        display_date = (
            local_dt.strftime(
                "%Y-%m-%d"
            )
        )


        display_time = (
            local_dt.strftime(
                "%H:%M"
            )
        )


    except Exception:

        display_date = (
            fixture_date[:10]
        )

        display_time = (
            fixture_date[11:16]
        )


    # ========================================================
    # OUTPUT OBJECT
    # ========================================================

    evaluated_matches.append(
        {
            "fixture_id":
                fixture["fixture"]["id"],

            "league_id":
                league_id,

            "league":
                league_name,

            "country":
                fixture["league"].get(
                    "country",
                    ""
                ),

            "home":
                home_name,

            "away":
                away_name,

            "date":
                display_date,

            "time":
                display_time,

            "status":
                fixture["fixture"]
                ["status"]
                ["short"],

            "signal":
                model["signal"],

            "prob":
                model["probability"],

            "edge":
                model["edge"],

            "model_status":
                model["model_status"],

            "xg_used":
                False,

            "data_warning":
                (
                    "Historical proxy from "
                    "2024 season. "
                    "NOT current 2026 form."
                ),

            "h_stats":
                home_stats,

            "a_stats":
                away_stats,
        }
    )


# ============================================================
# 21. SIGNAL SORT
# ============================================================

def signal_priority(
    signal
):

    if signal == "OVER_2_5":

        return 0


    if signal == "UNDER_2_5":

        return 1


    if signal == "NEUTRAL":

        return 2


    return 3


evaluated_matches.sort(
    key=lambda x: (
        signal_priority(
            x["signal"]
        ),
        x["date"],
        x["time"],
    )
)


# ============================================================
# 22. SAVE OUTPUT
# ============================================================

output = {

    "updated_at":
        now_mmt.strftime(
            "%Y-%m-%d %H:%M MMT"
        ),

    "window_range":
        (
            f"{date_from}"
            f" - "
            f"{date_to}"
            f" MMT"
        ),

    "mode":
        "MULTI_LEAGUE_PREMATCH",

    "league_filter":
        {
            str(k): v
            for k, v in LEAGUES.items()
        },

    "history_season":
        HISTORY_SEASON,

    "history_data_type":
        "2024 historical proxy",

    "current_form_available":
        False,

    "xg_used":
        False,

    "model_rules":
        {
            "over_2_5":
                {
                    "home_over_pct":
                        ">= 60",

                    "away_over_pct":
                        ">= 60",

                    "home_gf_avg":
                        "> 1.5",

                    "home_ga_avg":
                        "> 1.0",

                    "away_gf_avg":
                        "> 1.0",

                    "away_ga_avg":
                        "> 1.0",

                    "home_btts_pct":
                        ">= 60",

                    "away_btts_pct":
                        ">= 60",

                    "edge":
                        ">= 5",

                    "xg":
                        False,
                },

            "under_2_5":
                {
                    "home_under_pct":
                        ">= 60",

                    "away_under_pct":
                        ">= 60",

                    "home_gf_avg":
                        "< 1.3",

                    "home_ga_avg":
                        "< 1.0",

                    "away_gf_avg":
                        "< 1.1",

                    "away_ga_avg":
                        "< 1.2",

                    "home_btts_pct":
                        "< 50",

                    "away_btts_pct":
                        "< 50",

                    "edge":
                        ">= 5",

                    "xg":
                        False,
                },
        },

    "api_calls_this_run":
        api_calls_this_run,

    "remaining_quota":
        remaining_quota,

    "total_matches":
        len(
            evaluated_matches
        ),

    "matches":
        evaluated_matches,

    "safety":
        {
            "hard_call_limit":
                MAX_API_CALLS_PER_RUN,

            "minimum_remaining_quota":
                MIN_REMAINING_QUOTA,

            "api_delay_seconds":
                API_DELAY_SECONDS,

            "history_cache":
                True,

            "xg_api_calls":
                False,
        },
}


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# 23. FINAL REPORT
# ============================================================

print("\n" + "=" * 72)
print("✅ FETCH COMPLETE")
print("=" * 72)


print(
    f"Selected fixtures : "
    f"{len(selected_fixtures)}"
)


print(
    f"Evaluated matches : "
    f"{len(evaluated_matches)}"
)


print(
    f"API calls used    : "
    f"{api_calls_this_run}"
)


if remaining_quota is not None:

    print(
        f"Remaining quota  : "
        f"{remaining_quota}"
    )


print(
    f"Saved to          : "
    f"{OUTPUT_FILE}"
)


print("\n" + "-" * 72)


for match in evaluated_matches:

    print(
        f"\n🏆 {match['league']}"
    )

    print(
        f"⚽ {match['home']} "
        f"vs "
        f"{match['away']}"
    )

    print(
        f"Signal      : "
        f"{match['signal']}"
    )

    print(
        f"Probability : "
        f"{match['prob']}"
    )

    print(
        f"Edge        : "
        f"{match['edge']}"
    )

    print(
        f"Model Status: "
        f"{match['model_status']}"
    )


print("\n" + "=" * 72)
print("🛡️ API SAFETY")
print("=" * 72)


print(
    "✅ Hard stop at 80 API calls."
)


print(
    f"✅ Stop when remaining quota <= "
    f"{MIN_REMAINING_QUOTA}."
)


print(
    "✅ Team history is cached."
)


print(
    "✅ One fixture date-range request."
)


print(
    "✅ No xG API request."
)


print(
    "✅ No fake 50% fallback."
)


print(
    "✅ Over requires BOTH BTTS >= 60%."
)


print(
    "✅ Under requires BOTH BTTS < 50%."
)


print(
    "⚠️ History uses 2024 proxy because "
    "your Free plan does not expose "
    "2025/2026 history."
)


print("=" * 72)
