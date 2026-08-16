from datetime import datetime, timedelta, timezone
import math
import re
import time
import requests
import streamlit as st


# ============================================================
# 0. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Pre-Match Over/Under Intelligence Pro",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 1. CONFIGURATION
# ============================================================

MMT_TIMEZONE = timezone(timedelta(hours=6, minutes=30))

# -----------------------------
# Main model thresholds
# -----------------------------

MIN_MODEL_PROBABILITY = 60.0
MIN_MODEL_EDGE = 5.0

# Over 2.5 base criteria
OVER_L5_MIN = 60.0
OVER_HOME_GF_MIN = 1.5
OVER_HOME_GA_MIN = 1.0
OVER_AWAY_GF_MIN = 1.0
OVER_AWAY_GA_MIN = 1.0
OVER_BTTS_MIN = 60.0

# Under 2.5 base criteria
UNDER_L5_MIN = 60.0
UNDER_HOME_GF_MAX = 1.3
UNDER_HOME_GA_MAX = 1.0
UNDER_AWAY_GF_MAX = 1.1
UNDER_AWAY_GA_MAX = 1.2
UNDER_BTTS_MAX = 50.0

# -----------------------------
# History settings
# -----------------------------

EXACT_L5_REQUIRED = 5

# First attempt:
# API-Football supports team=...&last=...
# We intentionally request more than 5 because we need
# to separate Home and Away and then take the exact latest 5.
INITIAL_LAST_FIXTURES = 20

# Fallback date-range search if exact 5 cannot be found
HISTORY_LOOKBACK_DAYS = 450
MAX_HISTORY_PAGES = 8

# -----------------------------
# Odds settings
# -----------------------------

ODDS_BET_NAME = "Goals Over/Under"
TARGET_GOAL_LINE = 2.5

# For Model Edge we use the BEST available valid bookmaker price.
# This is actionable, but can be more optimistic than market-average odds.
ODDS_MODE = "BEST"

# Minimum sensible decimal odds
MIN_VALID_ODDS = 1.01
MAX_VALID_ODDS = 100.0

# -----------------------------
# Cache TTL
# -----------------------------

FIXTURE_CACHE_TTL = 3600          # 1 hour
HISTORY_CACHE_TTL = 21600         # 6 hours
ODDS_CACHE_TTL = 1800             # 30 minutes


# ============================================================
# 2. DARK CYBER SPORTS THEME
# ============================================================

