import json
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
)


# ============================================================
# CONFIGURATION
# ============================================================

API_BASE = "https://v3.football.api-sports.io"

CACHE_FILE = "team_history_cache.json"
OUTPUT_FILE = "matches_data.json"

# ------------------------------------------------------------
# API SAFETY
# ------------------------------------------------------------

MAX_API_CALLS_PER_RUN = 80

# Stop before quota becomes dangerously low
MIN_REMAINING_QUOTA = 15

# Delay between API requests
API_DELAY_SECONDS = 1.5

# Maximum matches shown/evaluated
MAX_MATCHES = 50

# History sample
L5_MATCHES = 5

# Historical proxy season
#
# IMPORTANT:
# Change this only if your API plan provides another season.
#
# API-SPORTS free plan previously tested by us did not provide
# current 2025/2026 team-history data reliably.
HISTORY_SEASON = 2024

# Myanmar Time
MMT_TZ = timezone(timedelta(hours=6, minutes=30))


# ============================================================
# LEAGUE DATABASE
# ============================================================
#
# API-FOOTBALL / API-SPORTS league IDs
#
# Main leagues from your requested list.
# ------------------------------------------------------------

LEAGUES = {

    # ========================================================
    # ARGENTINA
    # ========================================================

    128: {
        "country": "Argentina",
        "name": "Liga Profesional",
        "group": "Main Leagues",
    },

    # ========================================================
    # AUSTRALIA
    # ========================================================

    188: {
        "country": "Australia",
        "name": "A-League",
        "group": "Main Leagues",
    },

    # ========================================================
    # AUSTRIA
    # ========================================================

    218: {
        "country": "Austria",
        "name": "Bundesliga",
        "group": "Main Leagues",
    },

    # ========================================================
    # BELGIUM
    # ========================================================

    144: {
        "country": "Belgium",
        "name": "Pro League",
        "group": "Main Leagues",
    },

    # ========================================================
    # BRAZIL
    # ========================================================

    71: {
        "country": "Brazil",
        "name": "Serie A",
        "group": "Main Leagues",
    },

    # ========================================================
    # CHILE
    # ========================================================

    265: {
        "country": "Chile",
        "name": "Primera División",
        "group": "Main Leagues",
    },

    # ========================================================
    # CHINA
    # ========================================================

    169: {
        "country": "China",
        "name": "Super League",
        "group": "Main Leagues",
    },

    # ========================================================
    # COLOMBIA
    # ========================================================

    239: {
        "country": "Colombia",
        "name": "Primera A",
        "group": "Main Leagues",
    },

    # ========================================================
    # CROATIA
    # ========================================================

    210: {
        "country": "Croatia",
        "name": "HNL",
        "group": "Main Leagues",
    },

    # ========================================================
    # DENMARK
    # ========================================================

    119: {
        "country": "Denmark",
        "name": "Superliga",
        "group": "Main Leagues",
    },

    # ========================================================
    # ECUADOR
    # ========================================================

    242: {
        "country": "Ecuador",
        "name": "Liga Pro",
        "group": "Main Leagues",
    },

    # ========================================================
    # GREECE
    # ========================================================

    197: {
        "country": "Greece",
        "name": "Super League",
        "group": "Main Leagues",
    },

    # ========================================================
    # JAPAN
    # ========================================================

    98: {
        "country": "Japan",
        "name": "J1 League",
        "group": "Main Leagues",
    },

    # ========================================================
    # MEXICO
    # ========================================================

    262: {
        "country": "Mexico",
        "name": "Liga MX",
        "group": "Main Leagues",
    },

    # ========================================================
    # NETHERLANDS
    # ========================================================

    88: {
        "country": "Netherlands",
        "name": "Eredivisie",
        "group": "Main Leagues",
    },

    # ========================================================
    # NORWAY
    # ========================================================

    103: {
        "country": "Norway",
        "name": "Eliteserien",
        "group": "Main Leagues",
    },

    # ========================================================
    # PERU
    # ========================================================

    281: {
        "country": "Peru",
        "name": "Liga 1",
        "group": "Main Leagues",
    },

    # ========================================================
    # POLAND
    # ========================================================

    106: {
        "country": "Poland",
        "name": "Ekstraklasa",
        "group": "Main Leagues",
    },

    # ========================================================
    # PORTUGAL
    # ========================================================

    94: {
        "country": "Portugal",
        "name": "Primeira Liga",
        "group": "Main Leagues",
    },

    # ========================================================
    # SAUDI ARABIA
    # ========================================================

    307: {
        "country": "Saudi Arabia",
        "name": "Saudi Pro League",
        "group": "Main Leagues",
    },

    # ========================================================
    # SCOTLAND
    # ========================================================

    179: {
        "country": "Scotland",
        "name": "Premiership",
        "group": "Main Leagues",
    },

    # ========================================================
    # SWEDEN
    # ========================================================

    113: {
        "country": "Sweden",
        "name": "Allsvenskan",
        "group": "Main Leagues",
    },

    # ========================================================
    # SWITZERLAND
    # ========================================================

    207: {
        "country": "Switzerland",
        "name": "Super League",
        "group": "Main Leagues",
    },

    # ========================================================
    # TURKEY
    # ========================================================

    203: {
        "country": "Turkey",
        "name": "Süper Lig",
        "group": "Main Leagues",
    },

    # ========================================================
    # USA
    # ========================================================

    253: {
        "country": "USA",
        "name": "MLS",
        "group": "Main Leagues",
    },

    # ========================================================
    # ENGLAND
    # ========================================================

    39: {
        "country": "England",
        "name": "Premier League",
        "group": "Second-Tier Included",
    },

    40: {
        "country": "England",
        "name": "Championship",
        "group": "Second-Tier Included",
    },

    # ========================================================
    # SPAIN
    # ========================================================

    140: {
        "country": "Spain",
        "name": "LaLiga",
        "group": "Second-Tier Included",
    },

    141: {
        "country": "Spain",
        "name": "LaLiga 2",
        "group": "Second-Tier Included",
    },

    # ========================================================
    # FRANCE
    # ========================================================

    61: {
        "country": "France",
        "name": "Ligue 1",
        "group": "Second-Tier Included",
    },

    62: {
        "country": "France",
        "name": "Ligue 2",
        "group": "Second-Tier Included",
    },

    # ========================================================
    # GERMANY
    # ========================================================

    78: {
        "country": "Germany",
        "name": "Bundesliga",
        "group": "Second-Tier Included",
    },

    79: {
        "country": "Germany",
        "name": "2. Bundesliga",
        "group": "Second-Tier Included",
    },

    # ========================================================
    # ITALY
    # ========================================================

    135: {
        "country": "Italy",
        "name": "Serie A",
        "group": "Second-Tier Included",
    },

    136: {
        "country": "Italy",
        "name": "Serie B",
        "group": "Second-Tier Included",
    },

    # ========================================================
    # UEFA CLUB COMPETITIONS
    # ========================================================

    2: {
        "country": "World",
        "name": "UEFA Champions League",
        "group": "European Cups",
    },

    3: {
        "country": "World",
        "name": "UEFA Europa League",
        "group": "European Cups",
    },

    848: {
        "country": "World",
        "name": "UEFA Europa Conference League",
        "group": "European Cups",
    },
}


