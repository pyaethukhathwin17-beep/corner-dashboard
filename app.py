import os
import time
from datetime import datetime, timedelta, timezone

import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Football Prematch Scanner",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CONFIG
# ============================================================

API_BASE = "https://v3.football.api-sports.io"

# ------------------------------------------------------------
# Myanmar Time
# ------------------------------------------------------------

MMT_TZ = timezone(timedelta(hours=6, minutes=30))

# ------------------------------------------------------------
# Search window
#
# TODAY 12:00 PM MMT
#       ->
# TOMORROW 12:00 PM MMT
# ------------------------------------------------------------

SEARCH_START_HOUR = 12

# ------------------------------------------------------------
# Historical proxy
#
# Your Free API setup previously tested successfully with 2024.
# This is intentionally kept as the historical proxy.
# ------------------------------------------------------------

HISTORY_SEASON = 2024

# ------------------------------------------------------------
# Maximum matches to analyse
# ------------------------------------------------------------

MAX_MATCHES_TO_ANALYZE = 5

# ------------------------------------------------------------
# API safety
#
# Stop this app after 80 requests in ONE RUN.
# ------------------------------------------------------------

MAX_API_CALLS_PER_RUN = 80

# If API itself reports very low remaining quota,
# stop before making another request.
MIN_REMAINING_QUOTA = 10

# API-Football free plan is currently 10 requests/minute.
# We use a small delay between calls.
API_DELAY_SECONDS = 1.0

# ------------------------------------------------------------
# Request timeout
# ------------------------------------------------------------

REQUEST_TIMEOUT = 30


# ============================================================
# API KEY
# ============================================================

def load_api_keys():

    # --------------------------------------------------------
    # Streamlit Cloud secrets
    # --------------------------------------------------------

    try:
        secret_value = st.secrets.get("API_KEYS_POOL", "")
    except Exception:
        secret_value = ""

    # --------------------------------------------------------
    # Environment variable
    # --------------------------------------------------------

    env_value = os.environ.get(
        "API_KEYS_POOL",
        ""
    )

    raw_keys = (
        secret_value
        or env_value
    )

    if not raw_keys:
        st.error(
            "❌ API_KEYS_POOL မတွေ့ပါ။ "
            "Streamlit Secrets သို့မဟုတ် Environment Variable "
            "ထဲတွင် API_KEYS_POOL ထည့်ပေးပါ။"
        )
        st.stop()

    keys = [
        key.strip()
        for key in str(raw_keys).split(",")
        if key.strip()
    ]

    if not keys:
        st.error(
            "❌ API key မတွေ့ပါ။"
        )
        st.stop()

    return keys


API_KEYS = load_api_keys()


# ============================================================
# SESSION STATE
# ============================================================

if "api_calls" not in st.session_state:
    st.session_state.api_calls = 0

if "remaining_quota" not in st.session_state:
    st.session_state.remaining_quota = None

if "current_key_index" not in st.session_state:
    st.session_state.current_key_index = 0

if "league_catalog" not in st.session_state:
    st.session_state.league_catalog = None

if "last_scan_results" not in st.session_state:
    st.session_state.last_scan_results = []

if "scan_message" not in st.session_state:
    st.session_state.scan_message = ""


# ============================================================
# API HELPERS
# ============================================================

def get_current_api_key():

    index = st.session_state.current_key_index

    if index >= len(API_KEYS):
        index = 0
        st.session_state.current_key_index = 0

    return API_KEYS[index]


def rotate_api_key():

    if len(API_KEYS) <= 1:
        return

    st.session_state.current_key_index = (
        st.session_state.current_key_index + 1
    ) % len(API_KEYS)


def api_request(
    endpoint,
    params=None,
    purpose=""
):

    # --------------------------------------------------------
    # LOCAL HARD LIMIT
    # --------------------------------------------------------

    if (
        st.session_state.api_calls
        >= MAX_API_CALLS_PER_RUN
    ):

        st.error(
            "🛑 API SAFETY STOP\n\n"
            f"ဒီ run အတွင်း API request "
            f"{MAX_API_CALLS_PER_RUN} ခု ပြည့်သွားပါပြီ။"
        )

        return None


    # --------------------------------------------------------
    # QUOTA SAFETY
    # --------------------------------------------------------

    remaining = st.session_state.remaining_quota

    if (
        remaining is not None
        and remaining <= MIN_REMAINING_QUOTA
    ):

        st.warning(
            "🛑 API quota နည်းနေသောကြောင့် "
            "request ထပ်မခေါ်တော့ပါ။"
        )

        return None


    url = f"{API_BASE}/{endpoint}"

    headers = {
        "x-apisports-key": get_current_api_key(),
        "Accept": "application/json",
    }


    # --------------------------------------------------------
    # Small delay
    # --------------------------------------------------------

    if st.session_state.api_calls > 0:
        time.sleep(API_DELAY_SECONDS)


    st.session_state.api_calls += 1


    try:

        response = requests.get(
            url,
            headers=headers,
            params=params or {},
            timeout=REQUEST_TIMEOUT,
        )

    except requests.RequestException as exc:

        st.warning(
            f"⚠️ API connection error: {exc}"
        )

        return None


    # --------------------------------------------------------
    # QUOTA HEADERS
    # --------------------------------------------------------

    remaining_headers = [
        "x-ratelimit-requests-remaining",
        "X-RateLimit-Requests-Remaining",
    ]

    for header_name in remaining_headers:

        value = response.headers.get(
            header_name
        )

        if value is not None:

            try:
                st.session_state.remaining_quota = int(
                    value
                )

            except ValueError:
                pass

            break


    # --------------------------------------------------------
    # 401 / 403
    # --------------------------------------------------------

    if response.status_code in [401, 403]:

        if len(API_KEYS) > 1:

            rotate_api_key()

            st.warning(
                "⚠️ API key permission error ဖြစ်နေသဖြင့် "
                "နောက် API key သို့ ပြောင်းပါမည်။"
            )

        else:

            st.error(
                "❌ API key authentication / permission error."
            )

        return None


    # --------------------------------------------------------
    # 429
    # --------------------------------------------------------

    if response.status_code == 429:

        st.warning(
            "🛑 API rate limit (429) ရရှိပါသည်။ "
            "Request များကို ရပ်ထားပါသည်။"
        )

        return None


    # --------------------------------------------------------
    # Other HTTP errors
    # --------------------------------------------------------

    if response.status_code != 200:

        st.warning(
            f"❌ API HTTP error: "
            f"{response.status_code}"
        )

        return None


    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    try:

        data = response.json()

    except Exception:

        st.warning(
            "❌ API response သည် JSON မဟုတ်ပါ။"
        )

        return None


    # --------------------------------------------------------
    # API errors
    # --------------------------------------------------------

    errors = data.get(
        "errors",
        {}
    )

    if errors:

        st.warning(
            f"❌ API error: {errors}"
        )

        return None


    return data