st.markdown(
    """
<style>
    .stApp {
        background-color: #0b0e14;
        color: #e6edf3;
    }

    .hero-card {
        background: linear-gradient(135deg, #131b26 0%, #1c2636 100%);
        border: 1px solid #00f2fe44;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 242, 254, 0.10);
    }

    .match-box {
        background-color: #121824;
        border: 1px solid #222d3d;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }

    .league-badge {
        background-color: #1f293d;
        color: #00f2fe;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 13px;
        display: inline-block;
    }

    .badge-win {
        background-color: #00e676;
        color: #042410;
        padding: 5px 10px;
        border-radius: 6px;
        font-weight: 900;
        font-size: 13px;
    }

    .badge-loss {
        background-color: #ff1744;
        color: #ffffff;
        padding: 5px 10px;
        border-radius: 6px;
        font-weight: 900;
        font-size: 13px;
    }

    .badge-over {
        background-color: #00e676;
        color: #042410;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 900;
    }

    .badge-under {
        background-color: #ff1744;
        color: #ffffff;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 900;
    }

    .badge-neutral {
        background-color: #45515f;
        color: #ffffff;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 800;
    }

    .badge-star {
        color: #ffd600;
        font-size: 20px;
        letter-spacing: 2px;
    }

    .stat-box {
        background-color: #172030;
        border: 1px solid #293850;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        min-height: 78px;
    }

    .metric-pass {
        color: #00e676;
        font-weight: 900;
    }

    .metric-fail {
        color: #ff5252;
        font-weight: 900;
    }

    .score-row {
        background-color: #172030;
        border-bottom: 1px solid #293850;
        border-radius: 5px;
        padding: 7px 10px;
        margin-bottom: 4px;
    }

    .small-muted {
        color: #8b949e;
        font-size: 12px;
    }

    .edge-positive {
        color: #00e676;
        font-weight: 900;
        font-size: 20px;
    }

    .edge-negative {
        color: #ff5252;
        font-weight: 900;
        font-size: 20px;
    }

    .model-box {
        background-color: #101722;
        border: 1px solid #30415a;
        border-radius: 10px;
        padding: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 3. API KEY LOADING
# ============================================================

raw_keys = st.secrets.get("API_KEY", "")

API_KEYS = [
    k.strip().replace('"', "").replace("'", "")
    for k in raw_keys.replace("\n", ",").split(",")
    if k.strip()
]

if not API_KEYS:
    st.error(
        "⚠️ API Key မတွေ့ရှိပါ။ Streamlit Secrets ထဲတွင် API_KEY ထည့်ပေးပါ။"
    )
    st.stop()


# ============================================================
# 4. API REQUEST ENGINE
# ============================================================

BASE_URL = "https://v3.football.api-sports.io"


def _is_rate_limit_error(errors):
    text = str(errors).lower()
    return (
        "ratelimit" in text
        or "rate limit" in text
        or "too many requests" in text
        or "requests limit" in text
    )


@st.cache_data(
    ttl=FIXTURE_CACHE_TTL,
    show_spinner=False,
)
def fetch_api_cached(endpoint, cache_bucket="default"):
    """
    Generic API-Football GET request with API-key rotation.

    cache_bucket is intentionally included so different TTL groups
    can use different wrapper functions if needed.
    """
    last_error = "Unknown API error"

    for idx, key in enumerate(API_KEYS):

        for attempt in range(2):

            try:
                url = f"{BASE_URL}/{endpoint}"

                headers = {
                    "x-apisports-key": key,
                    "Accept": "application/json",
                }

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=15,
                )

                if response.status_code == 429:
                    last_error = (
                        f"Key #{idx + 1}: HTTP 429 Rate Limit"
                    )
                    time.sleep(3)
                    continue

                if response.status_code >= 500:
                    last_error = (
                        f"Key #{idx + 1}: HTTP {response.status_code}"
                    )
                    time.sleep(1)
                    continue

                data = response.json()

                errors = data.get("errors", [])

                if errors:
                    last_error = (
                        f"Key #{idx + 1}: {errors}"
                    )

                    if _is_rate_limit_error(errors):
                        time.sleep(3)
                        continue

                    # Non-rate-limit API error:
                    # move to next key.
                    break

                if "response" in data:
                    return (
                        data["response"],
                        f"Key #{idx + 1} (Active)",
                    )

                last_error = (
                    f"Key #{idx + 1}: No Response Body"
                )

            except Exception as exc:
                last_error = (
                    f"Key #{idx + 1}: {type(exc).__name__}"
                )
                time.sleep(1)

    return [], last_error


@st.cache_data(
    ttl=HISTORY_CACHE_TTL,
    show_spinner=False,
)
def fetch_team_last_fixtures(team_id):
    """
    Fast path for upcoming fixtures.

    Request more than 5 recent results, then filter by venue.
    """
    endpoint = (
        f"fixtures?team={team_id}"
        f"&last={INITIAL_LAST_FIXTURES}"
        f"&status=FT-AET-PEN"
    )

    return fetch_api_cached(
        endpoint,
        cache_bucket="history",
    )


@st.cache_data(
    ttl=HISTORY_CACHE_TTL,
    show_spinner=False,
)
def fetch_team_history_range(
    team_id,
    from_date,
    to_date,
    page,
):
    """
    Fallback for exact historical L5.

    This is especially important when scanning a past date,
    because the normal last=20 request could otherwise include
    matches that happened AFTER the target fixture.
    """
    endpoint = (
        f"fixtures?team={team_id}"
        f"&from={from_date}"
        f"&to={to_date}"
        f"&status=FT-AET-PEN"
        f"&page={page}"
    )

    return fetch_api_cached(
        endpoint,
        cache_bucket="history_range",
    )


@st.cache_data(
    ttl=ODDS_CACHE_TTL,
    show_spinner=False,
)
def fetch_fixture_odds(fixture_id):
    """
    Pre-match odds for one fixture.

    API-Football's odds endpoint is:
        /odds?fixture=FIXTURE_ID
    """
    endpoint = f"odds?fixture={fixture_id}"

    return fetch_api_cached(
        endpoint,
        cache_bucket="odds",
    )


# ============================================================
# 5. TIME HELPERS
# ============================================================

def convert_to_mmt(iso_time_str):
    try:
        utc_dt = datetime.fromisoformat(
            iso_time_str.replace("Z", "+00:00")
        )

        return utc_dt.astimezone(
            MMT_TIMEZONE
        ).strftime("%I:%M %p")

    except Exception:
        return iso_time_str[11:16]


def fixture_timestamp(fixture):
    """
    Get reliable UTC timestamp from fixture.
    """
    ts = fixture.get("fixture", {}).get("timestamp")

    if ts is not None:
        try:
            return int(ts)
        except Exception:
            pass

    date_str = fixture.get("fixture", {}).get("date")

    if date_str:
        try:
            dt = datetime.fromisoformat(
                date_str.replace("Z", "+00:00")
            )
            return int(dt.timestamp())
        except Exception:
            pass

    return None


def is_completed_status(status_short):
    return status_short in {
        "FT",
        "AET",
        "PEN",
    }


# ============================================================
# 6. STRICT LEAGUE WHITELIST
# ============================================================

ALLOWED_CONFIG = {
    "england": [
        "premier league",
        "championship",
    ],
    "spain": [
        "la liga",
        "segunda division",
        "laliga 2",
    ],
    "france": [
        "ligue 1",
        "ligue 2",
    ],
    "germany": [
        "bundesliga",
        "2. bundesliga",
    ],
    "italy": [
        "serie a",
        "serie b",
    ],
    "argentina": [
        "liga profesional",
        "primera division",
    ],
    "australia": [
        "a-league",
    ],
    "austria": [
        "bundesliga",
    ],
    "belgium": [
        "pro league",
        "first division a",
    ],
    "brazil": [
        "serie a",
    ],
    "chile": [
        "primera division",
    ],
    "china": [
        "super league",
    ],
    "colombia": [
        "primera a",
    ],
    "croatia": [
        "hnl",
        "1. hnl",
    ],
    "denmark": [
        "superliga",
    ],
    "ecuador": [
        "liga pro",
    ],
    "greece": [
        "super league",
    ],
    "japan": [
        "j1 league",
    ],
    "mexico": [
        "liga mx",
    ],
    "netherlands": [
        "eredivisie",
    ],
    "norway": [
        "eliteserien",
    ],
    "peru": [
        "liga 1",
    ],
    "poland": [
        "ekstraklasa",
    ],
    "portugal": [
        "primeira liga",
        "liga portugal",
    ],
    "saudi arabia": [
        "saudi pro league",
        "pro league",
    ],
    "scotland": [
        "premiership",
        "scottish premiership",
    ],
    "sweden": [
        "allsvenskan",
    ],
    "switzerland": [
        "super league",
    ],
    "turkey": [
        "super lig",
        "süper lig",
    ],
    "usa": [
        "major league soccer",
    ],
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


def is_allowed_league(
    league_name,
    country_name,
    home_name,
    away_name,
):
    combined = (
        f"{league_name} "
        f"{country_name} "
        f"{home_name} "
        f"{away_name}"
    ).lower()

    if any(
        word in combined
        for word in BLACKLIST_WORDS
    ):
        return False

    if re.search(
        r"\b(ii|iii|b|c|u\s?-?\d{2})\b",
        home_name.lower(),
    ):
        return False

    if re.search(
        r"\b(ii|iii|b|c|u\s?-?\d{2})\b",
        away_name.lower(),
    ):
        return False

    l_low = league_name.lower()
    c_low = (
        country_name.lower()
        if country_name
        else ""
    )

    if (
        "major league soccer" in l_low
        or l_low == "mls"
    ):
        return True

    for c_key, valid_leagues in ALLOWED_CONFIG.items():

        if (
            c_key in c_low
            or c_key in l_low
        ):
            if any(
                valid_league in l_low
                for valid_league in valid_leagues
            ):
                return True

    for world_league in ALLOWED_CONFIG["world"]:
        if world_league in l_low:
            return True

    return False


# ============================================================
# 7. EXACT LAST 5 HOME / LAST 5 AWAY ENGINE
# ============================================================

def sort_fixtures_newest_first(fixtures):
    return sorted(
        fixtures,
        key=lambda f: fixture_timestamp(f) or 0,
        reverse=True,
    )


def extract_exact_l5(
    fixtures,
    team_id,
    is_home,
    cutoff_timestamp,
):
    """
    Take ONLY completed matches BEFORE the target fixture kickoff.

    If is_home=True:
        team must be home.

    If is_home=False:
        team must be away.

    This is the important part that prevents future-data leakage.
    """

    selected = []

    for fixture in sort_fixtures_newest_first(fixtures):

        status = (
            fixture
            .get("fixture", {})
            .get("status", {})
            .get("short")
        )

        if not is_completed_status(status):
            continue

        ts = fixture_timestamp(fixture)

        if ts is None:
            continue

        # Must happen BEFORE target match
        if cutoff_timestamp is not None:
            if ts >= cutoff_timestamp:
                continue

        home_id = (
            fixture
            .get("teams", {})
            .get("home", {})
            .get("id")
        )

        away_id = (
            fixture
            .get("teams", {})
            .get("away", {})
            .get("id")
        )

        if is_home and home_id == team_id:
            selected.append(fixture)

        elif (not is_home) and away_id == team_id:
            selected.append(fixture)

        if len(selected) == EXACT_L5_REQUIRED:
            break

    return selected


def get_exact_l5_matches(
    team_id,
    is_home,
    cutoff_timestamp,
):
    """
    Get the exact latest 5 Home or Away matches
    before the target fixture.

    Fast path:
        team + last=20

    Fallback:
        date-range + pagination
    """

    # --------------------------------------------------------
    # FAST PATH
    # --------------------------------------------------------

    fixtures, status = fetch_team_last_fixtures(
        team_id
    )

    if fixtures:
        selected = extract_exact_l5(
            fixtures=fixtures,
            team_id=team_id,
            is_home=is_home,
            cutoff_timestamp=cutoff_timestamp,
        )

        if len(selected) == EXACT_L5_REQUIRED:
            return selected, status

    # --------------------------------------------------------
    # FALLBACK FOR TRUE HISTORICAL EXACT L5
    # --------------------------------------------------------

    if cutoff_timestamp is None:
        return [], status

    cutoff_dt = datetime.fromtimestamp(
        cutoff_timestamp,
        tz=timezone.utc,
    )

    from_dt = cutoff_dt - timedelta(
        days=HISTORY_LOOKBACK_DAYS
    )

    from_date = from_dt.strftime("%Y-%m-%d")
    to_date = cutoff_dt.strftime("%Y-%m-%d")

    all_history = []

    for page in range(
        1,
        MAX_HISTORY_PAGES + 1,
    ):
        page_data, page_status = (
            fetch_team_history_range(
                team_id=team_id,
                from_date=from_date,
                to_date=to_date,
                page=page,
            )
        )

        if page_data:
            all_history.extend(page_data)

        if not page_data:
            break

        # If we already have enough raw data,
        # test whether exact L5 is available.
        selected = extract_exact_l5(
            fixtures=all_history,
            team_id=team_id,
            is_home=is_home,
            cutoff_timestamp=cutoff_timestamp,
        )

        if len(selected) == EXACT_L5_REQUIRED:
            return selected, page_status

    selected = extract_exact_l5(
        fixtures=all_history,
        team_id=team_id,
        is_home=is_home,
        cutoff_timestamp=cutoff_timestamp,
    )

    return selected, status


# ============================================================
# 8. L5 STATISTICS
# ============================================================

def calculate_l5_metrics(
    matches,
    team_id,
    is_home,
):
    if len(matches) != EXACT_L5_REQUIRED:
        return None

    over_count = 0
    under_count = 0
    btts_count = 0

    gf_total = 0
    ga_total = 0

    scorelines = []

    for match in matches:

        home_id = (
            match["teams"]["home"]["id"]
        )

        away_id = (
            match["teams"]["away"]["id"]
        )

        home_name = (
            match["teams"]["home"]["name"]
        )

        away_name = (
            match["teams"]["away"]["name"]
        )

        goals_home = match["goals"]["home"]
        goals_away = match["goals"]["away"]

        if goals_home is None:
            return None

        if goals_away is None:
            return None

        total_goals = (
            goals_home + goals_away
        )

        if total_goals >= 3:
            over_count += 1
        else:
            under_count += 1

        if (
            goals_home > 0
            and goals_away > 0
        ):
            btts_count += 1

        if is_home:
            gf = goals_home
            ga = goals_away
        else:
            gf = goals_away
            ga = goals_home

        gf_total += gf
        ga_total += ga

        result_side = (
            "OVER"
            if total_goals >= 3
            else "UNDER"
        )

        btts_side = (
            "BTTS"
            if goals_home > 0
            and goals_away > 0
            else "NO BTTS"
        )

        scorelines.append(
            {
                "date": (
                    match["fixture"]["date"]
                ),
                "home": home_name,
                "away": away_name,
                "home_goals": goals_home,
                "away_goals": goals_away,
                "total_goals": total_goals,
                "line_result": result_side,
                "btts": btts_side,
            }
        )

    sample = len(matches)

    return {
        "over_pct": round(
            over_count / sample * 100,
            1,
        ),
        "under_pct": round(
            under_count / sample * 100,
            1,
        ),
        "btts_pct": round(
            btts_count / sample * 100,
            1,
        ),
        "gf_avg": round(
            gf_total / sample,
            2,
        ),
        "ga_avg": round(
            ga_total / sample,
            2,
        ),
        "sample": sample,
        "over_count": over_count,
        "under_count": under_count,
        "btts_count": btts_count,
        "scorelines": scorelines,
    }


# ============================================================
# 9. POISSON MODEL
# ============================================================

def poisson_probability_exactly(
    goals,
    expected_goals,
):
    """
    P(X = goals) for Poisson distribution.
    """
    if expected_goals < 0:
        return 0.0

    return (
        math.exp(-expected_goals)
        * expected_goals ** goals
        / math.factorial(goals)
    )


def poisson_over_2_5_probability(
    expected_total_goals,
):
    """
    P(total goals >= 3)

    = 1 - P(0) - P(1) - P(2)
    """

    p0 = poisson_probability_exactly(
        0,
        expected_total_goals,
    )

    p1 = poisson_probability_exactly(
        1,
        expected_total_goals,
    )

    p2 = poisson_probability_exactly(
        2,
        expected_total_goals,
    )

    probability = (
        1.0 - p0 - p1 - p2
    )

    return max(
        0.0,
        min(1.0, probability),
    )


def build_model_probability(
    home_stats,
    away_stats,
):
    """
    xG မသုံးပါ။

    We estimate expected goals from L5:
        Home expected goals =
            average(Home L5 GF, Away L5 GA)

        Away expected goals =
            average(Away L5 GF, Home L5 GA)

    Then use a Poisson total-goals model.

    This is a transparent model estimate,
    NOT a calibrated historical probability yet.
    """

    home_expected_goals = (
        home_stats["gf_avg"]
        + away_stats["ga_avg"]
    ) / 2.0

    away_expected_goals = (
        away_stats["gf_avg"]
        + home_stats["ga_avg"]
    ) / 2.0

    total_expected_goals = (
        home_expected_goals
        + away_expected_goals
    )

    over_probability = (
        poisson_over_2_5_probability(
            total_expected_goals
        )
    )

    under_probability = (
        1.0 - over_probability
    )

    return {
        "home_expected_goals": round(
            home_expected_goals,
            3,
        ),
        "away_expected_goals": round(
            away_expected_goals,
            3,
        ),
        "total_expected_goals": round(
            total_expected_goals,
            3,
        ),
        "over_probability": round(
            over_probability * 100,
            2,
        ),
        "under_probability": round(
            under_probability * 100,
            2,
        ),
    }


# ============================================================
# 10. BASE CRITERIA
# ============================================================

def evaluate_over_base(
    home_stats,
    away_stats,
):
    checks = {
        "Home L5 O2.5 >= 60%":
            home_stats["over_pct"]
            >= OVER_L5_MIN,

        "Away L5 O2.5 >= 60%":
            away_stats["over_pct"]
            >= OVER_L5_MIN,

        "Home GF > 1.5":
            home_stats["gf_avg"]
            > OVER_HOME_GF_MIN,

        "Home GA > 1.0":
            home_stats["ga_avg"]
            > OVER_HOME_GA_MIN,

        "Away GF > 1.0":
            away_stats["gf_avg"]
            > OVER_AWAY_GF_MIN,

        "Away GA > 1.0":
            away_stats["ga_avg"]
            > OVER_AWAY_GA_MIN,

        "Home BTTS >= 60%":
            home_stats["btts_pct"]
            >= OVER_BTTS_MIN,

        "Away BTTS >= 60%":
            away_stats["btts_pct"]
            >= OVER_BTTS_MIN,
    }

    return (
        all(checks.values()),
        checks,
    )


def evaluate_under_base(
    home_stats,
    away_stats,
):
    checks = {
        "Home L5 U2.5 >= 60%":
            home_stats["under_pct"]
            >= UNDER_L5_MIN,

        "Away L5 U2.5 >= 60%":
            away_stats["under_pct"]
            >= UNDER_L5_MIN,

        "Home GF < 1.3":
            home_stats["gf_avg"]
            < UNDER_HOME_GF_MAX,

        "Home GA < 1.0":
            home_stats["ga_avg"]
            < UNDER_HOME_GA_MAX,

        "Away GF < 1.1":
            away_stats["gf_avg"]
            < UNDER_AWAY_GF_MAX,

        "Away GA < 1.2":
            away_stats["ga_avg"]
            < UNDER_AWAY_GA_MAX,

        "Home BTTS <= 50%":
            home_stats["btts_pct"]
            <= UNDER_BTTS_MAX,

        "Away BTTS <= 50%":
            away_stats["btts_pct"]
            <= UNDER_BTTS_MAX,
    }

    return (
        all(checks.values()),
        checks,
    )


# ============================================================
# 11. ODDS PARSER
# ============================================================

def safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def extract_over_under_2_5_odds(
    odds_response,
    target_side,
):
    """
    Parse API-Football pre-match odds.

    Expected market:
        Goals Over/Under

    Target:
        Over 2.5
        or
        Under 2.5

    Returns the best valid bookmaker price.
    """

    candidates = []

    for response_item in odds_response:

        bookmakers = response_item.get(
            "bookmakers",
            [],
        )

        for bookmaker in bookmakers:

            bookmaker_id = bookmaker.get(
                "id"
            )

            bookmaker_name = bookmaker.get(
                "name",
                "Unknown",
            )

            bets = bookmaker.get(
                "bets",
                [],
            )

            for bet in bets:

                bet_name = str(
                    bet.get("name", "")
                ).strip().lower()

                # Main pre-match market
                if (
                    bet_name
                    != ODDS_BET_NAME.lower()
                ):
                    continue

                values = bet.get(
                    "values",
                    [],
                )

                for value_item in values:

                    value_name = str(
                        value_item.get(
                            "value",
                            "",
                        )
                    ).strip()

                    handicap = str(
                        value_item.get(
                            "handicap",
                            "",
                        )
                    ).strip()

                    odd = safe_float(
                        value_item.get("odd")
                    )

                    if odd is None:
                        continue

                    if (
                        odd < MIN_VALID_ODDS
                        or odd > MAX_VALID_ODDS
                    ):
                        continue

                    normalized = (
                        value_name.lower()
                    )

                    target_name = (
                        f"{target_side} 2.5"
                        .lower()
                    )

                    # Typical API structure:
                    # value = "Over"
                    # handicap = "2.5"
                    #
                    # Some feeds may instead return:
                    # value = "Over 2.5"
                    #
                    # Accept both.

                    exact_match = (
                        normalized
                        == target_name
                        and (
                            handicap == "2.5"
                            or handicap == "2,5"
                            or handicap == ""
                        )
                    )

                    combined_match = (
                        normalized
                        == target_name
                    )

                    if not (
                        exact_match
                        or combined_match
                    ):
                        continue

                    candidates.append(
                        {
                            "bookmaker_id":
                                bookmaker_id,
                            "bookmaker":
                                bookmaker_name,
                            "odds": odd,
                            "market":
                                bet.get(
                                    "name",
                                    "",
                                ),
                            "value":
                                value_name,
                            "handicap":
                                handicap,
                        }
                    )

    if not candidates:
        return None

    # Best available price.
    # Higher odds = better price for the bettor.
    candidates.sort(
        key=lambda x: x["odds"],
        reverse=True,
    )

    best = candidates[0]

    best["num_bookmakers"] = len(
        candidates
    )

    return best


# ============================================================
# 12. MODEL EDGE
# ============================================================

def calculate_market_implied_probability(
    decimal_odds,
):
    if not decimal_odds or decimal_odds <= 1:
        return None

    return (
        1.0 / decimal_odds
    ) * 100.0


def calculate_model_edge(
    model_probability,
    decimal_odds,
):
    """
    Edge = Model Probability - Market Implied Probability

    Example:
        Model = 62%
        Odds = 1.80

        Market implied =
            1 / 1.80 = 55.56%

        Edge =
            62 - 55.56 = +6.44 percentage points
    """

    market_probability = (
        calculate_market_implied_probability(
            decimal_odds
        )
    )

    if market_probability is None:
        return None, None

    edge = (
        model_probability
        - market_probability
    )

    return (
        round(market_probability, 2),
        round(edge, 2),
    )


# ============================================================
# 13. COMPLETE FIXTURE EVALUATION
# ============================================================

def evaluate_fixture(
    fixture,
    fetch_odds=True,
):
    fixture_id = fixture["fixture"]["id"]

    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]

    home_name = fixture["teams"]["home"]["name"]
    away_name = fixture["teams"]["away"]["name"]

    cutoff_timestamp = fixture_timestamp(
        fixture
    )

    if cutoff_timestamp is None:
        return {
            "status": "NO_FIXTURE_TIME",
            "reason": "Fixture timestamp unavailable.",
        }

    # --------------------------------------------------------
    # Exact L5
    # --------------------------------------------------------

    home_l5, home_status = get_exact_l5_matches(
        team_id=home_id,
        is_home=True,
        cutoff_timestamp=cutoff_timestamp,
    )

    away_l5, away_status = get_exact_l5_matches(
        team_id=away_id,
        is_home=False,
        cutoff_timestamp=cutoff_timestamp,
    )

    # --------------------------------------------------------
    # EXACT 5 REQUIRED
    # --------------------------------------------------------

    if len(home_l5) != EXACT_L5_REQUIRED:
        return {
            "status": "INSUFFICIENT_DATA",
            "reason": (
                f"Home exact L5 unavailable "
                f"({len(home_l5)}/5)."
            ),
            "home_l5_count": len(home_l5),
            "away_l5_count": len(away_l5),
            "home_status": home_status,
            "away_status": away_status,
        }

    if len(away_l5) != EXACT_L5_REQUIRED:
        return {
            "status": "INSUFFICIENT_DATA",
            "reason": (
                f"Away exact L5 unavailable "
                f"({len(away_l5)}/5)."
            ),
            "home_l5_count": len(home_l5),
            "away_l5_count": len(away_l5),
            "home_status": home_status,
            "away_status": away_status,
        }

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    home_stats = calculate_l5_metrics(
        matches=home_l5,
        team_id=home_id,
        is_home=True,
    )

    away_stats = calculate_l5_metrics(
        matches=away_l5,
        team_id=away_id,
        is_home=False,
    )

    if not home_stats or not away_stats:
        return {
            "status": "INVALID_L5_DATA",
            "reason": "Could not calculate exact L5 metrics.",
        }

    # --------------------------------------------------------
    # Base criteria
    # --------------------------------------------------------

    over_base_pass, over_checks = (
        evaluate_over_base(
            home_stats,
            away_stats,
        )
    )

    under_base_pass, under_checks = (
        evaluate_under_base(
            home_stats,
            away_stats,
        )
    )

    # --------------------------------------------------------
    # Model probability
    # --------------------------------------------------------

    model = build_model_probability(
        home_stats,
        away_stats,
    )

    # --------------------------------------------------------
    # Determine candidate side before odds
    #
    # Only one side should normally be considered.
    # If both somehow pass, choose the side with stronger
    # model probability.
    # --------------------------------------------------------

    candidate_side = None

    if (
        over_base_pass
        and model["over_probability"]
        >= MIN_MODEL_PROBABILITY
    ):
        candidate_side = "OVER_2_5"

    if (
        under_base_pass
        and model["under_probability"]
        >= MIN_MODEL_PROBABILITY
    ):
        if candidate_side is None:
            candidate_side = "UNDER_2_5"
        else:
            # Keep the stronger probability
            if (
                model["under_probability"]
                > model["over_probability"]
            ):
                candidate_side = "UNDER_2_5"

    # --------------------------------------------------------
    # No candidate = no odds call
    # --------------------------------------------------------

    if candidate_side is None:
        return {
            "status": "NEUTRAL",
            "home_stats": home_stats,
            "away_stats": away_stats,
            "model": model,
            "over_base_pass": over_base_pass,
            "under_base_pass": under_base_pass,
            "over_checks": over_checks,
            "under_checks": under_checks,
            "candidate_side": None,
            "fixture_id": fixture_id,
            "home_l5": home_l5,
            "away_l5": away_l5,
        }

    # --------------------------------------------------------
    # Odds
    # --------------------------------------------------------

    odds_info = None

    if fetch_odds:
        odds_response, odds_status = (
            fetch_fixture_odds(
                fixture_id
            )
        )

        if candidate_side == "OVER_2_5":
            odds_info = (
                extract_over_under_2_5_odds(
                    odds_response,
                    "Over",
                )
            )

        else:
            odds_info = (
                extract_over_under_2_5_odds(
                    odds_response,
                    "Under",
                )
            )
    else:
        odds_status = "Odds skipped"

    # --------------------------------------------------------
    # Model probability for selected side
    # --------------------------------------------------------

    if candidate_side == "OVER_2_5":
        model_probability = (
            model["over_probability"]
        )
    else:
        model_probability = (
            model["under_probability"]
        )

    # --------------------------------------------------------
    # If odds unavailable:
    # No real market edge.
    # Therefore NOT 5-star.
    # --------------------------------------------------------

    if not odds_info:
        return {
            "status": "ODDS_UNAVAILABLE",
            "home_stats": home_stats,
            "away_stats": away_stats,
            "model": model,
            "over_base_pass": over_base_pass,
            "under_base_pass": under_base_pass,
            "over_checks": over_checks,
            "under_checks": under_checks,
            "candidate_side": candidate_side,
            "model_probability": model_probability,
            "odds": None,
            "market_probability": None,
            "model_edge": None,
            "star5": False,
            "fixture_id": fixture_id,
            "home_l5": home_l5,
            "away_l5": away_l5,
            "odds_status": odds_status,
        }

    # --------------------------------------------------------
    # Real Model Edge
    # --------------------------------------------------------

    market_probability, model_edge = (
        calculate_model_edge(
            model_probability,
            odds_info["odds"],
        )
    )

    # --------------------------------------------------------
    # FINAL 5-STAR QUALIFICATION
    #
    # Base criteria
    # + Model probability >= 60
    # + Model edge >= 5
    # --------------------------------------------------------

    if candidate_side == "OVER_2_5":
        base_pass = over_base_pass
    else:
        base_pass = under_base_pass

    star5 = (
        base_pass
        and model_probability
        >= MIN_MODEL_PROBABILITY
        and model_edge is not None
        and model_edge
        >= MIN_MODEL_EDGE
    )

    status = (
        "STAR_5"
        if star5
        else "MODEL_PASS_EDGE_FAIL"
    )

    return {
        "status": status,
        "home_stats": home_stats,
        "away_stats": away_stats,
        "model": model,
        "over_base_pass": over_base_pass,
        "under_base_pass": under_base_pass,
        "over_checks": over_checks,
        "under_checks": under_checks,
        "candidate_side": candidate_side,
        "model_probability": model_probability,
        "odds": odds_info,
        "market_probability": market_probability,
        "model_edge": model_edge,
        "star5": star5,
        "fixture_id": fixture_id,
        "home_l5": home_l5,
        "away_l5": away_l5,
        "odds_status": odds_status,
    }


# ============================================================
# 14. UI HELPERS
# ============================================================

def metric_html(
    title,
    value,
    passed,
    subtitle="",
):
    status_icon = "✅" if passed else "❌"

    status_class = (
        "metric-pass"
        if passed
        else "metric-fail"
    )

    return f"""
    <div class="stat-box">
        <span style="font-size:11px;color:#8b949e;">
            {title}
        </span>
        <br>
        <b>{value}</b>
        <br>
        <span class="{status_class}">
            {status_icon}
        </span>
        <span class="small-muted">
            {subtitle}
        </span>
    </div>
    """


def format_scoreline_date(date_str):
    try:
        dt = datetime.fromisoformat(
            date_str.replace("Z", "+00:00")
        )

        return dt.astimezone(
            MMT_TIMEZONE
        ).strftime("%d %b %Y")

    except Exception:
        return date_str[:10]


def render_scorelines(
    title,
    matches,
):
    st.markdown(
        f"##### {title}"
    )

    for idx, item in enumerate(
        matches,
        start=1,
    ):

        result_badge = (
            "🟢 OVER"
            if item["line_result"] == "OVER"
            else "🔴 UNDER"
        )

        btts_badge = (
            "BTTS"
            if item["btts"] == "BTTS"
            else "NO BTTS"
        )

        st.markdown(
            f"""
            <div class="score-row">
                <b>#{idx}</b>
                &nbsp;&nbsp;
                {format_scoreline_date(item["date"])}
                &nbsp;&nbsp;|&nbsp;&nbsp;
                {item["home"]}
                <b>{item["home_goals"]}</b>
                -
                <b>{item["away_goals"]}</b>
                {item["away"]}
                &nbsp;&nbsp;
                <span class="small-muted">
                    {result_badge} • {btts_badge}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_check_table(
    title,
    checks,
):
    st.markdown(
        f"##### {title}"
    )

    rows = []

    for name, passed in checks.items():
        icon = "✅" if passed else "❌"
        rows.append(
            f"{icon} {name}"
        )

    for row in rows:
        st.write(row)


def render_model_panel(
    analysis,
):
    model = analysis["model"]

    candidate = analysis.get(
        "candidate_side"
    )

    model_probability = analysis.get(
        "model_probability"
    )

    market_probability = analysis.get(
        "market_probability"
    )

    model_edge = analysis.get(
        "model_edge"
    )

    odds = analysis.get(
        "odds"
    )

    st.markdown(
        """
        <div class="model-box">
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "##### 🧠 MODEL / MARKET"
    )

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "Home λ",
            f"{model['home_expected_goals']:.2f}",
        )

    with m2:
        st.metric(
            "Away λ",
            f"{model['away_expected_goals']:.2f}",
        )

    with m3:
        st.metric(
            "Total λ",
            f"{model['total_expected_goals']:.2f}",
        )

    with m4:
        if model_probability is not None:
            st.metric(
                "Model Probability",
                f"{model_probability:.2f}%",
            )
        else:
            st.metric(
                "Model Probability",
                "N/A",
            )

    if odds:

        o1, o2, o3 = st.columns(3)

        with o1:
            st.metric(
                "Market Odds",
                f"{odds['odds']:.2f}",
            )

        with o2:
            if market_probability is not None:
                st.metric(
                    "Implied Probability",
                    f"{market_probability:.2f}%",
                )
            else:
                st.metric(
                    "Implied Probability",
                    "N/A",
                )

        with o3:
            if model_edge is not None:

                if model_edge >= 0:
                    st.markdown(
                        f"""
                        <div>
                            <span class="small-muted">
                                MODEL EDGE
                            </span><br>
                            <span class="edge-positive">
                                +{model_edge:.2f}%
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                        <div>
                            <span class="small-muted">
                                MODEL EDGE
                            </span><br>
                            <span class="edge-negative">
                                {model_edge:.2f}%
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.caption(
            f"Best available bookmaker: "
            f"**{odds['bookmaker']}** • "
            f"{odds['num_bookmakers']} valid price(s) found"
        )

    else:
        st.warning(
            "⚠️ Real bookmaker O/U 2.5 odds မရသေးပါ။ "
            "ဒါကြောင့် Model Edge မတွက်နိုင်သဖြင့် "
            "⭐⭐⭐⭐⭐ မပေးပါ။"
        )

    st.caption(
        "xG မသုံးထားပါ။ λ (expected goals) ကို "
        "L5 GF/GA data မှ Poisson model ဖြင့် "
        "ခန့်မှန်းထားခြင်းသာဖြစ်ပြီး calibration/backtest "
        "မပြီးသေးပါ။"
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# 15. MAIN HEADER
# ============================================================

st.markdown(
    """
    ## ⚽ Pre-Match
    <span style="color:#00f2fe;">
        Over/Under Intelligence Pro
    </span>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Exact L5 Home/Away • No xG • "
    "Poisson Model Probability • Real Market Odds • "
    "Model Edge • 5-Star Qualification"
)


# ============================================================
# 16. DATE CONTROLS
# ============================================================

current_mmt_date = datetime.now(
    MMT_TIMEZONE
).date()

if "target_date" not in st.session_state:
    st.session_state.target_date = (
        current_mmt_date
    )

c_d1, c_d2, c_d3, c_d4 = st.columns(
    [2, 1, 1, 2]
)

with c_d1:
    st.session_state.target_date = (
        st.date_input(
            "📅 စစ်ဆေးလိုသည့် ရက်စွဲ",
            value=st.session_state.target_date,
        )
    )

with c_d2:
    if st.button("⬅️ Yesterday"):
        st.session_state.target_date = (
            current_mmt_date
            - timedelta(days=1)
        )
        st.rerun()

with c_d3:
    if st.button("➡️ Tomorrow"):
        st.session_state.target_date = (
            current_mmt_date
            + timedelta(days=1)
        )
        st.rerun()

with c_d4:
    show_upcoming_only = st.checkbox(
        "⏳ Upcoming Matches Only",
        value=True,
    )


date_str = (
    st.session_state.target_date
    .strftime("%Y-%m-%d")
)


st.divider()


# ============================================================
# 17. SCAN BUTTON
# ============================================================

col_b1, col_b2 = st.columns(
    [3, 1]
)

with col_b1:
    st.markdown(
        f"""
        ### 📋 Selected Date:
        **`{date_str}` (MMT)**
        """
    )

with col_b2:
    scan_clicked = st.button(
        "🔍 Scan & Evaluate",
        type="primary",
        use_container_width=True,
    )


if not scan_clicked:

    st.info(
        f"`{date_str}` ရက်စွဲအတွက် Whitelist "
        "ပွဲများကို စစ်ရန် "
        "**🔍 Scan & Evaluate** ကိုနှိပ်ပါ။"
    )

    st.markdown(
        """
        ### ⭐ 5-Star Qualification

        **OVER 2.5**

        - Exact Home L5 O2.5 ≥ 60%
        - Exact Away L5 O2.5 ≥ 60%
        - Home GF > 1.5
        - Home GA > 1.0
        - Away GF > 1.0
        - Away GA > 1.0
        - Home BTTS ≥ 60%
        - Away BTTS ≥ 60%
        - Model Probability ≥ 60%
        - Model Edge ≥ 5%

        **UNDER 2.5**

        - Exact Home L5 U2.5 ≥ 60%
        - Exact Away L5 U2.5 ≥ 60%
        - Home GF < 1.3
        - Home GA < 1.0
        - Away GF < 1.1
        - Away GA < 1.2
        - Home BTTS ≤ 50%
        - Away BTTS ≤ 50%
        - Model Probability ≥ 60%
        - Model Edge ≥ 5%

        **xG = မသုံးပါ။**
        """,
    )


# ============================================================
# 18. SCAN
# ============================================================

else:

    with st.spinner(
        f"Loading fixtures for {date_str}..."
    ):

        raw_matches, conn_status = (
            fetch_api_cached(
                f"fixtures?date={date_str}"
                f"&timezone=Asia/Yangon",
                cache_bucket="fixtures",
            )
        )

    if not raw_matches:

        st.error(
            f"⚠️ API Error: `{conn_status}`"
        )

        st.info(
            "API limit ဖြစ်နေရင် ခဏစောင့်ပြီး "
            "ပြန် Scan လုပ်ပါ။"
        )

        st.stop()

    # --------------------------------------------------------
    # Whitelist
    # --------------------------------------------------------

    filtered_fixtures = [
        f
        for f in raw_matches
        if is_allowed_league(
            f["league"]["name"],
            f["league"].get(
                "country",
                "",
            ),
            f["teams"]["home"]["name"],
            f["teams"]["away"]["name"],
        )
    ]

    # --------------------------------------------------------
    # Upcoming only
    # --------------------------------------------------------

    if show_upcoming_only:

        filtered_fixtures = [
            f
            for f in filtered_fixtures
            if f["fixture"]["status"]["short"]
            in {
                "NS",
                "TBD",
            }
        ]

    if not filtered_fixtures:

        st.warning(
            f"`{date_str}` မှာ Whitelist criteria "
            "ကိုက်ညီတဲ့ fixtures မတွေ့ပါ။"
        )

        st.stop()

    # --------------------------------------------------------
    # Containers
    # --------------------------------------------------------

    analyzed_cards = []

    star5_count = 0
    model_candidate_count = 0
    insufficient_count = 0
    odds_missing_count = 0

    finished_evaluated = 0
    won_count = 0
    lost_count = 0

    prog_bar = st.progress(
        0,
        text="Preparing exact L5 analysis...",
    )

    total_fixtures = len(
        filtered_fixtures
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # We evaluate base data first.
    # Odds are requested only when a candidate exists.
    # This saves API quota.
    # --------------------------------------------------------

    for i, fixture in enumerate(
        filtered_fixtures
    ):

        home_name = fixture["teams"][
            "home"
        ]["name"]

        away_name = fixture["teams"][
            "away"
        ]["name"]

        prog_bar.progress(
            (i + 1) / total_fixtures,
            text=(
                f"Analyzing {i + 1}/"
                f"{total_fixtures}: "
                f"{home_name} vs {away_name}"
            ),
        )

        status_short = (
            fixture["fixture"]["status"][
                "short"
            ]
        )

        score_h = fixture["goals"]["home"]
        score_a = fixture["goals"]["away"]

        is_finished = (
            is_completed_status(
                status_short
            )
            and score_h is not None
            and score_a is not None
        )

        # ----------------------------------------------------
        # Evaluate
        # ----------------------------------------------------

        analysis = evaluate_fixture(
            fixture,
            fetch_odds=True,
        )

        # ----------------------------------------------------
        # Backtest only if a STAR_5 analysis
        #
        # NOTE:
        # Historical odds may be unavailable because
        # API-Football retains odds history for only 7 days.
        # Therefore this is not a full historical odds backtest.
        # ----------------------------------------------------

        backtest_badge = None

        if (
            is_finished
            and analysis.get("star5", False)
        ):

            finished_evaluated += 1

            total_actual_goals = (
                score_h + score_a
            )

            if (
                analysis["candidate_side"]
                == "OVER_2_5"
                and total_actual_goals >= 3
            ):
                won_count += 1

                backtest_badge = (
                    "WON",
                    (
                        f"✅ WON "
                        f"[{score_h}-{score_a}]"
                    ),
                )

            elif (
                analysis["candidate_side"]
                == "UNDER_2_5"
                and total_actual_goals <= 2
            ):
                won_count += 1

                backtest_badge = (
                    "WON",
                    (
                        f"✅ WON "
                        f"[{score_h}-{score_a}]"
                    ),
                )

            else:
                lost_count += 1

                backtest_badge = (
                    "LOSS",
                    (
                        f"❌ LOST "
                        f"[{score_h}-{score_a}]"
                    ),
                )

        # ----------------------------------------------------
        # Counters
        # ----------------------------------------------------

        if analysis.get("status") == "INSUFFICIENT_DATA":
            insufficient_count += 1

        if analysis.get("candidate_side"):
            model_candidate_count += 1

        if (
            analysis.get("status")
            == "ODDS_UNAVAILABLE"
        ):
            odds_missing_count += 1

        if analysis.get("star5", False):
            star5_count += 1

        # ----------------------------------------------------
        # Keep only useful analysis cards:
        #
        # STAR_5
        # model candidates
        # odds unavailable candidates
        #
        # This prevents UI overload from dozens of neutral games.
        # ----------------------------------------------------

        if (
            analysis.get("star5", False)
            or analysis.get("candidate_side")
            or analysis.get("status")
            == "ODDS_UNAVAILABLE"
        ):

            analyzed_cards.append(
                {
                    "fixture": fixture,
                    "home": home_name,
                    "away": away_name,
                    "league": fixture[
                        "league"
                    ]["name"],
                    "country": fixture[
                        "league"
                    ].get(
                        "country",
                        "",
                    ),
                    "time": convert_to_mmt(
                        fixture[
                            "fixture"
                        ]["date"]
                    ),
                    "status": status_short,
                    "analysis": analysis,
                    "is_finished": is_finished,
                    "backtest": backtest_badge,
                }
            )

    prog_bar.empty()

    # ========================================================
    # 19. PERFORMANCE SUMMARY
    # ========================================================

    win_rate = (
        (
            won_count
            / finished_evaluated
            * 100
        )
        if finished_evaluated > 0
        else None
    )

    st.markdown(
        f"""
        <div class="hero-card">

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
            ">

                <h4 style="
                    margin:0;
                    color:#00f2fe;
                ">
                    📊 SCAN SUMMARY
                    ({date_str})
                </h4>

                <span style="
                    font-size:12px;
                    color:#8b949e;
                ">
                    API: {conn_status}
                </span>

            </div>

            <hr style="
                border-color:#222d3d;
                margin:10px 0;
            ">

            <div style="
                display:grid;
                grid-template-columns:
                repeat(auto-fit,
                minmax(130px,1fr));
                gap:10px;
                text-align:center;
            ">

                <div>
                    <span class="small-muted">
                        WHITELIST
                    </span>
                    <br>
                    <b style="font-size:18px;">
                        {len(filtered_fixtures)}
                    </b>
                </div>

                <div>
                    <span class="small-muted">
                        MODEL CANDIDATES
                    </span>
                    <br>
                    <b style="
                        font-size:18px;
                        color:#00f2fe;
                    ">
                        {model_candidate_count}
                    </b>
                </div>

                <div>
                    <span class="small-muted">
                        ⭐⭐⭐⭐⭐ PICKS
                    </span>
                    <br>
                    <b style="
                        font-size:18px;
                        color:#ffd600;
                    ">
                        {star5_count}
                    </b>
                </div>

                <div>
                    <span class="small-muted">
                        INSUFFICIENT L5
                    </span>
                    <br>
                    <b style="font-size:18px;">
                        {insufficient_count}
                    </b>
                </div>

                <div>
                    <span class="small-muted">
                        ODDS MISSING
                    </span>
                    <br>
                    <b style="font-size:18px;">
                        {odds_missing_count}
                    </b>
                </div>

                <div>
                    <span class="small-muted">
                        WON / LOST
                    </span>
                    <br>
                    <b style="
                        font-size:18px;
                        color:#00e676;
                    ">
                        {won_count}
                    </b>
                    /
                    <b style="
                        font-size:18px;
                        color:#ff1744;
                    ">
                        {lost_count}
                    </b>
                </div>

                <div>
                    <span class="small-muted">
                        STAR-5 WIN RATE
                    </span>
                    <br>
                    <b style="
                        font-size:18px;
                        color:#ffd600;
                    ">
                        {
                            f"{win_rate:.1f}%"
                            if win_rate is not None
                            else "N/A"
                        }
                    </b>
                </div>

            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # 20. EXPLANATION
    # ========================================================

    st.info(
        "⭐ **5-Star rule:** Base L5 criteria "
        "အားလုံးပြည့် + Model Probability ≥ 60% "
        "+ Real Market Model Edge ≥ 5% ဖြစ်မှသာ "
        "⭐⭐⭐⭐⭐ ပေးထားပါတယ်။ "
        "xG မပါပါ။"
    )

    # ========================================================
    # 21. SORT STAR 5 FIRST
    # ========================================================

    analyzed_cards.sort(
        key=lambda card: (
            card["analysis"].get(
                "star5",
                False,
            ),
            card["analysis"].get(
                "model_edge",
                -999,
            )
            if card["analysis"].get(
                "model_edge"
            ) is not None
            else -999,
        ),
        reverse=True,
    )

    # ========================================================
    # 22. DISPLAY
    # ========================================================

    if not analyzed_cards:

        st.info(
            "သတ်မှတ်ထားတဲ့ Base Criteria + "
            "Model Probability ≥ 60% ကိုက်တဲ့ "
            "candidate မတွေ့ပါ။"
        )

    else:

        for card in analyzed_cards:

            analysis = card["analysis"]

            hs = analysis.get(
                "home_stats"
            )

            aws = analysis.get(
                "away_stats"
            )

            candidate = analysis.get(
                "candidate_side"
            )

            is_star5 = analysis.get(
                "star5",
                False,
            )

            # ------------------------------------------------
            # Match container
            # ------------------------------------------------

            with st.container():

                st.markdown(
                    '<div class="match-box">',
                    unsafe_allow_html=True,
                )

                c1, c2, c3 = st.columns(
                    [3, 2, 2]
                )

                # ------------------------------------------------
                # MATCH
                # ------------------------------------------------

                with c1:

                    st.markdown(
                        f"""
                        <span class="league-badge">
                            🏆 {card['league']}
                            • {card['country']}
                        </span>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        f"""
                        ### ⚽ {card['home']}
                        vs
                        {card['away']}
                        """
                    )

                    st.caption(
                        f"⏰ {card['time']} MMT "
                        f"• Status: {card['status']}"
                    )

                # ------------------------------------------------
                # SIGNAL
                # ------------------------------------------------

                with c2:

                    if candidate == "OVER_2_5":

                        st.markdown(
                            """
                            <span class="badge-over">
                                OVER 2.5
                            </span>
                            """,
                            unsafe_allow_html=True,
                        )

                    elif candidate == "UNDER_2_5":

                        st.markdown(
                            """
                            <span class="badge-under">
                                UNDER 2.5
                            </span>
                            """,
                            unsafe_allow_html=True,
                        )

                    else:

                        st.markdown(
                            """
                            <span class="badge-neutral">
                                NO QUALIFIED SIDE
                            </span>
                            """,
                            unsafe_allow_html=True,
                        )

                    if is_star5:

                        st.markdown(
                            """
                            <div class="badge-star">
                                ⭐⭐⭐⭐⭐
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.success(
                            "5-STAR QUALIFIED"
                        )

                    else:

                        st.markdown(
                            """
                            <div style="
                                color:#8b949e;
                                font-size:18px;
                                margin-top:8px;
                            ">
                                ⭐⭐⭐⭐⭐
                                <span style="
                                    font-size:11px;
                                ">
                                    NOT QUALIFIED
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    if (
                        analysis.get(
                            "model_probability"
                        )
                        is not None
                    ):

                        st.caption(
                            "Model Probability: "
                            f"**"
                            f"{analysis['model_probability']:.2f}%"
                            f"**"
                        )

                    if (
                        analysis.get(
                            "model_edge"
                        )
                        is not None
                    ):

                        edge = analysis[
                            "model_edge"
                        ]

                        if edge >= MIN_MODEL_EDGE:
                            st.caption(
                                "Model Edge: "
                                f"**+{edge:.2f}% ✅**"
                            )
                        else:
                            st.caption(
                                "Model Edge: "
                                f"**{edge:.2f}% ❌**"
                            )

                # ------------------------------------------------
                # RESULT
                # ------------------------------------------------

                with c3:

                    if card["backtest"]:

                        res_type, res_text = (
                            card["backtest"]
                        )

                        if res_type == "WON":

                            st.markdown(
                                f"""
                                <div class="badge-win">
                                    {res_text}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        else:

                            st.markdown(
                                f"""
                                <div class="badge-loss">
                                    {res_text}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    elif (
                        analysis.get(
                            "status"
                        )
                        == "ODDS_UNAVAILABLE"
                    ):

                        st.warning(
                            "⚠️ Odds unavailable"
                        )

                    else:

                        st.info(
                            "⏳ Candidate / "
                            "not yet 5-star"
                        )

                # =================================================
                # METRICS
                # =================================================

                if hs and aws:

                    st.markdown(
                        "##### 📊 Exact L5 Metrics"
                    )

                    b1, b2, b3, b4 = (
                        st.columns(4)
                    )

                    # -----------------------------
                    # HOME
                    # -----------------------------

                    with b1:

                        if candidate == "UNDER_2_5":

                            st.markdown(
                                metric_html(
                                    "HOME L5 UNDER",
                                    (
                                        f"{hs['under_pct']:.0f}% "
                                        f"({hs['under_count']}/5)"
                                    ),
                                    hs[
                                        "under_pct"
                                    ]
                                    >= UNDER_L5_MIN,
                                    (
                                        f"GF {hs['gf_avg']}"
                                        f" / GA {hs['ga_avg']}"
                                    ),
                                ),
                                unsafe_allow_html=True,
                            )

                        else:

                            st.markdown(
                                metric_html(
                                    "HOME L5 OVER",
                                    (
                                        f"{hs['over_pct']:.0f}% "
                                        f"({hs['over_count']}/5)"
                                    ),
                                    hs[
                                        "over_pct"
                                    ]
                                    >= OVER_L5_MIN,
                                    (
                                        f"GF {hs['gf_avg']}"
                                        f" / GA {hs['ga_avg']}"
                                    ),
                                ),
                                unsafe_allow_html=True,
                            )

                    # -----------------------------
                    # AWAY
                    # -----------------------------

                    with b2:

                        if candidate == "UNDER_2_5":

                            st.markdown(
                                metric_html(
                                    "AWAY L5 UNDER",
                                    (
                                        f"{aws['under_pct']:.0f}% "
                                        f"({aws['under_count']}/5)"
                                    ),
                                    aws[
                                        "under_pct"
                                    ]
                                    >= UNDER_L5_MIN,
                                    (
                                        f"GF {aws['gf_avg']}"
                                        f" / GA {aws['ga_avg']}"
                                    ),
                                ),
                                unsafe_allow_html=True,
                            )

                        else:

                            st.markdown(
                                metric_html(
                                    "AWAY L5 OVER",
                                    (
                                        f"{aws['over_pct']:.0f}% "
                                        f"({aws['over_count']}/5)"
                                    ),
                                    aws[
                                        "over_pct"
                                    ]
                                    >= OVER_L5_MIN,
                                    (
                                        f"GF {aws['gf_avg']}"
                                        f" / GA {aws['ga_avg']}"
                                    ),
                                ),
                                unsafe_allow_html=True,
                            )

                    # -----------------------------
                    # HOME BTTS
                    # -----------------------------

                    with b3:

                        btts_pass = (
                            hs["btts_pct"]
                            >= OVER_BTTS_MIN
                            if candidate
                            == "OVER_2_5"
                            else hs["btts_pct"]
                            <= UNDER_BTTS_MAX
                        )

                        st.markdown(
                            metric_html(
                                "HOME L5 BTTS",
                                (
                                    f"{hs['btts_pct']:.0f}% "
                                    f"({hs['btts_count']}/5)"
                                ),
                                btts_pass,
                            ),
                            unsafe_allow_html=True,
                        )

                    # -----------------------------
                    # AWAY BTTS
                    # -----------------------------

                    with b4:

                        btts_pass = (
                            aws["btts_pct"]
                            >= OVER_BTTS_MIN
                            if candidate
                            == "OVER_2_5"
                            else aws["btts_pct"]
                            <= UNDER_BTTS_MAX
                        )

                        st.markdown(
                            metric_html(
                                "AWAY L5 BTTS",
                                (
                                    f"{aws['btts_pct']:.0f}% "
                                    f"({aws['btts_count']}/5)"
                                ),
                                btts_pass,
                            ),
                            unsafe_allow_html=True,
                        )

                    # =================================================
                    # MODEL
                    # =================================================

                    st.markdown(
                        "##### 🧠 Model Probability & Real Market Edge"
                    )

                    render_model_panel(
                        analysis
                    )

                    # =================================================
                    # EXPANDER
                    # =================================================

                    with st.expander(
                        "📈 View Exact L5 Scorelines / Criteria"
                    ):

                        tabs = st.tabs(
                            [
                                "🏠 Home L5",
                                "✈️ Away L5",
                                "📋 Criteria",
                            ]
                        )

                        # ---------------------------------------------
                        # HOME L5
                        # ---------------------------------------------

                        with tabs[0]:

                            render_scorelines(
                                "🏠 Last 5 Home Matches",
                                [
                                    {
                                        "date":
                                            item[
                                                "fixture"
                                            ]["date"],
                                        "home":
                                            item[
                                                "teams"
                                            ]["home"][
                                                "name"
                                            ],
                                        "away":
                                            item[
                                                "teams"
                                            ]["away"][
                                                "name"
                                            ],
                                        "home_goals":
                                            item[
                                                "goals"
                                            ]["home"],
                                        "away_goals":
                                            item[
                                                "goals"
                                            ]["away"],
                                        "total_goals":
                                            (
                                                item[
                                                    "goals"
                                                ]["home"]
                                                +
                                                item[
                                                    "goals"
                                                ]["away"]
                                            ),
                                        "line_result":
                                            (
                                                "OVER"
                                                if (
                                                    item[
                                                        "goals"
                                                    ]["home"]
                                                    +
                                                    item[
                                                        "goals"
                                                    ]["away"]
                                                )
                                                >= 3
                                                else "UNDER"
                                            ),
                                        "btts":
                                            (
                                                "BTTS"
                                                if (
                                                    item[
                                                        "goals"
                                                    ]["home"]
                                                    > 0
                                                    and
                                                    item[
                                                        "goals"
                                                    ]["away"]
                                                    > 0
                                                )
                                                else "NO BTTS"
                                            ),
                                    }
                                    for item in
                                    analysis[
                                        "home_l5"
                                    ]
                                ],
                            )

                            st.write(
                                f"**OVER 2.5:** "
                                f"{hs['over_count']}/5 "
                                f"= {hs['over_pct']:.0f}%"
                            )

                            st.write(
                                f"**UNDER 2.5:** "
                                f"{hs['under_count']}/5 "
                                f"= {hs['under_pct']:.0f}%"
                            )

                            st.write(
                                f"**BTTS:** "
                                f"{hs['btts_count']}/5 "
                                f"= {hs['btts_pct']:.0f}%"
                            )

                            st.write(
                                f"**GF:** {hs['gf_avg']} "
                                f"• **GA:** {hs['ga_avg']}"
                            )

                        # ---------------------------------------------
                        # AWAY L5
                        # ---------------------------------------------

                        with tabs[1]:

                            render_scorelines(
                                "✈️ Last 5 Away Matches",
                                [
                                    {
                                        "date":
                                            item[
                                                "fixture"
                                            ]["date"],
                                        "home":
                                            item[
                                                "teams"
                                            ]["home"][
                                                "name"
                                            ],
                                        "away":
                                            item[
                                                "teams"
                                            ]["away"][
                                                "name"
                                            ],
                                        "home_goals":
                                            item[
                                                "goals"
                                            ]["home"],
                                        "away_goals":
                                            item[
                                                "goals"
                                            ]["away"],
                                        "total_goals":
                                            (
                                                item[
                                                    "goals"
                                                ]["home"]
                                                +
                                                item[
                                                    "goals"
                                                ]["away"]
                                            ),
                                        "line_result":
                                            (
                                                "OVER"
                                                if (
                                                    item[
                                                        "goals"
                                                    ]["home"]
                                                    +
                                                    item[
                                                        "goals"
                                                    ]["away"]
                                                )
                                                >= 3
                                                else "UNDER"
                                            ),
                                        "btts":
                                            (
                                                "BTTS"
                                                if (
                                                    item[
                                                        "goals"
                                                    ]["home"]
                                                    > 0
                                                    and
                                                    item[
                                                        "goals"
                                                    ]["away"]
                                                    > 0
                                                )
                                                else "NO BTTS"
                                            ),
                                    }
                                    for item in
                                    analysis[
                                        "away_l5"
                                    ]
                                ],
                            )

                            st.write(
                                f"**OVER 2.5:** "
                                f"{aws['over_count']}/5 "
                                f"= {aws['over_pct']:.0f}%"
                            )

                            st.write(
                                f"**UNDER 2.5:** "
                                f"{aws['under_count']}/5 "
                                f"= {aws['under_pct']:.0f}%"
                            )

                            st.write(
                                f"**BTTS:** "
                                f"{aws['btts_count']}/5 "
                                f"= {aws['btts_pct']:.0f}%"
                            )

                            st.write(
                                f"**GF:** {aws['gf_avg']} "
                                f"• **GA:** {aws['ga_avg']}"
                            )

                        # ---------------------------------------------
                        # CRITERIA
                        # ---------------------------------------------

                        with tabs[2]:

                            if candidate == "OVER_2_5":

                                render_check_table(
                                    "🟢 OVER 2.5 Base Criteria",
                                    analysis[
                                        "over_checks"
                                    ],
                                )

                            elif candidate == "UNDER_2_5":

                                render_check_table(
                                    "🔴 UNDER 2.5 Base Criteria",
                                    analysis[
                                        "under_checks"
                                    ],
                                )

                            else:

                                st.write(
                                    "No qualified "
                                    "Over/Under side."
                                )

                            st.markdown(
                                "##### ⭐ Final Gate"
                            )

                            probability = analysis.get(
                                "model_probability"
                            )

                            edge = analysis.get(
                                "model_edge"
                            )

                            st.write(
                                (
                                    "Model Probability "
                                    f"≥ {MIN_MODEL_PROBABILITY}%: "
                                    f"{'✅' if probability is not None and probability >= MIN_MODEL_PROBABILITY else '❌'}"
                                )
                            )

                            st.write(
                                (
                                    "Model Edge "
                                    f"≥ {MIN_MODEL_EDGE}%: "
                                    f"{'✅' if edge is not None and edge >= MIN_MODEL_EDGE else '❌'}"
                                )
                            )

                            st.write(
                                (
                                    "Exact Home L5 = 5/5: "
                                    f"{'✅' if len(analysis.get('home_l5', [])) == 5 else '❌'}"
                                )
                            )

                            st.write(
                                (
                                    "Exact Away L5 = 5/5: "
                                    f"{'✅' if len(analysis.get('away_l5', [])) == 5 else '❌'}"
                                )
                            )

                            if is_star5:

                                st.success(
                                    "⭐⭐⭐⭐⭐ FINAL QUALIFICATION PASSED"
                                )

                            else:

                                st.warning(
                                    "⭐⭐⭐⭐⭐ FINAL QUALIFICATION NOT PASSED"
                                )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True,
                )


# ============================================================
# 23. FOOTER
# ============================================================

st.divider()

st.caption(
    "Model: Exact L5 Home/Away + GF/GA + BTTS + "
    "Poisson total-goals probability + real pre-match O/U 2.5 odds. "
    "xG is intentionally excluded."
)

st.caption(
    "⚠️ Model Probability is an estimated statistical output, "
    "not a guaranteed hit rate. "
    "For a trustworthy 60% threshold, historical calibration/backtesting "
    "should be performed before treating the number as a true probability."
)