# ============================================================
# SESSION STATE
# ============================================================

if "api_calls" not in st.session_state:
    st.session_state.api_calls = 0

if "remaining_quota" not in st.session_state:
    st.session_state.remaining_quota = None

if "current_key_index" not in st.session_state:
    st.session_state.current_key_index = 0

if "stop_reason" not in st.session_state:
    st.session_state.stop_reason = ""

if "history_cache" not in st.session_state:
    st.session_state.history_cache = None


# ============================================================
# API KEY
# ============================================================

raw_keys = os.environ.get(
    "API_KEYS_POOL",
    ""
).strip()

if not raw_keys:

    st.error(
        """
        ❌ API_KEYS_POOL မတွေ့ပါ။

        Streamlit Cloud → Settings → Secrets

        မှာ API_KEYS_POOL ထည့်ပါ။

        ဥပမာ:

        API_KEYS_POOL="YOUR_API_KEY"
        """
    )

    st.stop()


API_KEYS = [
    key.strip()
    for key in raw_keys.split(",")
    if key.strip()
]


if not API_KEYS:

    st.error(
        "❌ API_KEYS_POOL ထဲမှာ valid API key မရှိပါ။"
    )

    st.stop()


# ============================================================
# ACTIVE API KEY
# ============================================================

def get_active_key():

    index = st.session_state.current_key_index

    if index >= len(API_KEYS):
        index = 0
        st.session_state.current_key_index = 0

    return API_KEYS[index]


# ============================================================
# LOAD CACHE
# ============================================================

def load_cache():

    if st.session_state.history_cache is not None:
        return st.session_state.history_cache

    if not os.path.exists(CACHE_FILE):
        st.session_state.history_cache = {}
        return {}

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if isinstance(data, dict):

            st.session_state.history_cache = data

            return data

    except Exception:
        pass

    st.session_state.history_cache = {}

    return {}


# ============================================================
# SAVE CACHE
# ============================================================

def save_cache(cache):

    st.session_state.history_cache = cache

    try:

        with open(
            CACHE_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                cache,
                file,
                indent=2,
                ensure_ascii=False,
            )

    except Exception:
        pass


history_cache = load_cache()


# ============================================================
# API REQUEST
# ============================================================

def api_request(
    endpoint,
    params=None,
    purpose="",
):

    # --------------------------------------------------------
    # HARD 80 REQUEST LIMIT
    # --------------------------------------------------------

    if (
        st.session_state.api_calls
        >= MAX_API_CALLS_PER_RUN
    ):

        st.session_state.stop_reason = (
            f"API request limit reached "
            f"({MAX_API_CALLS_PER_RUN})."
        )

        return None


    # --------------------------------------------------------
    # QUOTA SAFETY
    # --------------------------------------------------------

    remaining = (
        st.session_state.remaining_quota
    )

    if (
        remaining is not None
        and remaining <= MIN_REMAINING_QUOTA
    ):

        st.session_state.stop_reason = (
            f"API quota safety stop. "
            f"Remaining quota = {remaining}."
        )

        return None


    url = f"{API_BASE}/{endpoint}"

    headers = {
        "x-apisports-key": get_active_key()
    }


    st.session_state.api_calls += 1


    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
        )


        # ----------------------------------------------------
        # READ QUOTA
        # ----------------------------------------------------

        quota_headers = [
            "x-ratelimit-requests-remaining",
            "X-RateLimit-Requests-Remaining",
        ]

        for header in quota_headers:

            value = response.headers.get(
                header
            )

            if value is not None:

                try:

                    st.session_state.remaining_quota = int(
                        value
                    )

                except ValueError:
                    pass

                break


        # ----------------------------------------------------
        # HTTP ERROR
        # ----------------------------------------------------

        if response.status_code != 200:

            # Try next key on authentication errors
            if response.status_code in [401, 403]:

                if (
                    len(API_KEYS) > 1
                    and
                    st.session_state.current_key_index
                    < len(API_KEYS) - 1
                ):

                    st.session_state.current_key_index += 1

            if response.status_code == 429:

                st.session_state.stop_reason = (
                    "API rate limit reached."
                )

            return None


        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        try:

            data = response.json()

        except Exception:

            return None


        errors = data.get(
            "errors",
            {},
        )

        if errors:

            return None


        return data


    except requests.RequestException:

        return None