# ============================================================
# TIME WINDOW
# ============================================================

def get_search_window():

    now_mmt = datetime.now(
        MMT_TZ
    )

    start = datetime(
        now_mmt.year,
        now_mmt.month,
        now_mmt.day,
        SEARCH_START_HOUR,
        0,
        0,
        tzinfo=MMT_TZ,
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # If current time is already after today's 12 PM,
    # search starts TODAY 12 PM.
    #
    # If current time is before today's 12 PM,
    # search still starts TODAY 12 PM.
    #
    # This is intentionally fixed to:
    # TODAY 12:00 PM -> TOMORROW 12:00 PM
    # --------------------------------------------------------

    end = start + timedelta(
        days=1
    )

    return start, end


# ============================================================
# LEAGUE CATALOG
# ============================================================

def fetch_league_catalog():

    data = api_request(
        "leagues",
        params={
            "season": 2026,
        },
        purpose="Load 2026 league catalogue",
    )

    if data is None:
        return []

    response = data.get(
        "response",
        []
    )

    catalog = []

    seen = set()

    for item in response:

        league = item.get(
            "league",
            {}
        )

        country = item.get(
            "country",
            {}
        )

        league_id = league.get(
            "id"
        )

        league_name = league.get(
            "name"
        )

        league_type = league.get(
            "type",
            ""
        )

        country_name = country.get(
            "name",
            "Unknown"
        )

        if not league_id:
            continue

        if not league_name:
            continue

        unique_key = (
            league_id,
            league_name,
            country_name,
        )

        if unique_key in seen:
            continue

        seen.add(unique_key)

        catalog.append(
            {
                "id": int(league_id),
                "name": str(league_name),
                "country": str(country_name),
                "type": str(league_type),
            }
        )

    catalog.sort(
        key=lambda x: (
            x["country"].lower(),
            x["name"].lower(),
        )
    )

    return catalog


def ensure_league_catalog():

    if (
        st.session_state.league_catalog
        is not None
    ):
        return st.session_state.league_catalog

    with st.spinner(
        "🏆 League list ကို API မှ ရယူနေပါသည်..."
    ):

        catalog = fetch_league_catalog()

    if not catalog:

        return []

    st.session_state.league_catalog = catalog

    return catalog


# ============================================================
# LEAGUE DISPLAY HELPERS
# ============================================================

def league_label(item):

    return (
        f"{item['name']} "
        f"— {item['country']} "
        f"[{item['type']}]"
    )


def country_options(catalog):

    countries = sorted(
        {
            item["country"]
            for item in catalog
            if item.get("country")
        },
        key=lambda x: x.lower(),
    )

    return countries


# ============================================================
# FIXTURE FETCH
# ============================================================

def fetch_fixtures_for_date(
    date_string
):

    return api_request(
        "fixtures",
        params={
            "date": date_string,
            "timezone": "Asia/Yangon",
        },
        purpose=(
            f"Fixtures for {date_string} "
            f"MMT"
        ),
    )


def fixture_is_in_window(
    fixture,
    start,
    end
):

    fixture_data = fixture.get(
        "fixture",
        {}
    )

    status = fixture_data.get(
        "status",
        {}
    ).get(
        "short"
    )

    if status not in [
        "NS",
        "TBD",
    ]:
        return False


    fixture_date = fixture_data.get(
        "date"
    )

    if not fixture_date:
        return False


    try:

        dt = datetime.fromisoformat(
            fixture_date
        )

    except Exception:

        return False


    if dt.tzinfo is None:

        dt = dt.replace(
            tzinfo=timezone.utc
        )


    dt_mmt = dt.astimezone(
        MMT_TZ
    )


    return (
        start
        <= dt_mmt
        <= end
    )


def collect_selected_fixtures(
    selected_league_ids,
    start,
    end
):

    date_1 = start.strftime(
        "%Y-%m-%d"
    )

    date_2 = end.strftime(
        "%Y-%m-%d"
    )


    raw_fixtures = []


    # --------------------------------------------------------
    # TODAY
    # --------------------------------------------------------

    data_today = fetch_fixtures_for_date(
        date_1
    )

    if data_today:

        raw_fixtures.extend(
            data_today.get(
                "response",
                []
            )
        )


    # --------------------------------------------------------
    # TOMORROW
    # --------------------------------------------------------

    if date_2 != date_1:

        data_tomorrow = (
            fetch_fixtures_for_date(
                date_2
            )
        )

        if data_tomorrow:

            raw_fixtures.extend(
                data_tomorrow.get(
                    "response",
                    []
                )
            )


    # --------------------------------------------------------
    # LOCAL FILTER
    #
    # Important:
    # We DO NOT call the API separately for every league.
    #
    # We fetch date fixtures and filter league IDs locally.
    # This saves a lot of API calls.
    # --------------------------------------------------------

    selected = []

    seen_ids = set()

    for fixture in raw_fixtures:

        fixture_data = fixture.get(
            "fixture",
            {}
        )

        league_data = fixture.get(
            "league",
            {}
        )

        fixture_id = fixture_data.get(
            "id"
        )

        league_id = league_data.get(
            "id"
        )

        if not fixture_id:
            continue

        if fixture_id in seen_ids:
            continue

        seen_ids.add(
            fixture_id
        )


        if league_id not in selected_league_ids:
            continue


        if not fixture_is_in_window(
            fixture,
            start,
            end
        ):
            continue


        home = fixture.get(
            "teams",
            {}
        ).get(
            "home",
            {}
        )

        away = fixture.get(
            "teams",
            {}
        ).get(
            "away",
            {}
        )


        if not home.get("id"):
            continue

        if not away.get("id"):
            continue


        selected.append(
            fixture
        )


    selected.sort(
        key=lambda x: x.get(
            "fixture",
            {}
        ).get(
            "date",
            ""
        )
    )


    return selected


# ============================================================
# TEAM HISTORY
# ============================================================

def get_team_history(
    team_id,
    team_name,
    venue
):

    cache_key = (
        f"{team_id}_"
        f"{venue}_"
        f"{HISTORY_SEASON}"
    )


    # --------------------------------------------------------
    # SESSION CACHE
    # --------------------------------------------------------

    cache = st.session_state.get(
        "history_cache",
        {}
    )

    if cache_key in cache:

        return cache[
            cache_key
        ]


    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    data = api_request(
        "fixtures",
        params={
            "team": team_id,
            "season": HISTORY_SEASON,
        },
        purpose=(
            f"{team_name} "
            f"{venue} L5 history"
        ),
    )


    if data is None:

        return {
            "status": "API_ERROR",
            "sample_size": 0,
            "over_pct": None,
            "under_pct": None,
            "btts_pct": None,
            "gf_avg": None,
            "ga_avg": None,
            "scorelines": [],
        }


    fixtures = data.get(
        "response",
        []
    )


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


        teams = fixture.get(
            "teams",
            {}
        )

        home = teams.get(
            "home",
            {}
        )

        away = teams.get(
            "away",
            {}
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


        if home_goals is None:
            continue

        if away_goals is None:
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
                "date": fixture
                .get(
                    "fixture",
                    {}
                )
                .get(
                    "date",
                    ""
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


    finished.sort(
        key=lambda x: x["date"],
        reverse=True
    )


    selected = finished[:5]


    if len(selected) < 5:

        result = {
            "status": (
                "INSUFFICIENT_L5_DATA"
            ),
            "sample_size": len(
                selected
            ),
            "over_pct": None,
            "under_pct": None,
            "btts_pct": None,
            "gf_avg": None,
            "ga_avg": None,
            "scorelines": [],
        }

        cache[
            cache_key
        ] = result

        st.session_state.history_cache = cache

        return result


    # --------------------------------------------------------
    # CALCULATE
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


        if (
            match["home_id"]
            == team_id
        ):

            gf_total += match[
                "gh"
            ]

            ga_total += match[
                "ga"
            ]

        else:

            gf_total += match[
                "ga"
            ]

            ga_total += match[
                "gh"
            ]


        scorelines.append(
            {
                "date": match[
                    "date"
                ][:10],

                "home": match[
                    "home"
                ],

                "away": match[
                    "away"
                ],

                "gh": match[
                    "gh"
                ],

                "ga": match[
                    "ga"
                ],

                "tot": total_goals,
            }
        )


    count = len(
        selected
    )


    result = {

        "status": "PROXY_2024_25",

        "data_source": (
            "API-SPORTS 2024 "
            "historical proxy"
        ),

        "sample_size": count,

        "over_pct": round(
            over_count
            / count
            * 100,
            1
        ),

        "under_pct": round(
            (
                count
                - over_count
            )
            / count
            * 100,
            1
        ),

        "btts_pct": round(
            btts_count
            / count
            * 100,
            1
        ),

        "gf_avg": round(
            gf_total
            / count,
            2
        ),

        "ga_avg": round(
            ga_total
            / count,
            2
        ),

        "scorelines": scorelines,
    }


    cache[
        cache_key
    ] = result

    st.session_state.history_cache = cache


    return result


# ============================================================
# MODEL
# ============================================================

def calculate_model(
    home_stats,
    away_stats
):

    required_status = [
        "PROXY_2024_25",
    ]


    if (
        home_stats.get(
            "status"
        ) not in required_status
        or
        away_stats.get(
            "status"
        ) not in required_status
    ):

        return {
            "signal": "DATA_UNAVAILABLE",
            "probability": None,
            "edge": None,
            "over_checks": {},
            "under_checks": {},
            "model_status": (
                "INSUFFICIENT_DATA"
            ),
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
            "signal": "DATA_UNAVAILABLE",
            "probability": None,
            "edge": None,
            "over_checks": {},
            "under_checks": {},
            "model_status": (
                "INSUFFICIENT_L5_DATA"
            ),
        }


    # ========================================================
    # OVER 2.5 CONDITIONS
    #
    # EXACT LOGIC REQUESTED
    #
    # Home L5 O2.5 >= 60%
    # Away L5 O2.5 >= 60%
    #
    # Home GF > 1.5
    # Home GA > 1.0
    #
    # Away GF > 1.0
    # Away GA > 1.0
    #
    # Home BTTS >= 60%
    # Away BTTS >= 60%
    #
    # Model edge > 5%
    # ========================================================

    over_checks = {

        "home_o25":
            home_stats[
                "over_pct"
            ] >= 60,

        "away_o25":
            away_stats[
                "over_pct"
            ] >= 60,

        "home_gf":
            home_stats[
                "gf_avg"
            ] > 1.5,

        "home_ga":
            home_stats[
                "ga_avg"
            ] > 1.0,

        "away_gf":
            away_stats[
                "gf_avg"
            ] > 1.0,

        "away_ga":
            away_stats[
                "ga_avg"
            ] > 1.0,

        "home_btts":
            home_stats[
                "btts_pct"
            ] >= 60,

        "away_btts":
            away_stats[
                "btts_pct"
            ] >= 60,
    }


    # ========================================================
    # UNDER 2.5 CONDITIONS
    #
    # Home L5 U2.5 >= 60%
    # Away L5 U2.5 >= 60%
    #
    # Home GF < 1.3
    # Home GA < 1.0
    #
    # Away GF < 1.1
    # Away GA < 1.2
    #
    # Home BTTS < 50%
    # Away BTTS < 50%
    #
    # Model edge > 5%
    # ========================================================

    under_checks = {

        "home_u25":
            home_stats[
                "under_pct"
            ] >= 60,

        "away_u25":
            away_stats[
                "under_pct"
            ] >= 60,

        "home_gf":
            home_stats[
                "gf_avg"
            ] < 1.3,

        "home_ga":
            home_stats[
                "ga_avg"
            ] < 1.0,

        "away_gf":
            away_stats[
                "gf_avg"
            ] < 1.1,

        "away_ga":
            away_stats[
                "ga_avg"
            ] < 1.2,

        "home_btts":
            home_stats[
                "btts_pct"
            ] < 50,

        "away_btts":
            away_stats[
                "btts_pct"
            ] < 50,
    }


    # ========================================================
    # MODEL PROBABILITY
    #
    # NO xG
    #
    # Only:
    # O/U %
    # BTTS %
    # GF / GA
    # ========================================================

    avg_over = (
        home_stats[
            "over_pct"
        ]
        +
        away_stats[
            "over_pct"
        ]
    ) / 2


    avg_under = (
        home_stats[
            "under_pct"
        ]
        +
        away_stats[
            "under_pct"
        ]
    ) / 2


    avg_btts = (
        home_stats[
            "btts_pct"
        ]
        +
        away_stats[
            "btts_pct"
        ]
    ) / 2


    goal_environment = (
        home_stats[
            "gf_avg"
        ]
        +
        home_stats[
            "ga_avg"
        ]
        +
        away_stats[
            "gf_avg"
        ]
        +
        away_stats[
            "ga_avg"
        ]
    )


    # --------------------------------------------------------
    # Goal score
    # 5.5 is the maximum environment reference.
    # --------------------------------------------------------

    goal_score = min(
        100,
        (
            goal_environment
            / 5.5
        )
        * 100
    )


    # --------------------------------------------------------
    # OVER probability
    # --------------------------------------------------------

    over_probability = (
        avg_over * 0.50
        +
        avg_btts * 0.20
        +
        goal_score * 0.30
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


    # --------------------------------------------------------
    # UNDER probability
    # --------------------------------------------------------

    under_probability = (
        avg_under * 0.50
        +
        (100 - avg_btts)
        * 0.20
        +
        (100 - goal_score)
        * 0.30
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
    # EDGE
    #
    # Baseline = 60%
    # ========================================================

    over_edge = round(
        over_probability - 60,
        1
    )

    under_edge = round(
        under_probability - 60,
        1
    )


    # ========================================================
    # FINAL QUALIFICATION
    #
    # IMPORTANT:
    # BTTS condition is now a HARD CONDITION.
    #
    # This prevents:
    # Away BTTS = 40%
    # from still producing OVER_2_5.
    # ========================================================

    over_all_conditions = (
        all(
            over_checks.values()
        )
        and
        over_edge > 5
    )


    under_all_conditions = (
        all(
            under_checks.values()
        )
        and
        under_edge > 5
    )


    if over_all_conditions:

        signal = "OVER_2_5"
        probability = over_probability
        edge = over_edge


    elif under_all_conditions:

        signal = "UNDER_2_5"
        probability = under_probability
        edge = under_edge


    else:

        signal = "NEUTRAL"
        probability = max(
            over_probability,
            under_probability
        )

        if (
            probability
            == over_probability
        ):

            edge = over_edge

        else:

            edge = under_edge


    return {

        "signal": signal,

        "probability": probability,

        "edge": edge,

        "over_probability":
            over_probability,

        "under_probability":
            under_probability,

        "over_edge":
            over_edge,

        "under_edge":
            under_edge,

        "over_checks":
            over_checks,

        "under_checks":
            under_checks,

        "model_status":
            "RULE_MODEL_NO_XG",
    }


# ============================================================
# FORMAT HELPERS
# ============================================================

def safe_pct(value):

    if value is None:
        return "—"

    return f"{value:.1f}%"


def safe_num(value):

    if value is None:
        return "—"

    return f"{value:.2f}"


def condition_icon(value):

    return "✅" if value else "❌"


def format_fixture_time(
    fixture
):

    date_string = (
        fixture
        .get("fixture", {})
        .get("date")
    )

    if not date_string:
        return "—", "—"


    try:

        dt = datetime.fromisoformat(
            date_string
        )

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        dt = dt.astimezone(
            MMT_TZ
        )

        return (
            dt.strftime(
                "%Y-%m-%d"
            ),
            dt.strftime(
                "%H:%M"
            ),
        )

    except Exception:

        return (
            date_string[:10],
            date_string[11:16],
        )


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #8f98a8;
        margin-bottom: 1.2rem;
    }

    .info-card {
        padding: 18px;
        border-radius: 14px;
        background: rgba(40, 50, 65, 0.55);
        border: 1px solid rgba(150, 160, 175, 0.22);
        margin-bottom: 12px;
    }

    .match-card {
        padding: 20px;
        border-radius: 16px;
        background: rgba(30, 36, 47, 0.72);
        border: 1px solid rgba(150, 160, 175, 0.25);
        margin-bottom: 16px;
    }

    .signal-over {
        padding: 8px 14px;
        border-radius: 10px;
        font-weight: 800;
        display: inline-block;
    }

    .signal-under {
        padding: 8px 14px;
        border-radius: 10px;
        font-weight: 800;
        display: inline-block;
    }

    .signal-neutral {
        padding: 8px 14px;
        border-radius: 10px;
        font-weight: 800;
        display: inline-block;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">⚽ Football Prematch Scanner</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Over 2.5 / Under 2.5 • L5 • BTTS • GF/GA • Model Edge'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SEARCH WINDOW DISPLAY
# ============================================================

search_start, search_end = (
    get_search_window()
)

col1, col2, col3 = st.columns(
    3
)

with col1:

    st.markdown(
        '<div class="info-card">'
        '<b>🕐 SEARCH WINDOW</b><br><br>'
        f'{search_start.strftime("%Y-%m-%d %I:%M %p")} '
        'MMT<br>'
        '↓<br>'
        f'{search_end.strftime("%Y-%m-%d %I:%M %p")} '
        'MMT'
        '</div>',
        unsafe_allow_html=True,
    )


with col2:

    st.markdown(
        '<div class="info-card">'
        '<b>⚙️ MODE</b><br><br>'
        'MULTI_LEAGUE_PREMATCH'
        '</div>',
        unsafe_allow_html=True,
    )


with col3:

    remaining = (
        st.session_state.remaining_quota
    )

    remaining_text = (
        str(remaining)
        if remaining is not None
        else "Not reported"
    )

    st.markdown(
        '<div class="info-card">'
        '<b>🛡️ API SAFETY</b><br><br>'
        f'Run calls: '
        f'{st.session_state.api_calls}/'
        f'{MAX_API_CALLS_PER_RUN}'
        '<br>'
        f'Remaining: {remaining_text}'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# LEAGUE FILTER
# ============================================================

st.markdown(
    "## 🏆 League Filter"
)


# ------------------------------------------------------------
# Load catalogue
# ------------------------------------------------------------

catalog = ensure_league_catalog()


# ------------------------------------------------------------
# Refresh button
# ------------------------------------------------------------

refresh_col1, refresh_col2 = st.columns(
    [1, 4]
)

with refresh_col1:

    if st.button(
        "🔄 Refresh Leagues",
        use_container_width=True,
    ):

        st.session_state.league_catalog = None

        st.rerun()


if not catalog:

    st.warning(
        "⚠️ League catalogue မရရှိသေးပါ။ "
        "API key / quota ကို စစ်ပါ။"
    )

    st.stop()


# ============================================================
# COUNTRY SELECTOR
# ============================================================

countries = country_options(
    catalog
)

country_choices = [
    "🌍 All Countries"
] + countries


selected_country = st.selectbox(
    "Country",
    country_choices,
    index=0,
    key="country_selector",
    filter_mode="contains",
)


# ============================================================
# FILTER LEAGUES BY COUNTRY
# ============================================================

if selected_country == "🌍 All Countries":

    filtered_leagues = catalog

else:

    filtered_leagues = [
        item
        for item in catalog
        if item["country"]
        == selected_country
    ]


# ============================================================
# COMPETITION MULTISELECT
# ============================================================

league_options = [
    league_label(item)
    for item in filtered_leagues
]


label_to_item = {
    league_label(item): item
    for item in filtered_leagues
}


selected_labels = st.multiselect(
    "Competition",
    league_options,
    default=[],
    placeholder=(
        "Competition ရွေးပါ "
        "(Search လုပ်လို့ရပါတယ်)"
    ),
    filter_mode="contains",
    key="competition_selector",
)


selected_leagues = [
    label_to_item[label]
    for label in selected_labels
    if label in label_to_item
]


# ============================================================
# SELECTED LEAGUE SUMMARY
# ============================================================

st.info(
    f"🏆 Selected leagues: "
    f"**{len(selected_leagues)}**"
)


if selected_leagues:

    with st.expander(
        "▼ View selected leagues",
        expanded=False,
    ):

        for league in selected_leagues:

            st.write(
                f"• **{league['name']}** "
                f"— {league['country']} "
                f"• ID: {league['id']}"
            )


# ============================================================
# QUICK PRESETS
# ============================================================

st.markdown(
    "### ⚡ Quick League Presets"
)

preset_col1, preset_col2, preset_col3 = (
    st.columns(3)
)


def find_leagues(
    names,
    country=None
):

    results = []

    for item in catalog:

        if country:

            if item[
                "country"
            ].lower() != country.lower():

                continue


        if item[
            "name"
        ].lower() in [
            name.lower()
            for name in names
        ]:

            results.append(
                item
            )

    return results


with preset_col1:

    if st.button(
        "🇬🇧 England Top 2",
        use_container_width=True,
    ):

        # Note:
        # Widget state cannot safely be mutated
        # after the widget is instantiated.
        # So show the suggested IDs instead.
        england = [
            item
            for item in catalog
            if item[
                "country"
            ].lower()
            == "england"
            and item[
                "name"
            ].lower()
            in [
                "premier league",
                "championship",
            ]
        ]

        if england:

            st.session_state[
                "preset_message"
            ] = england

            st.rerun()


with preset_col2:

    if st.button(
        "🇪🇸 Spain Top 2",
        use_container_width=True,
    ):

        spain = [
            item
            for item in catalog
            if item[
                "country"
            ].lower()
            == "spain"
            and item[
                "name"
            ].lower()
            in [
                "la liga",
                "la liga 2",
            ]
        ]

        if spain:

            st.session_state[
                "preset_message"
            ] = spain

            st.rerun()


with preset_col3:

    if st.button(
        "🇩🇪 Germany Top 2",
        use_container_width=True,
    ):

        germany = [
            item
            for item in catalog
            if item[
                "country"
            ].lower()
            == "germany"
            and item[
                "name"
            ].lower()
            in [
                "bundesliga",
                "2. bundesliga",
            ]
        ]

        if germany:

            st.session_state[
                "preset_message"
            ] = germany

            st.rerun()


# ============================================================
# PRESET DISPLAY
# ============================================================

if (
    "preset_message"
    in st.session_state
    and
    st.session_state[
        "preset_message"
    ]
):

    preset_items = st.session_state[
        "preset_message"
    ]

    st.success(
        "Preset တွေ့ပါပြီ။ "
        "Competition dropdown ထဲမှာ "
        "အဆိုပါ leagues ကို ရွေးနိုင်ပါတယ်။"
    )

    for item in preset_items:

        st.write(
            f"• {item['name']} "
            f"— {item['country']} "
            f"(ID {item['id']})"
        )

    if st.button(
        "✖ Clear Preset"
    ):

        st.session_state[
            "preset_message"
        ] = []

        st.rerun()


# ============================================================
# SEARCH BUTTON
# ============================================================

st.markdown(
    "---"
)


scan_button = st.button(
    "🔍 SEARCH MATCHES",
    type="primary",
    use_container_width=True,
)


# ============================================================
# SCAN
# ============================================================

if scan_button:

    if not selected_leagues:

        st.warning(
            "⚠️ အနည်းဆုံး Competition တစ်ခု ရွေးပေးပါ။"
        )

    else:

        selected_ids = {
            item["id"]
            for item in selected_leagues
        }


        st.session_state.api_calls = 0

        st.session_state.remaining_quota = None

        st.session_state.last_scan_results = []


        # ----------------------------------------------------
        # SEARCH WINDOW
        # ----------------------------------------------------

        st.info(
            "🔎 Fixtures ရှာနေပါသည်...\n\n"
            f"{search_start.strftime('%Y-%m-%d %I:%M %p')} "
            "MMT → "
            f"{search_end.strftime('%Y-%m-%d %I:%M %p')} "
            "MMT"
        )


        fixtures = collect_selected_fixtures(
            selected_ids,
            search_start,
            search_end,
        )


        if not fixtures:

            st.warning(
                "⚠️ ရွေးထားသော leagues များအတွက် "
                "သတ်မှတ်ထားသော 12:00 PM → "
                "နောက်နေ့ 12:00 PM MMT window အတွင်း "
                "upcoming match မတွေ့ပါ။"
            )

        else:

            st.success(
                f"📅 Fixtures found: "
                f"{len(fixtures)}"
            )


            # ------------------------------------------------
            # LIMIT MATCHES
            # ------------------------------------------------

            fixtures_to_analyze = fixtures[
                :MAX_MATCHES_TO_ANALYZE
            ]


            st.info(
                f"📊 Analysis limit: "
                f"{len(fixtures_to_analyze)} "
                f"matches"
            )


            # ------------------------------------------------
            # TEAM CACHE
            # ------------------------------------------------

            home_cache = {}
            away_cache = {}


            evaluated = []


            # ------------------------------------------------
            # ANALYZE
            # ------------------------------------------------

            progress = st.progress(
                0
            )


            for index, fixture in enumerate(
                fixtures_to_analyze,
                1,
            ):

                home = fixture[
                    "teams"
                ][
                    "home"
                ]

                away = fixture[
                    "teams"
                ][
                    "away"
                ]


                home_id = home[
                    "id"
                ]

                away_id = away[
                    "id"
                ]

                home_name = home[
                    "name"
                ]

                away_name = away[
                    "name"
                ]


                # --------------------------------------------
                # HOME HISTORY
                # --------------------------------------------

                home_key = (
                    f"{home_id}_HOME"
                )


                if home_key not in home_cache:

                    home_cache[
                        home_key
                    ] = get_team_history(
                        home_id,
                        home_name,
                        "HOME",
                    )


                home_stats = home_cache[
                    home_key
                ]


                # --------------------------------------------
                # STOP IF API SAFETY LIMIT HIT
                # --------------------------------------------

                if (
                    st.session_state.api_calls
                    >= MAX_API_CALLS_PER_RUN
                ):

                    st.warning(
                        "🛑 API 80-call safety stop "
                        "ဖြစ်သွားပါပြီ။"
                    )

                    break


                # --------------------------------------------
                # AWAY HISTORY
                # --------------------------------------------

                away_key = (
                    f"{away_id}_AWAY"
                )


                if away_key not in away_cache:

                    away_cache[
                        away_key
                    ] = get_team_history(
                        away_id,
                        away_name,
                        "AWAY",
                    )


                away_stats = away_cache[
                    away_key
                ]


                # --------------------------------------------
                # MODEL
                # --------------------------------------------

                model = calculate_model(
                    home_stats,
                    away_stats,
                )


                # --------------------------------------------
                # TIME
                # --------------------------------------------

                display_date, display_time = (
                    format_fixture_time(
                        fixture
                    )
                )


                evaluated.append(
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
                            display_date,

                        "time":
                            display_time,

                        "signal":
                            model[
                                "signal"
                            ],

                        "prob":
                            model[
                                "probability"
                            ],

                        "edge":
                            model[
                                "edge"
                            ],

                        "model":
                            model,

                        "h_stats":
                            home_stats,

                        "a_stats":
                            away_stats,
                    }
                )


                progress.progress(
                    index
                    /
                    len(
                        fixtures_to_analyze
                    )
                )


            progress.empty()


            st.session_state.last_scan_results = (
                evaluated
            )


            st.session_state.scan_message = (
                f"Scan complete • "
                f"{len(evaluated)} matches"
            )


# ============================================================
# RESULTS
# ============================================================

results = (
    st.session_state.last_scan_results
)


if results:

    st.markdown(
        "---"
    )

    st.markdown(
        "## 📊 Match Results"
    )


    # --------------------------------------------------------
    # SORT:
    # OVER → UNDER → NEUTRAL
    # --------------------------------------------------------

    priority = {
        "OVER_2_5": 0,
        "UNDER_2_5": 1,
        "NEUTRAL": 2,
        "DATA_UNAVAILABLE": 3,
    }


    results.sort(
        key=lambda x: (
            priority.get(
                x["signal"],
                9
            ),
            x["date"],
            x["time"],
        )
    )


    # --------------------------------------------------------
    # RESULT CARDS
    # --------------------------------------------------------

    for match in results:

        signal = match[
            "signal"
        ]


        if signal == "OVER_2_5":

            signal_text = (
                "🟢 OVER 2.5"
            )

            signal_class = (
                "signal-over"
            )

        elif signal == "UNDER_2_5":

            signal_text = (
                "🔵 UNDER 2.5"
            )

            signal_class = (
                "signal-under"
            )

        else:

            signal_text = (
                "⚪ NEUTRAL"
            )

            signal_class = (
                "signal-neutral"
            )


        st.markdown(
            '<div class="match-card">',
            unsafe_allow_html=True,
        )


        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        c1, c2 = st.columns(
            [3, 1]
        )


        with c1:

            st.markdown(
                f"### ⚽ "
                f"{match['home']} "
                f"vs "
                f"{match['away']}"
            )

            st.write(
                f"🏆 {match['league']} "
                f"— {match['country']}"
            )

            st.write(
                f"📅 {match['date']} "
                f"  🕐 {match['time']} MMT"
            )


        with c2:

            st.markdown(
                f'<div class="{signal_class}">'
                f'{signal_text}'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.write("")


            prob = match[
                "prob"
            ]

            edge = match[
                "edge"
            ]


            if prob is None:

                st.write(
                    "Probability: —"
                )

            else:

                st.write(
                    f"Probability: "
                    f"**{prob:.1f}%**"
                )


            if edge is None:

                st.write(
                    "Model Edge: —"
                )

            else:

                st.write(
                    f"Model Edge: "
                    f"**{edge:+.1f}%**"
                )


        st.markdown(
            "---"
        )


        # ----------------------------------------------------
        # STATS
        # ----------------------------------------------------

        home_stats = match[
            "h_stats"
        ]

        away_stats = match[
            "a_stats"
        ]


        stat1, stat2 = st.columns(
            2
        )


        with stat1:

            st.markdown(
                f"#### 🏠 "
                f"{match['home']} — L5 HOME"
            )

            st.write(
                f"O2.5: "
                f"**{safe_pct(home_stats.get('over_pct'))}**"
            )

            st.write(
                f"U2.5: "
                f"**{safe_pct(home_stats.get('under_pct'))}**"
            )

            st.write(
                f"BTTS: "
                f"**{safe_pct(home_stats.get('btts_pct'))}**"
            )

            st.write(
                f"GF: "
                f"**{safe_num(home_stats.get('gf_avg'))}**"
            )

            st.write(
                f"GA: "
                f"**{safe_num(home_stats.get('ga_avg'))}**"
            )


        with stat2:

            st.markdown(
                f"#### ✈️ "
                f"{match['away']} — L5 AWAY"
            )

            st.write(
                f"O2.5: "
                f"**{safe_pct(away_stats.get('over_pct'))}**"
            )

            st.write(
                f"U2.5: "
                f"**{safe_pct(away_stats.get('under_pct'))}**"
            )

            st.write(
                f"BTTS: "
                f"**{safe_pct(away_stats.get('btts_pct'))}**"
            )

            st.write(
                f"GF: "
                f"**{safe_num(away_stats.get('gf_avg'))}**"
            )

            st.write(
                f"GA: "
                f"**{safe_num(away_stats.get('ga_avg'))}**"
            )


        # ----------------------------------------------------
        # RULE CHECKS
        # ----------------------------------------------------

        model = match[
            "model"
        ]


        with st.expander(
            "🔎 View model conditions"
        ):


            if signal == "OVER_2_5":

                st.markdown(
                    "### 🟢 OVER 2.5 Conditions"
                )


                checks = model[
                    "over_checks"
                ]


                st.write(
                    f"{condition_icon(checks['home_o25'])} "
                    f"Home L5 O2.5 ≥ 60% "
                    f"— "
                    f"{safe_pct(home_stats.get('over_pct'))}"
                )

                st.write(
                    f"{condition_icon(checks['away_o25'])} "
                    f"Away L5 O2.5 ≥ 60% "
                    f"— "
                    f"{safe_pct(away_stats.get('over_pct'))}"
                )

                st.write(
                    f"{condition_icon(checks['home_gf'])} "
                    f"Home GF > 1.5 "
                    f"— "
                    f"{safe_num(home_stats.get('gf_avg'))}"
                )

                st.write(
                    f"{condition_icon(checks['home_ga'])} "
                    f"Home GA > 1.0 "
                    f"— "
                    f"{safe_num(home_stats.get('ga_avg'))}"
                )

                st.write(
                    f"{condition_icon(checks['away_gf'])} "
                    f"Away GF > 1.0 "
                    f"— "
                    f"{safe_num(away_stats.get('gf_avg'))}"
                )

                st.write(
                    f"{condition_icon(checks['away_ga'])} "
                    f"Away GA > 1.0 "
                    f"— "
                    f"{safe_num(away_stats.get('ga_avg'))}"
                )

                st.write(
                    f"{condition_icon(checks['home_btts'])} "
                    f"Home BTTS ≥ 60% "
                    f"— "
                    f"{safe_pct(home_stats.get('btts_pct'))}"
                )

                st.write(
                    f"{condition_icon(checks['away_btts'])} "
                    f"Away BTTS ≥ 60% "
                    f"— "
                    f"{safe_pct(away_stats.get('btts_pct'))}"
                )

                st.write(
                    f"Model Edge > 5% "
                    f"— "
                    f"**{model['over_edge']:+.1f}%**"
                )


            elif signal == "UNDER_2_5":

                st.markdown(
                    "### 🔵 UNDER 2.5 Conditions"
                )


                checks = model[
                    "under_checks"
                ]


                st.write(
                    f"{condition_icon(checks['home_u25'])} "
                    f"Home L5 U2.5 ≥ 60% "
                    f"— "
                    f"{safe_pct(home_stats.get('under_pct'))}"
                )

                st.write(
                    f"{condition_icon(checks['away_u25'])} "
                    f"Away L5 U2.5 ≥ 60% "
                    f"— "
                    f"{safe_pct(away_stats.get('under_pct'))}"
                )

                st.write(
                    f"{condition_icon(checks['home_gf'])} "
                    f"Home GF < 1.3 "
                    f"— "
                    f"{safe_num(home_stats.get('gf_avg'))}"
                )

                st.write(
                    f"{condition_icon(checks['home_ga'])} "
                    f"Home GA < 1.0 "
                    f"— "
                    f"{safe_num(home_stats.get('ga_avg'))}"
                )

                st.write(
                    f"{condition_icon(checks['away_gf'])} "
                    f"Away GF < 1.1 "
                    f"— "
                    f"{safe_num(away_stats.get('gf_avg'))}"
                )

                st.write(
                    f"{condition_icon(checks['away_ga'])} "
                    f"Away GA < 1.2 "
                    f"— "
                    f"{safe_num(away_stats.get('ga_avg'))}"
                )

                st.write(
                    f"{condition_icon(checks['home_btts'])} "
                    f"Home BTTS < 50% "
                    f"— "
                    f"{safe_pct(home_stats.get('btts_pct'))}"
                )

                st.write(
                    f"{condition_icon(checks['away_btts'])} "
                    f"Away BTTS < 50% "
                    f"— "
                    f"{safe_pct(away_stats.get('btts_pct'))}"
                )

                st.write(
                    f"Model Edge > 5% "
                    f"— "
                    f"**{model['under_edge']:+.1f}%**"
                )


            else:

                st.markdown(
                    "### ⚪ Why NEUTRAL?"
                )


                over_failed = [
                    key
                    for key, value
                    in model[
                        "over_checks"
                    ].items()
                    if not value
                ]


                under_failed = [
                    key
                    for key, value
                    in model[
                        "under_checks"
                    ].items()
                    if not value
                ]


                st.write(
                    "OVER failed conditions:"
                )

                if over_failed:

                    st.write(
                        "❌ "
                        +
                        ", ".join(
                            over_failed
                        )
                    )

                else:

                    st.write(
                        "✅ All Over conditions passed "
                        "but edge condition failed."
                    )


                st.write(
                    "UNDER failed conditions:"
                )

                if under_failed:

                    st.write(
                        "❌ "
                        +
                        ", ".join(
                            under_failed
                        )
                    )

                else:

                    st.write(
                        "✅ All Under conditions passed "
                        "but edge condition failed."
                    )


        # ----------------------------------------------------
        # DATA WARNING
        # ----------------------------------------------------

        st.caption(
            "⚠️ L5 history = API-SPORTS 2024 "
            "historical proxy. "
            "xG မသုံးထားပါ။ "
            "BTTS condition ကို hard filter အဖြစ် "
            "သတ်မှတ်ထားသည်။"
        )


        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


# ============================================================
# FOOTER / API SAFETY
# ============================================================

st.markdown(
    "---"
)

footer_col1, footer_col2 = st.columns(
    2
)

with footer_col1:

    st.caption(
        f"API calls this run: "
        f"{st.session_state.api_calls} "
        f"/ {MAX_API_CALLS_PER_RUN}"
    )


with footer_col2:

    if (
        st.session_state.remaining_quota
        is not None
    ):

        st.caption(
            "API remaining quota: "
            f"{st.session_state.remaining_quota}"
        )

    else:

        st.caption(
            "API remaining quota: Not reported"
        )


st.caption(
    "Myanmar Time window: "
    "Today 12:00 PM → Tomorrow 12:00 PM MMT"
)

st.caption(
    "No xG • L5 O/U • L5 BTTS • GF/GA • Model Edge"
)
