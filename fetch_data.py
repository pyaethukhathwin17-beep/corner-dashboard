import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests


# ============================================================
# CONFIGURATION
# ============================================================

API_BASE = "https://v3.football.api-sports.io"

# Champions League ONLY
CHAMPIONS_LEAGUE_ID = 2

# API-SPORTS Free plan limitation discovered from testing:
# 2025 / 2026 season history is NOT available.
#
# 2024 season is available and contains 2024/25 competition data.
# We therefore use it ONLY as a clearly-labelled historical proxy.
HISTORY_SEASON = 2024

# Maximum upcoming matches to evaluate
MAX_MATCHES = 5

# Safety limits
MAX_API_CALLS_PER_RUN = 12
MIN_REMAINING_QUOTA = 15

# Delay between API calls
API_DELAY_SECONDS = 7

# Cache
CACHE_FILE = "team_history_cache.json"

# Output
OUTPUT_FILE = "matches_data.json"

# Myanmar Time
MMT_TZ = timezone(timedelta(hours=6, minutes=30))


# ============================================================
# API KEY
# ============================================================

raw_keys = os.environ.get("API_KEYS_POOL", "").strip()

if not raw_keys:
    raise RuntimeError(
        "\n"
        "❌ API_KEYS_POOL is not configured.\n\n"
        "GitHub Repository → Settings → Secrets and variables → Actions\n"
        "→ New repository secret\n\n"
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
    raise RuntimeError("❌ No valid API key found in API_KEYS_POOL.")

current_key_index = 0

print("=" * 70)
print("🔐 API CONFIGURATION")
print("=" * 70)
print(f"Total API Keys Loaded : {len(API_KEYS)}")
print("API keys are NOT printed for security.")
print("=" * 70)


# ============================================================
# API STATE
# ============================================================

api_calls_this_run = 0
remaining_quota = None


def get_active_key():
    return API_KEYS[current_key_index]


# ============================================================
# SAFE API REQUEST
# ============================================================

def api_request(endpoint, params=None, purpose=""):
    global api_calls_this_run
    global current_key_index
    global remaining_quota

    # --------------------------------------------------------
    # HARD LOCAL REQUEST LIMIT
    # --------------------------------------------------------

    if api_calls_this_run >= MAX_API_CALLS_PER_RUN:
        print("\n🛑 API SAFETY STOP")
        print(
            f"Maximum API calls per run reached: "
            f"{MAX_API_CALLS_PER_RUN}"
        )
        return None

    # --------------------------------------------------------
    # QUOTA SAFETY
    # --------------------------------------------------------

    if (
        remaining_quota is not None
        and remaining_quota <= MIN_REMAINING_QUOTA
    ):
        print("\n🛑 API SAFETY STOP")
        print(
            f"Remaining quota is only {remaining_quota}. "
            f"Safety threshold = {MIN_REMAINING_QUOTA}."
        )
        return None

    url = f"{API_BASE}/{endpoint}"

    headers = {
        "x-apisports-key": get_active_key()
    }

    print("\n" + "-" * 70)
    print("🌐 API REQUEST")
    print("-" * 70)

    if purpose:
        print(f"Purpose : {purpose}")

    print(f"Endpoint: {endpoint}")

    api_calls_this_run += 1

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
        )

        # ----------------------------------------------------
        # READ QUOTA HEADER
        # ----------------------------------------------------

        quota_header_names = [
            "x-ratelimit-requests-remaining",
            "X-RateLimit-Requests-Remaining",
        ]

        for header_name in quota_header_names:
            value = response.headers.get(header_name)

            if value is not None:
                try:
                    remaining_quota = int(value)
                except ValueError:
                    pass

                break

        print(f"HTTP Status: {response.status_code}")

        if remaining_quota is not None:
            print(f"Remaining Quota: {remaining_quota}")

        # ----------------------------------------------------
        # HTTP ERROR
        # ----------------------------------------------------

        if response.status_code != 200:
            print("❌ HTTP ERROR")

            if response.status_code in [401, 403]:
                print(
                    "⚠️ Authentication / permission error."
                )

            if response.status_code == 429:
                print(
                    "🛑 RATE LIMIT / TOO MANY REQUESTS."
                )

            return None

        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        try:
            data = response.json()
        except Exception:
            print("❌ Invalid JSON response.")
            return None

        errors = data.get("errors", {})
        results = data.get("results", 0)

        print(f"API Results: {results}")
        print(f"API Errors : {errors}")

        if errors:
            print("❌ API ERROR")
            return None

        print("✅ API DATA RECEIVED")

        return data

    except requests.RequestException as exc:
        print(f"❌ CONNECTION ERROR: {exc}")
        return None