# ============================================================
# MMT SEARCH WINDOW
# ============================================================
#
# IMPORTANT:
#
# Every day:
#
# TODAY 12:00 PM MMT
#       ↓
# TOMORROW 12:00 PM MMT
#
# This is NOT midnight-to-midnight.
# ============================================================

def get_mmt_search_window():

    now = datetime.now(
        MMT_TZ
    )

    today_noon = datetime(
        now.year,
        now.month,
        now.day,
        12,
        0,
        0,
        tzinfo=MMT_TZ,
    )

    # Before 12 PM:
    #
    # The active window started yesterday 12 PM.
    #
    if now < today_noon:

        window_start = (
            today_noon
            - timedelta(days=1)
        )

    else:

        window_start = today_noon


    window_end = (
        window_start
        + timedelta(days=1)
    )


    return (
        now,
        window_start,
        window_end,
    )


now_mmt, window_start, window_end = (
    get_mmt_search_window()
)


# ============================================================
# DATE STRINGS
# ============================================================

search_dates = [
    window_start.strftime("%Y-%m-%d"),
    window_end.strftime("%Y-%m-%d"),
]


# ============================================================
# FETCH DAILY FIXTURES
# ============================================================

def fetch_daily_fixtures(
    date_string
):

    data = api_request(
        "fixtures",
        params={
            "date": date_string,
            "timezone": "Asia/Yangon",
        },
        purpose=(
            f"Fixtures for "
            f"{date_string} MMT"
        ),
    )

    if data is None:
        return []

    return data.get(
        "response",
        [],
    )


# ============================================================
# FETCH FIXTURES FOR WINDOW
# ============================================================

def fetch_window_fixtures():

    all_fixtures = []

    seen_ids = set()


    for date_string in search_dates:

        fixtures = fetch_daily_fixtures(
            date_string
        )


        for fixture in fixtures:

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

            all_fixtures.append(
                fixture
            )


        # Delay only if another request is needed
        if date_string != search_dates[-1]:

            if (
                st.session_state.api_calls
                < MAX_API_CALLS_PER_RUN
            ):

                time.sleep(
                    API_DELAY_SECONDS
                )


    return all_fixtures


# ============================================================
# FILTER FIXTURES
# ============================================================