# ============================================================
# CACHE
# ============================================================

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception as exc:
        print(f"⚠️ Cache read error: {exc}")

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

        print(f"💾 History cache saved: {CACHE_FILE}")

    except Exception as exc:
        print(f"⚠️ Cache save error: {exc}")


history_cache = load_cache()


# ============================================================
# TIME WINDOW
# ============================================================

now_mmt = datetime.now(MMT_TZ)

window_start = datetime(
    now_mmt.year,
    now_mmt.month,
    now_mmt.day,
    12,
    0,
    0,
    tzinfo=MMT_TZ,
)

window_end = window_start + timedelta(days=1)

date_today = window_start.strftime("%Y-%m-%d")
date_tomorrow = window_end.strftime("%Y-%m-%d")


# ============================================================
# UPCOMING CHAMPIONS LEAGUE FIXTURES
# ============================================================

print("\n" + "=" * 70)
print("🏆 CHAMPIONS LEAGUE TEST MODE")
print("=" * 70)

print(
    f"Window:\n"
    f"{window_start.strftime('%Y-%m-%d %I:%M %p')} MMT\n"
    f"to\n"
    f"{window_end.strftime('%Y-%m-%d %I:%M %p')} MMT"
)

print()
print("League Filter : UEFA Champions League ONLY")
print(f"Maximum Games : {MAX_MATCHES}")
print(f"API Delay     : {API_DELAY_SECONDS} seconds")
print(f"History Season: {HISTORY_SEASON} proxy")
print(f"Max API Calls : {MAX_API_CALLS_PER_RUN}")
print("=" * 70)


def fetch_daily_fixtures(date_string):

    data = api_request(
        "fixtures",
        params={
            "date": date_string,
            "timezone": "Asia/Yangon",
        },
        purpose=f"Upcoming fixtures for {date_string}",
    )

    if data is None:
        return []

    return data.get("response", [])


print("\n📅 Fetching today's fixtures...")

raw_today = fetch_daily_fixtures(date_today)

if raw_today:
    time.sleep(API_DELAY_SECONDS)


print("\n📅 Fetching tomorrow's fixtures...")

raw_tomorrow = fetch_daily_fixtures(date_tomorrow)


all_fixtures = raw_today + raw_tomorrow

print(
    f"\nRaw fixtures received: {len(all_fixtures)}"
)


# ============================================================
# SELECT UPCOMING CHAMPIONS LEAGUE MATCHES
# ============================================================

selected_fixtures = []
seen_ids = set()

for fixture in all_fixtures:

    fixture_data = fixture.get("fixture", {})
    league_data = fixture.get("league", {})
    teams_data = fixture.get("teams", {})

    fixture_id = fixture_data.get("id")

    if fixture_id in seen_ids:
        continue

    seen_ids.add(fixture_id)

    # Only Champions League
    if league_data.get("id") != CHAMPIONS_LEAGUE_ID:
        continue

    status = fixture_data.get("status", {}).get("short")

    if status not in ["NS", "TBD"]:
        continue

    fixture_date = fixture_data.get("date")

    if not fixture_date:
        continue

    try:
        fixture_dt = datetime.fromisoformat(fixture_date)
    except Exception:
        continue

    # Make sure date has timezone
    if fixture_dt.tzinfo is None:
        fixture_dt = fixture_dt.replace(tzinfo=timezone.utc)

    if not (
        window_start
        <= fixture_dt
        <= window_end
    ):
        continue

    home = teams_data.get("home", {})
    away = teams_data.get("away", {})

    if not home.get("id") or not away.get("id"):
        continue

    selected_fixtures.append(fixture)


selected_fixtures.sort(
    key=lambda x: x["fixture"]["date"]
)

selected_fixtures = selected_fixtures[:MAX_MATCHES]


print("\n" + "=" * 70)
print("🏆 CHAMPIONS LEAGUE FIXTURES FOUND")
print("=" * 70)

print(
    f"Total Champions League matches selected: "
    f"{len(selected_fixtures)}"
)

for index, fixture in enumerate(
    selected_fixtures,
    1
):

    home = fixture["teams"]["home"]["name"]
    away = fixture["teams"]["away"]["name"]
    date = fixture["fixture"]["date"]

    print(
        f"{index}. {home} vs {away} | {date}"
    )

print("=" * 70)


# ============================================================
# TEAM HISTORY
# ============================================================

def get_team_history(
    team_id,
    team_name,
    venue
):

    cache_key = f"{team_id}_{HISTORY_SEASON}"

    # --------------------------------------------------------
    # USE CACHE FIRST
    # --------------------------------------------------------

    if cache_key in history_cache:

        print("\n" + "=" * 70)
        print("📦 USING CACHED TEAM HISTORY")
        print("=" * 70)

        print(f"Team   : {team_name}")
        print(f"Team ID: {team_id}")
        print(f"Season : {HISTORY_SEASON}")

        fixtures = history_cache[cache_key]

    else:

        print("\n" + "=" * 70)
        print("📊 TEAM HISTORY REQUEST")
        print("=" * 70)

        print(f"Team   : {team_name}")
        print(f"Team ID: {team_id}")
        print(f"Season : {HISTORY_SEASON}")
        print(
            "Method : team + season "
            "(Free-plan compatible)"
        )

        data = api_request(
            "fixtures",
            params={
                "team": team_id,
                "season": HISTORY_SEASON,
            },
            purpose=(
                f"{team_name} historical fixtures "
                f"season {HISTORY_SEASON}"
            ),
        )

        if data is None:
            return {
                "status": "API_ERROR",
                "matches": [],
                "over_pct": None,
                "under_pct": None,
                "btts_pct": None,
                "gf_avg": None,
                "ga_avg": None,
            }

        fixtures = data.get("response", [])

        history_cache[cache_key] = fixtures

        save_cache(history_cache)

    # --------------------------------------------------------
    # FILTER FINISHED MATCHES
    # --------------------------------------------------------

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
            "PEN",
        ]:
            continue

        home = fixture.get("teams", {}).get(
            "home",
            {}
        )

        away = fixture.get("teams", {}).get(
            "away",
            {}
        )

        goals = fixture.get("goals", {})

        home_id = home.get("id")
        away_id = away.get("id")

        home_goals = goals.get("home")
        away_goals = goals.get("away")

        if (
            home_goals is None
            or away_goals is None
        ):
            continue

        # HOME / AWAY filter
        if venue == "HOME":

            if home_id != team_id:
                continue

        elif venue == "AWAY":

            if away_id != team_id:
                continue

        finished.append(
            {
                "date": fixture
                .get("fixture", {})
                .get("date", ""),

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

                "gh": int(home_goals),
                "ga": int(away_goals),
            }
        )

    # Newest first
    finished.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    selected = finished[:5]

    # --------------------------------------------------------
    # NOT ENOUGH DATA
    # --------------------------------------------------------

    if len(selected) < 5:

        print(
            f"⚠️ {team_name} "
            f"({venue}) → "
            f"Only {len(selected)}/5 matches"
        )

        if len(selected) == 0:

            return {
                "status": "INSUFFICIENT_L5_DATA",
                "matches": [],
                "over_pct": None,
                "under_pct": None,
                "btts_pct": None,
                "gf_avg": None,
                "ga_avg": None,
            }

    # --------------------------------------------------------
    # CALCULATE STATS
    # --------------------------------------------------------

    over_count = 0
    btts_count = 0
    gf_total = 0
    ga_total = 0

    scorelines = []

    for match in selected:

        total_goals = (
            match["gh"]
            + match["ga"]
        )

        if total_goals >= 3:
            over_count += 1

        if (
            match["gh"] > 0
            and match["ga"] > 0
        ):
            btts_count += 1

        if match["home_id"] == team_id:

            gf_total += match["gh"]
            ga_total += match["ga"]

        else:

            gf_total += match["ga"]
            ga_total += match["gh"]

        scorelines.append(
            {
                "date": match["date"][:10],
                "home": match["home"],
                "away": match["away"],
                "gh": match["gh"],
                "ga": match["ga"],
                "tot": total_goals,
            }
        )

    count = len(selected)

    return {
        "status": (
            "PROXY_2024_25"
            if count >= 5
            else "PARTIAL_PROXY_2024_25"
        ),

        "data_source": (
            "API-SPORTS 2024 season "
            "(historical proxy; NOT current 2026 form)"
        ),

        "sample_size": count,

        "over_pct": round(
            over_count / count * 100,
            1
        ),

        "under_pct": round(
            (count - over_count)
            / count
            * 100,
            1
        ),

        "btts_pct": round(
            btts_count / count * 100,
            1
        ),

        "gf_avg": round(
            gf_total / count,
            2
        ),

        "ga_avg": round(
            ga_total / count,
            2
        ),

        "scorelines": scorelines,
    }