def filter_fixtures(
    fixtures,
    selected_league_ids,
):

    selected = []

    seen = set()


    for fixture in fixtures:

        fixture_id = (
            fixture
            .get("fixture", {})
            .get("id")
        )

        if not fixture_id:
            continue

        if fixture_id in seen:
            continue

        seen.add(
            fixture_id
        )


        league = fixture.get(
            "league",
            {}
        )

        league_id = league.get(
            "id"
        )


        # League filter
        if league_id not in selected_league_ids:
            continue


        status = (
            fixture
            .get("fixture", {})
            .get("status", {})
            .get("short")
        )


        # Prematch only
        if status not in [
            "NS",
            "TBD",
            "PST",
        ]:

            continue


        fixture_date = (
            fixture
            .get("fixture", {})
            .get("date")
        )

        if not fixture_date:
            continue


        try:

            fixture_dt = datetime.fromisoformat(
                fixture_date
            )

        except Exception:

            continue


        if fixture_dt.tzinfo is None:

            fixture_dt = fixture_dt.replace(
                tzinfo=timezone.utc
            )


        # Convert fixture to MMT
        fixture_mmt = fixture_dt.astimezone(
            MMT_TZ
        )


        # ----------------------------------------------------
        # EXACT MMT WINDOW
        # ----------------------------------------------------

        if not (
            window_start
            <= fixture_mmt
            < window_end
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


    # Sort by MMT kickoff time
    selected.sort(
        key=lambda x: (
            x
            .get("fixture", {})
            .get("date", "")
        )
    )


    return selected


# ============================================================
# TEAM HISTORY
# ============================================================

def get_team_history(
    team_id,
    team_name,
    venue,
):

    cache_key = (
        f"{team_id}_"
        f"{HISTORY_SEASON}"
    )


    # --------------------------------------------------------
    # CACHE
    # --------------------------------------------------------

    if cache_key in history_cache:

        fixtures = history_cache[
            cache_key
        ]

    else:

        data = api_request(
            "fixtures",
            params={
                "team": team_id,
                "season": HISTORY_SEASON,
            },
            purpose=(
                f"{team_name} "
                f"history {HISTORY_SEASON}"
            ),
        )


        if data is None:

            return {
                "status": "API_ERROR",
                "sample_size": 0,
                "matches": [],
                "over_pct": None,
                "under_pct": None,
                "btts_pct": None,
                "gf_avg": None,
                "ga_avg": None,
            }


        fixtures = data.get(
            "response",
            []
        )


        history_cache[
            cache_key
        ] = fixtures

        save_cache(
            history_cache
        )


    # --------------------------------------------------------
    # FINISHED MATCHES
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
            or away_goals is None
        ):

            continue


        # ----------------------------------------------------
        # HOME / AWAY FILTER
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
                    "Unknown",
                ),

                "away": away.get(
                    "name",
                    "Unknown",
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


    # Newest first
    finished.sort(
        key=lambda x: x["date"],
        reverse=True,
    )


    selected = finished[
        :L5_MATCHES
    ]


    # --------------------------------------------------------
    # EMPTY DATA
    # --------------------------------------------------------

    if not selected:

        return {
            "status": "INSUFFICIENT_L5_DATA",
            "sample_size": 0,
            "matches": [],
            "over_pct": None,
            "under_pct": None,
            "btts_pct": None,
            "gf_avg": None,
            "ga_avg": None,
        }


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


        # Team GF / GA
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


    return {

        "status": (
            "PROXY_2024_25"
            if count >= 5
            else "PARTIAL_PROXY_2024_25"
        ),

        "data_source": (
            "API-SPORTS 2024 season "
            "historical proxy"
        ),

        "sample_size": count,

        "over_pct": round(
            over_count
            / count
            * 100,
            1,
        ),

        "under_pct": round(
            (
                count
                - over_count
            )
            / count
            * 100,
            1,
        ),

        "btts_pct": round(
            btts_count
            / count
            * 100,
            1,
        ),

        "gf_avg": round(
            gf_total
            / count,
            2,
        ),

        "ga_avg": round(
            ga_total
            / count,
            2,
        ),

        "scorelines": scorelines,
    }


# ============================================================
# MODEL
# ============================================================
#
# NO xG
#
# OVER:
#
# Home L5 O2.5 >= 60%
# Away L5 O2.5 >= 60%
# Home GF > 1.5
# Home GA > 1.0
# Away GF > 1.0
# Away GA > 1.0
# Home BTTS >= 60%
# Away BTTS >= 60%
# Model edge >= 5%
#
# UNDER:
#
# Home L5 U2.5 >= 60%
# Away L5 U2.5 >= 60%
# Home GF < 1.3
# Home GA < 1.0
# Away GF < 1.1
# Away GA < 1.2
# Home BTTS < 50%
# Away BTTS < 50%
# Model edge >= 5%
# ============================================================

def calculate_model(
    home_stats,
    away_stats,
):

    valid_statuses = [
        "PROXY_2024_25",
        "PARTIAL_PROXY_2024_25",
    ]


    if (
        home_stats.get(
            "status"
        )
        not in valid_statuses
        or
        away_stats.get(
            "status"
        )
        not in valid_statuses
    ):

        return {
            "signal": "DATA_UNAVAILABLE",
            "probability": None,
            "edge": None,
            "model_status": (
                "INSUFFICIENT_DATA"
            ),
            "over_checks": {},
            "under_checks": {},
        }


    if (
        home_stats.get(
            "sample_size",
            0,
        ) < 5
        or
        away_stats.get(
            "sample_size",
            0,
        ) < 5
    ):

        return {
            "signal": "DATA_UNAVAILABLE",
            "probability": None,
            "edge": None,
            "model_status": (
                "INSUFFICIENT_L5_DATA"
            ),
            "over_checks": {},
            "under_checks": {},
        }


    # ========================================================
    # OVER SCORE
    # ========================================================

    over_components = [

        home_stats[
            "over_pct"
        ],

        away_stats[
            "over_pct"
        ],

        home_stats[
            "btts_pct"
        ],

        away_stats[
            "btts_pct"
        ],
    ]


    avg_over = sum(
        over_components[:2]
    ) / 2


    avg_btts = sum(
        over_components[2:]
    ) / 2


    # Goal environment
    goal_environment = (

        home_stats[
            "gf_avg"
        ]

        + home_stats[
            "ga_avg"
        ]

        + away_stats[
            "gf_avg"
        ]

        + away_stats[
            "ga_avg"
        ]
    )


    # Convert goal environment
    # into a 0-100 score
    goal_score = min(
        100,
        goal_environment
        / 6.0
        * 100,
    )


    # --------------------------------------------------------
    # Probability
    #
    # No xG
    # --------------------------------------------------------

    probability = (

        avg_over * 0.40

        + avg_btts * 0.25

        + goal_score * 0.35
    )


    probability = round(
        max(
            0,
            min(
                100,
                probability,
            ),
        ),
        1,
    )


    # --------------------------------------------------------
    # Edge
    # --------------------------------------------------------

    edge = round(
        probability - 60,
        1,
    )


    # ========================================================
    # OVER 2.5 CONFIRMATION
    # ========================================================

    over_checks = {

        "home_o25_60": (
            home_stats[
                "over_pct"
            ] >= 60
        ),

        "away_o25_60": (
            away_stats[
                "over_pct"
            ] >= 60
        ),

        "home_gf_15": (
            home_stats[
                "gf_avg"
            ] > 1.5
        ),

        "home_ga_10": (
            home_stats[
                "ga_avg"
            ] > 1.0
        ),

        "away_gf_10": (
            away_stats[
                "gf_avg"
            ] > 1.0
        ),

        "away_ga_10": (
            away_stats[
                "ga_avg"
            ] > 1.0
        ),

        # IMPORTANT:
        # BTTS MUST BE >= 60%
        #
        # This fixes the previous problem
        # where a team with BTTS 40%
        # could still get OVER.
        "home_btts_60": (
            home_stats[
                "btts_pct"
            ] >= 60
        ),

        "away_btts_60": (
            away_stats[
                "btts_pct"
            ] >= 60
        ),

        "edge_5": (
            edge >= 5
        ),
    }


    strong_over = all(
        over_checks.values()
    )


    # ========================================================
    # UNDER 2.5 CONFIRMATION
    # ========================================================

    under_checks = {

        "home_u25_60": (
            home_stats[
                "under_pct"
            ] >= 60
        ),

        "away_u25_60": (
            away_stats[
                "under_pct"
            ] >= 60
        ),

        "home_gf_13": (
            home_stats[
                "gf_avg"
            ] < 1.3
        ),

        "home_ga_10": (
            home_stats[
                "ga_avg"
            ] < 1.0
        ),

        "away_gf_11": (
            away_stats[
                "gf_avg"
            ] < 1.1
        ),

        "away_ga_12": (
            away_stats[
                "ga_avg"
            ] < 1.2
        ),

        "home_btts_50": (
            home_stats[
                "btts_pct"
            ] < 50
        ),

        "away_btts_50": (
            away_stats[
                "btts_pct"
            ] < 50
        ),

        "edge_5": (
            edge >= 5
        ),
    }


    strong_under = all(
        under_checks.values()
    )


    # ========================================================
    # FINAL SIGNAL
    # ========================================================

    if strong_over:

        signal = "OVER_2_5"

    elif strong_under:

        signal = "UNDER_2_5"

    else:

        signal = "NEUTRAL"


    return {

        "signal": signal,

        "probability": probability,

        "edge": edge,

        "model_status": (
            "PROXY_MODEL_2024_25"
        ),

        "over_checks": over_checks,

        "under_checks": under_checks,
    }


# ============================================================
# EVALUATE MATCHES
# ============================================================

def evaluate_matches(
    selected_fixtures
):

    evaluated = []

    team_cache = {}


    # --------------------------------------------------------
    # Unique teams
    # --------------------------------------------------------

    unique_requests = []

    seen_requests = set()


    for fixture in selected_fixtures:

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


        home_request = (
            home["id"],
            "HOME",
        )

        away_request = (
            away["id"],
            "AWAY",
        )


        for request in [
            home_request,
            away_request,
        ]:

            if request not in seen_requests:

                seen_requests.add(
                    request
                )

                unique_requests.append(
                    request
                )


    # --------------------------------------------------------
    # Fetch history
    # --------------------------------------------------------

    for team_id, venue in unique_requests:

        if (
            st.session_state.api_calls
            >= MAX_API_CALLS_PER_RUN
        ):

            break


        cache_key = (
            f"{team_id}_"
            f"{venue}_"
            f"{HISTORY_SEASON}"
        )


        if cache_key in team_cache:

            continue


        # Get team name from fixture
        team_name = "Unknown"


        for fixture in selected_fixtures:

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


            if home.get(
                "id"
            ) == team_id:

                team_name = home.get(
                    "name",
                    "Unknown",
                )

                break


            if away.get(
                "id"
            ) == team_id:

                team_name = away.get(
                    "name",
                    "Unknown",
                )

                break


        team_cache[
            cache_key
        ] = get_team_history(
            team_id,
            team_name,
            venue,
        )


        if (
            st.session_state.api_calls
            < MAX_API_CALLS_PER_RUN
        ):

            time.sleep(
                API_DELAY_SECONDS
            )


    # --------------------------------------------------------
    # Match evaluation
    # --------------------------------------------------------

    for fixture in selected_fixtures:

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


        home_key = (
            f"{home_id}_"
            f"HOME_"
            f"{HISTORY_SEASON}"
        )

        away_key = (
            f"{away_id}_"
            f"AWAY_"
            f"{HISTORY_SEASON}"
        )


        home_stats = team_cache.get(
            home_key,
            {
                "status": "API_ERROR",
                "sample_size": 0,
            },
        )


        away_stats = team_cache.get(
            away_key,
            {
                "status": "API_ERROR",
                "sample_size": 0,
            },
        )


        model = calculate_model(
            home_stats,
            away_stats,
        )


        fixture_date = (
            fixture[
                "fixture"
            ][
                "date"
            ]
        )


        try:

            local_dt = datetime.fromisoformat(
                fixture_date
            ).astimezone(
                MMT_TZ
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


        evaluated.append(
            {

                "fixture_id": fixture[
                    "fixture"
                ][
                    "id"
                ],

                "league_id": fixture[
                    "league"
                ][
                    "id"
                ],

                "league": fixture[
                    "league"
                ][
                    "name"
                ],

                "country": fixture[
                    "league"
                ].get(
                    "country",
                    "",
                ),

                "home": home_name,

                "away": away_name,

                "date": display_date,

                "time": display_time,

                "signal": model[
                    "signal"
                ],

                "prob": model[
                    "probability"
                ],

                "edge": model[
                    "edge"
                ],

                "model_status": model[
                    "model_status"
                ],

                "h_stats": home_stats,

                "a_stats": away_stats,

                "over_checks": model.get(
                    "over_checks",
                    {},
                ),

                "under_checks": model.get(
                    "under_checks",
                    {},
                ),

                "xg_used": False,
            }
        )


    return evaluated


# ============================================================
# SIGNAL PRIORITY
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


# ============================================================
# HEADER
# ============================================================

st.title(
    "⚽ Football Prematch Scanner"
)

st.caption(
    "Multi-League Prematch Analysis"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ Scanner Settings"
    )


    st.write(
        "### 🕐 Search Window"
    )

    st.write(
        f"**{window_start.strftime('%Y-%m-%d %I:%M %p')} MMT**"
    )

    st.write(
        "→"
    )

    st.write(
        f"**{window_end.strftime('%Y-%m-%d %I:%M %p')} MMT**"
    )


    st.divider()


    st.write(
        "### 🛡️ API Safety"
    )

    st.write(
        f"Max API calls: "
        f"**{MAX_API_CALLS_PER_RUN}**"
    )

    st.write(
        f"Calls used: "
        f"**{st.session_state.api_calls}**"
    )


    if (
        st.session_state.remaining_quota
        is not None
    ):

        st.write(
            "Remaining quota: "
            f"**{st.session_state.remaining_quota}**"
        )


    st.divider()


    st.write(
        "### 📊 Model"
    )

    st.write(
        "xG: **NOT USED**"
    )

    st.write(
        "L5: **HOME / AWAY separated**"
    )

    st.write(
        "Over BTTS: **≥ 60%**"
    )

    st.write(
        "Under BTTS: **< 50%**"
    )

    st.write(
        "Edge: **≥ 5%**"
    )


# ============================================================
# TOP STATUS
# ============================================================

col1, col2, col3, col4 = st.columns(
    4
)


with col1:

    st.metric(
        "SEARCH WINDOW",
        (
            f"{window_start.strftime('%m-%d %I:%M')}"
            " → "
            f"{window_end.strftime('%m-%d %I:%M')}"
            " MMT"
        ),
    )


with col2:

    st.metric(
        "MODE",
        "MULTI-LEAGUE",
    )


with col3:

    st.metric(
        "MAX API",
        str(
            MAX_API_CALLS_PER_RUN
        ),
    )


with col4:

    remaining_display = (
        st.session_state.remaining_quota
        if
        st.session_state.remaining_quota
        is not None
        else "—"
    )

    st.metric(
        "API REMAINING",
        str(
            remaining_display
        ),
    )


# ============================================================
# LEAGUE FILTER UI
# ============================================================

st.header(
    "🏆 League Filter"
)


# Group leagues
grouped = {}

for league_id, info in LEAGUES.items():

    group = info[
        "group"
    ]

    if group not in grouped:
        grouped[group] = []

    grouped[group].append(
        (
            league_id,
            info[
                "country"
            ],
            info[
                "name"
            ],
        )
    )


# Default ALL leagues
default_league_ids = list(
    LEAGUES.keys()
)


selected_league_ids = []


# ------------------------------------------------------------
# Quick selection
# ------------------------------------------------------------

quick_col1, quick_col2, quick_col3 = st.columns(
    3
)


with quick_col1:

    all_leagues = st.checkbox(
        "Select ALL leagues",
        value=True,
    )


with quick_col2:

    main_only = st.checkbox(
        "Main leagues only",
        value=False,
    )


with quick_col3:

    cups_only = st.checkbox(
        "European Cups only",
        value=False,
    )


if all_leagues:

    selected_league_ids = (
        default_league_ids.copy()
    )


elif main_only:

    selected_league_ids = [

        league_id

        for league_id, info
        in LEAGUES.items()

        if info[
            "group"
        ] == "Main Leagues"
    ]


elif cups_only:

    selected_league_ids = [

        league_id

        for league_id, info
        in LEAGUES.items()

        if info[
            "group"
        ] == "European Cups"
    ]


else:

    for group_name, leagues in grouped.items():

        st.subheader(
            group_name
        )


        for league_id, country, name in leagues:

            checked = st.checkbox(
                f"{country} — {name}",
                value=True,
                key=f"league_{league_id}",
            )

            if checked:

                selected_league_ids.append(
                    league_id
                )


# ------------------------------------------------------------
# Always show selected information safely
# ------------------------------------------------------------

selected_names = [

    LEAGUES[
        league_id
    ][
        "name"
    ]

    for league_id
    in selected_league_ids

    if league_id in LEAGUES
]


if selected_names:

    st.info(
        f"Selected leagues: "
        f"**{len(selected_names)}**"
    )

    with st.expander(
        "View selected leagues"
    ):

        st.write(
            ", ".join(
                selected_names
            )
        )

else:

    st.warning(
        "⚠️ No league selected."
    )


# ============================================================
# SEARCH BUTTON
# ============================================================

st.divider()


run_scan = st.button(
    "🔎 SEARCH MATCHES",
    type="primary",
    use_container_width=True,
)


# ============================================================
# SCAN
# ============================================================

if run_scan:

    # --------------------------------------------------------
    # Reset current-run state
    # --------------------------------------------------------

    st.session_state.api_calls = 0

    st.session_state.remaining_quota = None

    st.session_state.stop_reason = ""

    # --------------------------------------------------------
    # Validate league selection
    # --------------------------------------------------------

    if not selected_league_ids:

        st.error(
            "❌ League တစ်ခုမှ မရွေးထားပါ။"
        )

        st.stop()


    # --------------------------------------------------------
    # Display exact MMT window
    # --------------------------------------------------------

    st.subheader(
        "🕐 SEARCH WINDOW"
    )

    st.success(
        (
            f"{window_start.strftime('%Y-%m-%d %I:%M %p')} MMT"
            f" → "
            f"{window_end.strftime('%Y-%m-%d %I:%M %p')} MMT"
        )
    )


    # --------------------------------------------------------
    # Fetch fixtures
    # --------------------------------------------------------

    with st.spinner(
        "Fetching fixtures..."
    ):

        raw_fixtures = (
            fetch_window_fixtures()
        )


    st.write(
        f"Raw fixtures received: "
        f"**{len(raw_fixtures)}**"
    )


    # --------------------------------------------------------
    # Filter
    # --------------------------------------------------------

    filtered_fixtures = filter_fixtures(
        raw_fixtures,
        selected_league_ids,
    )


    # --------------------------------------------------------
    # Maximum matches
    # --------------------------------------------------------

    if len(
        filtered_fixtures
    ) > MAX_MATCHES:

        filtered_fixtures = (
            filtered_fixtures[
                :MAX_MATCHES
            ]
        )


    # --------------------------------------------------------
    # No matches
    # --------------------------------------------------------

    if not filtered_fixtures:

        st.warning(
            "⚠️ လက်ရှိ MMT search window အတွင်း "
            "ရွေးထားသော league များမှ "
            "prematch data မတွေ့ပါ။"
        )


        st.info(
            (
                "Search window = "
                f"{window_start.strftime('%Y-%m-%d %I:%M %p')} "
                "→ "
                f"{window_end.strftime('%Y-%m-%d %I:%M %p')} MMT"
            )
        )


    else:

        st.success(
            f"Found {len(filtered_fixtures)} "
            f"prematch matches."
        )


        # ----------------------------------------------------
        # Basic fixture list
        # ----------------------------------------------------

        st.header(
            "📅 MATCHES"
        )


        fixture_rows = []


        for fixture in filtered_fixtures:

            fixture_mmt = datetime.fromisoformat(
                fixture[
                    "fixture"
                ][
                    "date"
                ]
            ).astimezone(
                MMT_TZ
            )


            fixture_rows.append(
                {
                    "Date": fixture_mmt.strftime(
                        "%Y-%m-%d"
                    ),

                    "Time MMT": fixture_mmt.strftime(
                        "%H:%M"
                    ),

                    "League": fixture[
                        "league"
                    ][
                        "name"
                    ],

                    "Country": fixture[
                        "league"
                    ].get(
                        "country",
                        "",
                    ),

                    "Home": fixture[
                        "teams"
                    ][
                        "home"
                    ][
                        "name"
                    ],

                    "Away": fixture[
                        "teams"
                    ][
                        "away"
                    ][
                        "name"
                    ],
                }
            )


        st.dataframe(
            fixture_rows,
            use_container_width=True,
            hide_index=True,
        )


        # ----------------------------------------------------
        # Evaluate
        # ----------------------------------------------------

        st.header(
            "📊 ANALYSIS"
        )


        with st.spinner(
            "Calculating L5 HOME/AWAY statistics..."
        ):

            evaluated_matches = (
                evaluate_matches(
                    filtered_fixtures
                )
            )


        # ----------------------------------------------------
        # Sort
        # ----------------------------------------------------

        evaluated_matches.sort(
            key=lambda x: (
                signal_priority(
                    x[
                        "signal"
                    ]
                ),

                x[
                    "date"
                ],

                x[
                    "time"
                ],
            )
        )


        # ----------------------------------------------------
        # Cards
        # ----------------------------------------------------

        for match in evaluated_matches:

            signal = match[
                "signal"
            ]


            if signal == "OVER_2_5":

                signal_text = (
                    "🟢 OVER 2.5"
                )

            elif signal == "UNDER_2_5":

                signal_text = (
                    "🔵 UNDER 2.5"
                )

            elif signal == "DATA_UNAVAILABLE":

                signal_text = (
                    "⚪ DATA UNAVAILABLE"
                )

            else:

                signal_text = (
                    "⚪ NEUTRAL"
                )


            with st.container(
                border=True
            ):

                st.subheader(
                    (
                        f"{match['home']} "
                        f"vs "
                        f"{match['away']}"
                    )
                )


                st.write(
                    (
                        f"🏆 {match['league']} "
                        f"({match['country']})"
                    )
                )


                st.write(
                    (
                        f"📅 {match['date']} "
                        f"⏰ {match['time']} MMT"
                    )
                )


                c1, c2, c3, c4 = st.columns(
                    4
                )


                with c1:

                    st.metric(
                        "Signal",
                        signal_text,
                    )


                with c2:

                    probability = (
                        match[
                            "prob"
                        ]
                    )

                    st.metric(
                        "Probability",
                        (
                            str(
                                probability
                            )
                            if probability
                            is not None
                            else "—"
                        ),
                    )


                with c3:

                    edge = (
                        match[
                            "edge"
                        ]
                    )

                    st.metric(
                        "Model Edge",
                        (
                            f"{edge}%"
                            if edge
                            is not None
                            else "—"
                        ),
                    )


                with c4:

                    st.metric(
                        "xG",
                        "NO",
                    )


                # ------------------------------------------------
                # Stats
                # ------------------------------------------------

                h_stats = match[
                    "h_stats"
                ]

                a_stats = match[
                    "a_stats"
                ]


                st.markdown(
                    "### 📈 L5 Statistics"
                )


                stats_col1, stats_col2 = st.columns(
                    2
                )


                with stats_col1:

                    st.markdown(
                        f"""
                        **🏠 {match['home']} — HOME L5**

                        - O2.5: **{h_stats.get('over_pct', '—')}%**
                        - U2.5: **{h_stats.get('under_pct', '—')}%**
                        - BTTS: **{h_stats.get('btts_pct', '—')}%**
                        - GF: **{h_stats.get('gf_avg', '—')}**
                        - GA: **{h_stats.get('ga_avg', '—')}**
                        """
                    )


                with stats_col2:

                    st.markdown(
                        f"""
                        **✈️ {match['away']} — AWAY L5**

                        - O2.5: **{a_stats.get('over_pct', '—')}%**
                        - U2.5: **{a_stats.get('under_pct', '—')}%**
                        - BTTS: **{a_stats.get('btts_pct', '—')}%**
                        - GF: **{a_stats.get('gf_avg', '—')}**
                        - GA: **{a_stats.get('ga_avg', '—')}**
                        """
                    )


                # ------------------------------------------------
                # OVER CHECKS
                # ------------------------------------------------

                if match[
                    "over_checks"
                ]:

                    with st.expander(
                        "OVER 2.5 Confirmation"
                    ):

                        checks = match[
                            "over_checks"
                        ]


                        for key, value in checks.items():

                            if value:

                                st.write(
                                    f"✅ {key}"
                                )

                            else:

                                st.write(
                                    f"❌ {key}"
                                )


                # ------------------------------------------------
                # UNDER CHECKS
                # ------------------------------------------------

                if match[
                    "under_checks"
                ]:

                    with st.expander(
                        "UNDER 2.5 Confirmation"
                    ):

                        checks = match[
                            "under_checks"
                        ]


                        for key, value in checks.items():

                            if value:

                                st.write(
                                    f"✅ {key}"
                                )

                            else:

                                st.write(
                                    f"❌ {key}"
                                )


                # ------------------------------------------------
                # Scorelines
                # ------------------------------------------------

                with st.expander(
                    "View L5 Scorelines"
                ):

                    h_scorelines = (
                        h_stats.get(
                            "scorelines",
                            [],
                        )
                    )

                    a_scorelines = (
                        a_stats.get(
                            "scorelines",
                            [],
                        )
                    )


                    st.markdown(
                        "#### 🏠 Home L5"
                    )

                    if h_scorelines:

                        st.dataframe(
                            h_scorelines,
                            use_container_width=True,
                            hide_index=True,
                        )

                    else:

                        st.write(
                            "No data."
                        )


                    st.markdown(
                        "#### ✈️ Away L5"
                    )

                    if a_scorelines:

                        st.dataframe(
                            a_scorelines,
                            use_container_width=True,
                            hide_index=True,
                        )

                    else:

                        st.write(
                            "No data."
                        )


                # ------------------------------------------------
                # Data warning
                # ------------------------------------------------

                st.warning(
                    (
                        "⚠️ History data is "
                        "2024 season proxy. "
                        "It is NOT current 2026 form."
                    )
                )


        # ----------------------------------------------------
        # Save JSON
        # ----------------------------------------------------

        output = {

            "updated_at": now_mmt.strftime(
                "%Y-%m-%d %H:%M MMT"
            ),

            "window_start": (
                window_start.strftime(
                    "%Y-%m-%d %H:%M MMT"
                )
            ),

            "window_end": (
                window_end.strftime(
                    "%Y-%m-%d %H:%M MMT"
                )
            ),

            "mode": (
                "MULTI_LEAGUE_PREMATCH"
            ),

            "league_filter": [
                LEAGUES[
                    league_id
                ]
                for league_id
                in selected_league_ids
                if league_id in LEAGUES
            ],

            "history_season": (
                HISTORY_SEASON
            ),

            "history_data_type": (
                "2024 historical proxy"
            ),

            "xg_used": False,

            "model_rules": {

                "over": {

                    "home_o25_min": 60,

                    "away_o25_min": 60,

                    "home_gf_min": 1.5,

                    "home_ga_min": 1.0,

                    "away_gf_min": 1.0,

                    "away_ga_min": 1.0,

                    "home_btts_min": 60,

                    "away_btts_min": 60,

                    "edge_min": 5,
                },

                "under": {

                    "home_u25_min": 60,

                    "away_u25_min": 60,

                    "home_gf_max": 1.3,

                    "home_ga_max": 1.0,

                    "away_gf_max": 1.1,

                    "away_ga_max": 1.2,

                    "home_btts_max": 50,

                    "away_btts_max": 50,

                    "edge_min": 5,
                },
            },

            "api_calls": (
                st.session_state.api_calls
            ),

            "remaining_quota": (
                st.session_state.remaining_quota
            ),

            "matches": (
                evaluated_matches
            ),
        }


        try:

            with open(
                OUTPUT_FILE,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    output,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

        except Exception:

            pass


# ============================================================
# API SAFETY STATUS
# ============================================================

st.divider()

st.header(
    "🛡️ API SAFETY STATUS"
)


s1, s2, s3 = st.columns(
    3
)


with s1:

    st.metric(
        "API Calls",
        str(
            st.session_state.api_calls
        ),
    )


with s2:

    quota = (
        st.session_state.remaining_quota
    )

    st.metric(
        "Remaining Quota",
        (
            str(quota)
            if quota is not None
            else "—"
        ),
    )


with s3:

    st.metric(
        "Hard Limit",
        str(
            MAX_API_CALLS_PER_RUN
        ),
    )


if st.session_state.stop_reason:

    st.warning(
        "⚠️ "
        + st.session_state.stop_reason
    )


# ============================================================
# FINAL INFORMATION
# ============================================================

st.divider()

st.caption(
    (
        "Data source: API-SPORTS / API-FOOTBALL. "
        "Historical team statistics use the configured "
        f"{HISTORY_SEASON} season proxy. "
        "xG is intentionally NOT used because the current "
        "API plan does not provide the required xG data."
    )
)

st.caption(
    (
        "Search window is always calculated in Myanmar Time "
        "(Asia/Yangon): 12:00 PM → next day 12:00 PM."
    )
)

st.caption(
    (
        "OVER 2.5 requires BOTH Home and Away BTTS ≥ 60%. "
        "A team with BTTS 40%, for example, cannot pass "
        "the OVER 2.5 confirmation."
    )
)