# ============================================================
# MODEL
# ============================================================

def calculate_model(
    home_stats,
    away_stats
):

    if (
        home_stats["status"]
        not in [
            "PROXY_2024_25",
            "PARTIAL_PROXY_2024_25",
        ]
        or
        away_stats["status"]
        not in [
            "PROXY_2024_25",
            "PARTIAL_PROXY_2024_25",
        ]
    ):

        return {
            "signal": "DATA_UNAVAILABLE",
            "probability": None,
            "edge": None,
            "model_status": "INSUFFICIENT_DATA",
        }

    # Need at least 5 matches on both sides
    if (
        home_stats.get("sample_size", 0) < 5
        or
        away_stats.get("sample_size", 0) < 5
    ):

        return {
            "signal": "DATA_UNAVAILABLE",
            "probability": None,
            "edge": None,
            "model_status": "INSUFFICIENT_L5_DATA",
        }

    # --------------------------------------------------------
    # OVER 2.5 MODEL
    # --------------------------------------------------------

    avg_over = (
        home_stats["over_pct"]
        + away_stats["over_pct"]
    ) / 2

    avg_btts = (
        home_stats["btts_pct"]
        + away_stats["btts_pct"]
    ) / 2

    # Combined expected goals
    combined_gf = (
        home_stats["gf_avg"]
        + away_stats["gf_avg"]
    )

    combined_ga = (
        home_stats["ga_avg"]
        + away_stats["ga_avg"]
    )

    # Goal environment
    goal_environment = (
        combined_gf
        + combined_ga
    )

    # Cap to 100
    goal_score = min(
        100,
        goal_environment / 5.5 * 100
    )

    # --------------------------------------------------------
    # Weighted probability
    #
    # IMPORTANT:
    # This is a model score, NOT bookmaker implied probability.
    # --------------------------------------------------------

    probability = (
        avg_over * 0.45
        + avg_btts * 0.20
        + goal_score * 0.35
    )

    probability = round(
        max(0, min(100, probability)),
        1
    )

    # --------------------------------------------------------
    # EDGE
    #
    # Baseline = 60%
    # --------------------------------------------------------

    edge = round(
        probability - 60,
        1
    )

    # --------------------------------------------------------
    # SIGNAL
    # --------------------------------------------------------

    strong_over = (
        home_stats["over_pct"] >= 60
        and away_stats["over_pct"] >= 60
        and home_stats["gf_avg"] >= 1.5
        and away_stats["gf_avg"] >= 1.2
    )

    strong_under = (
        home_stats["under_pct"] >= 60
        and away_stats["under_pct"] >= 60
        and home_stats["gf_avg"] <= 1.5
        and away_stats["gf_avg"] <= 1.5
    )

    if strong_over and edge >= 5:

        signal = "OVER_2_5"

    elif strong_under and edge <= -5:

        signal = "UNDER_2_5"

    else:

        signal = "NEUTRAL"

    return {
        "signal": signal,
        "probability": probability,
        "edge": edge,
        "model_status": "PROXY_MODEL_2024_25",
    }


# ============================================================
# EVALUATION
# ============================================================

evaluated_matches = []

unique_teams = set()

for fixture in selected_fixtures:

    unique_teams.add(
        fixture["teams"]["home"]["id"]
    )

    unique_teams.add(
        fixture["teams"]["away"]["id"]
    )


print("\n" + "=" * 70)
print("📊 TEAM HISTORY PLAN")
print("=" * 70)

print(
    f"Unique teams requiring history: "
    f"{len(unique_teams)}"
)

print(
    f"Maximum API calls this run: "
    f"{MAX_API_CALLS_PER_RUN}"
)

print("=" * 70)


# ------------------------------------------------------------
# We cache each team history.
# This prevents duplicate API requests if a team appears again.
# ------------------------------------------------------------

team_home_history = {}
team_away_history = {}


for index, fixture in enumerate(
    selected_fixtures,
    1
):

    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]

    home_name = fixture["teams"]["home"]["name"]
    away_name = fixture["teams"]["away"]["name"]

    print("\n" + "#" * 70)
    print(
        f"🎯 EVALUATING MATCH "
        f"{index}/{len(selected_fixtures)}"
    )
    print("#" * 70)

    print(
        f"\n⚽ {home_name} vs {away_name}"
    )

    # --------------------------------------------------------
    # HOME HISTORY
    # --------------------------------------------------------

    home_cache_key = (
        f"{home_id}_HOME_{HISTORY_SEASON}"
    )

    if home_cache_key not in team_home_history:

        team_home_history[home_cache_key] = (
            get_team_history(
                home_id,
                home_name,
                "HOME"
            )
        )

        if (
            team_home_history[home_cache_key]
            .get("status")
            == "API_ERROR"
        ):
            pass
        else:
            time.sleep(API_DELAY_SECONDS)

    home_stats = team_home_history[
        home_cache_key
    ]

    # --------------------------------------------------------
    # AWAY HISTORY
    # --------------------------------------------------------

    away_cache_key = (
        f"{away_id}_AWAY_{HISTORY_SEASON}"
    )

    if away_cache_key not in team_away_history:

        team_away_history[away_cache_key] = (
            get_team_history(
                away_id,
                away_name,
                "AWAY"
            )
        )

        if (
            team_away_history[away_cache_key]
            .get("status")
            == "API_ERROR"
        ):
            pass
        else:
            time.sleep(API_DELAY_SECONDS)

    away_stats = team_away_history[
        away_cache_key
    ]

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model = calculate_model(
        home_stats,
        away_stats
    )

    print("\n" + "-" * 70)
    print("🎯 MODEL RESULT")
    print("-" * 70)

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

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    fixture_date = fixture["fixture"]["date"]

    try:
        local_dt = datetime.fromisoformat(
            fixture_date
        ).astimezone(MMT_TZ)

        display_date = local_dt.strftime(
            "%Y-%m-%d"
        )

        display_time = local_dt.strftime(
            "%H:%M"
        )

    except Exception:

        display_date = fixture_date[:10]
        display_time = fixture_date[11:16]

    evaluated_matches.append(
        {
            "fixture_id": fixture["fixture"]["id"],

            "league": fixture["league"]["name"],

            "country": fixture["league"].get(
                "country",
                ""
            ),

            "home": home_name,

            "away": away_name,

            "date": display_date,

            "time": display_time,

            "status": fixture["fixture"]["status"]["short"],

            "signal": model["signal"],

            "prob": model["probability"],

            "edge": model["edge"],

            "model_status": model["model_status"],

            "data_warning": (
                "Historical proxy from "
                "2024 season. "
                "NOT current 2026 form."
            ),

            "h_stats": home_stats,

            "a_stats": away_stats,
        }
    )


# ============================================================
# SORT
# ============================================================

def signal_priority(signal):

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
        x["time"],
    )
)


# ============================================================
# SAVE OUTPUT
# ============================================================

output = {
    "updated_at": now_mmt.strftime(
        "%Y-%m-%d %H:%M MMT"
    ),

    "window_range": (
        f"{window_start.strftime('%Y-%m-%d %I:%M %p')}"
        f" - "
        f"{window_end.strftime('%Y-%m-%d %I:%M %p')}"
        f" MMT"
    ),

    "mode": "CHAMPIONS_LEAGUE_TEST",

    "league_filter": (
        "UEFA Champions League ONLY"
    ),

    "history_season": HISTORY_SEASON,

    "history_data_type": (
        "2024 season historical proxy"
    ),

    "current_form_available": False,

    "warning": (
        "Free API plan does not provide "
        "2025/2026 team history. "
        "Probability and Edge use "
        "2024 historical proxy data and "
        "must NOT be interpreted as "
        "current 2026 form."
    ),

    "api_calls_this_run": api_calls_this_run,

    "remaining_quota": remaining_quota,

    "total_matches": len(
        evaluated_matches
    ),

    "matches": evaluated_matches,
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
# FINAL REPORT
# ============================================================

print("\n" + "=" * 70)
print("✅ FETCH COMPLETE")
print("=" * 70)

print(
    f"Champions League matches: "
    f"{len(evaluated_matches)}"
)

print(
    f"API calls this run: "
    f"{api_calls_this_run}"
)

if remaining_quota is not None:

    print(
        f"Remaining API quota: "
        f"{remaining_quota}"
    )

print(
    f"Saved to: {OUTPUT_FILE}"
)

print("\n" + "-" * 70)

for match in evaluated_matches:

    print(
        f"\n⚽ {match['home']} "
        f"vs {match['away']}"
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

print("\n" + "=" * 70)
print("🛡️ API SAFETY")
print("=" * 70)

print(
    "No fake 50% fallback is used."
)

print(
    "API keys are read from GitHub Secrets."
)

print(
    "Historical team data is cached."
)

print(
    "API request limit is enforced."
)

print(
    "Current 2026 form is NOT falsely claimed."
)

print("=" * 70)
