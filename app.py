import streamlit as st
import requests

from datetime import datetime, timedelta, timezone, date
from typing import Dict, List, Any


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Football Prematch Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #0b0e14;
        color: #f2f4f8;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: #f5f7fa !important;
    }

    .card {
        background: #171c24;
        border: 1px solid #303744;
        border-radius: 18px;
        padding: 22px;
        margin-bottom: 18px;
    }

    .info-card {
        background: #192b44;
        border-radius: 16px;
        padding: 22px;
        margin: 15px 0;
    }

    .success-card {
        background: #123524;
        border: 1px solid #2f7b50;
        border-radius: 16px;
        padding: 20px;
        margin: 15px 0;
    }

    .warning-card {
        background: #403f0b;
        border: 1px solid #6c6b18;
        border-radius: 16px;
        padding: 20px;
        margin: 15px 0;
    }

    .error-card {
        background: #351c22;
        border: 1px solid #88404c;
        border-radius: 16px;
        padding: 20px;
        margin: 15px 0;
    }

    .league-card {
        background: #151a22;
        border: 1px solid #353c49;
        border-radius: 14px;
        padding: 15px;
        margin-bottom: 10px;
    }

    .league-name {
        font-size: 20px;
        font-weight: 700;
    }

    .league-meta {
        color: #9ca6b5;
        font-size: 14px;
        margin-top: 4px;
    }

    .match-card {
        background: #151a22;
        border: 1px solid #343b48;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .team {
        font-size: 18px;
        font-weight: 700;
    }

    .small {
        color: #9ca6b5;
        font-size: 14px;
    }

    .score {
        font-size: 24px;
        font-weight: 800;
    }

    .quota-box {
        background: #202630;
        border: 1px solid #3b4350;
        border-radius: 14px;
        padding: 16px;
        margin: 12px 0;
    }

    div[data-testid="stButton"] > button {
        border-radius: 12px;
        min-height: 45px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API CONFIGURATION
# ============================================================

API_BASE = "https://v3.football.api-sports.io"

# ------------------------------------------------------------
# IMPORTANT:
# Absolute maximum API requests allowed by this app.
#
# When 80 requests are reached:
# - No 81st request
# - Processing stops immediately
# ------------------------------------------------------------

MAX_API_REQUESTS = 80


# ============================================================
# TIMEZONE
# ============================================================

MMT_TZ = timezone(
    timedelta(hours=6, minutes=30)
)


# ============================================================
# SEASON
# ============================================================

FREE_SEASONS = [
    2022,
    2023,
    2024,
]


# ============================================================
# LOCAL LEAGUE CATALOGUE
# ============================================================
#
# IMPORTANT:
#
# This list is LOCAL.
#
# Searching / filtering / selecting leagues
# DOES NOT use API requests.
#
# API is only called after GET MATCHES.
#

LEAGUES = [

    # ========================================================
    # ENGLAND
    # ========================================================

    {
        "id": 39,
        "name": "Premier League",
        "country": "England",
        "type": "League",
    },

    {
        "id": 40,
        "name": "Championship",
        "country": "England",
        "type": "League",
    },

    {
        "id": 41,
        "name": "League One",
        "country": "England",
        "type": "League",
    },

    {
        "id": 42,
        "name": "League Two",
        "country": "England",
        "type": "League",
    },


    # ========================================================
    # SPAIN
    # ========================================================

    {
        "id": 140,
        "name": "LaLiga",
        "country": "Spain",
        "type": "League",
    },

    {
        "id": 141,
        "name": "LaLiga 2",
        "country": "Spain",
        "type": "League",
    },


    # ========================================================
    # ITALY
    # ========================================================

    {
        "id": 135,
        "name": "Serie A",
        "country": "Italy",
        "type": "League",
    },

    {
        "id": 136,
        "name": "Serie B",
        "country": "Italy",
        "type": "League",
    },


    # ========================================================
    # GERMANY
    # ========================================================

    {
        "id": 78,
        "name": "Bundesliga",
        "country": "Germany",
        "type": "League",
    },

    {
        "id": 79,
        "name": "2. Bundesliga",
        "country": "Germany",
        "type": "League",
    },


    # ========================================================
    # FRANCE
    # ========================================================

    {
        "id": 61,
        "name": "Ligue 1",
        "country": "France",
        "type": "League",
    },

    {
        "id": 62,
        "name": "Ligue 2",
        "country": "France",
        "type": "League",
    },


    # ========================================================
    # NETHERLANDS
    # ========================================================

    {
        "id": 88,
        "name": "Eredivisie",
        "country": "Netherlands",
        "type": "League",
    },


    # ========================================================
    # PORTUGAL
    # ========================================================

    {
        "id": 94,
        "name": "Primeira Liga",
        "country": "Portugal",
        "type": "League",
    },


    # ========================================================
    # BELGIUM
    # ========================================================

    {
        "id": 144,
        "name": "Jupiler Pro League",
        "country": "Belgium",
        "type": "League",
    },


    # ========================================================
    # TURKEY
    # ========================================================

    {
        "id": 203,
        "name": "Süper Lig",
        "country": "Turkey",
        "type": "League",
    },


    # ========================================================
    # SCOTLAND
    # ========================================================

    {
        "id": 179,
        "name": "Premiership",
        "country": "Scotland",
        "type": "League",
    },


    # ========================================================
    # AUSTRIA
    # ========================================================

    {
        "id": 218,
        "name": "Bundesliga",
        "country": "Austria",
        "type": "League",
    },


    # ========================================================
    # SWITZERLAND
    # ========================================================

    {
        "id": 207,
        "name": "Super League",
        "country": "Switzerland",
        "type": "League",
    },


    # ========================================================
    # GREECE
    # ========================================================

    {
        "id": 197,
        "name": "Super League 1",
        "country": "Greece",
        "type": "League",
    },


    # ========================================================
    # DENMARK
    # ========================================================

    {
        "id": 119,
        "name": "Superliga",
        "country": "Denmark",
        "type": "League",
    },


    # ========================================================
    # SWEDEN
    # ========================================================

    {
        "id": 113,
        "name": "Allsvenskan",
        "country": "Sweden",
        "type": "League",
    },


    # ========================================================
    # NORWAY
    # ========================================================

    {
        "id": 103,
        "name": "Eliteserien",
        "country": "Norway",
        "type": "League",
    },


    # ========================================================
    # POLAND
    # ========================================================

    {
        "id": 106,
        "name": "Ekstraklasa",
        "country": "Poland",
        "type": "League",
    },


    # ========================================================
    # CZECH REPUBLIC
    # ========================================================

    {
        "id": 345,
        "name": "Czech Liga",
        "country": "Czech Republic",
        "type": "League",
    },


    # ========================================================
    # ROMANIA
    # ========================================================

    {
        "id": 283,
        "name": "Liga I",
        "country": "Romania",
        "type": "League",
    },


    # ========================================================
    # CROATIA
    # ========================================================

    {
        "id": 210,
        "name": "HNL",
        "country": "Croatia",
        "type": "League",
    },


    # ========================================================
    # SERBIA
    # ========================================================

    {
        "id": 286,
        "name": "Super Liga",
        "country": "Serbia",
        "type": "League",
    },


    # ========================================================
    # SAUDI ARABIA
    # ========================================================

    {
        "id": 307,
        "name": "Saudi Pro League",
        "country": "Saudi-Arabia",
        "type": "League",
    },


    # ========================================================
    # USA
    # ========================================================

    {
        "id": 253,
        "name": "Major League Soccer",
        "country": "USA",
        "type": "League",
    },


    # ========================================================
    # MEXICO
    # ========================================================

    {
        "id": 262,
        "name": "Liga MX",
        "country": "Mexico",
        "type": "League",
    },


    # ========================================================
    # BRAZIL
    # ========================================================

    {
        "id": 71,
        "name": "Serie A",
        "country": "Brazil",
        "type": "League",
    },


    # ========================================================
    # ARGENTINA
    # ========================================================

    {
        "id": 128,
        "name": "Liga Profesional",
        "country": "Argentina",
        "type": "League",
    },


    # ========================================================
    # JAPAN
    # ========================================================

    {
        "id": 98,
        "name": "J1 League",
        "country": "Japan",
        "type": "League",
    },


    # ========================================================
    # SOUTH KOREA
    # ========================================================

    {
        "id": 292,
        "name": "K League 1",
        "country": "South-Korea",
        "type": "League",
    },


    # ========================================================
    # AUSTRALIA
    # ========================================================

    {
        "id": 188,
        "name": "A-League",
        "country": "Australia",
        "type": "League",
    },


    # ========================================================
    # CHINA
    # ========================================================

    {
        "id": 169,
        "name": "Super League",
        "country": "China",
        "type": "League",
    },


    # ========================================================
    # INDIA
    # ========================================================

    {
        "id": 323,
        "name": "Indian Super League",
        "country": "India",
        "type": "League",
    },


    # ========================================================
    # EUROPEAN COMPETITIONS
    # ========================================================

    {
        "id": 2,
        "name": "UEFA Champions League",
        "country": "World",
        "type": "Cup",
    },

    {
        "id": 3,
        "name": "UEFA Europa League",
        "country": "World",
        "type": "Cup",
    },

    {
        "id": 848,
        "name": "UEFA Europa Conference League",
        "country": "World",
        "type": "Cup",
    },
]


# ============================================================
# SESSION STATE
# ============================================================

if "selected_leagues" not in st.session_state:
    st.session_state.selected_leagues = []

if "matches" not in st.session_state:
    st.session_state.matches = []

if "api_errors" not in st.session_state:
    st.session_state.api_errors = []

if "last_request_count" not in st.session_state:
    st.session_state.last_request_count = 0

if "quota_stop" not in st.session_state:
    st.session_state.quota_stop = False


# ============================================================
# API KEY
# ============================================================

def get_api_key() -> str:

    try:

        key = st.secrets.get(
            "API_KEY",
            ""
        )

    except Exception:

        key = ""

    return str(key).strip()


API_KEY = get_api_key()


# ============================================================
# REQUEST COUNTER
# ============================================================

def can_make_api_request() -> bool:

    current_count = (
        st.session_state.last_request_count
    )

    if current_count >= MAX_API_REQUESTS:

        st.session_state.quota_stop = True

        return False

    return True


# ============================================================
# API REQUEST
# ============================================================

def api_get(
    endpoint: str,
    params: Dict[str, Any],
):

    # --------------------------------------------------------
    # HARD 80 REQUEST LIMIT
    # --------------------------------------------------------

    if not can_make_api_request():

        return {
            "ok": False,
            "status_code": 0,
            "data": {
                "errors": {
                    "safety": (
                        "API request safety limit "
                        "of 80 reached."
                    )
                }
            },
            "url": "",
            "blocked": True,
        }


    # --------------------------------------------------------
    # COUNT REQUEST BEFORE SENDING
    # --------------------------------------------------------

    st.session_state.last_request_count += 1

    request_number = (
        st.session_state.last_request_count
    )


    headers = {
        "x-apisports-key": API_KEY
    }

    url = API_BASE + endpoint


    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=25,
        )


        # ----------------------------------------------------
        # TRY JSON
        # ----------------------------------------------------

        try:

            data = response.json()

        except Exception:

            data = {}


        # ----------------------------------------------------
        # API RATE LIMIT
        # ----------------------------------------------------

        if response.status_code == 429:

            return {
                "ok": False,
                "status_code": 429,
                "data": data,
                "url": response.url,
                "blocked": False,
                "rate_limited": True,
                "request_number": request_number,
            }


        return {
            "ok": response.ok,
            "status_code": response.status_code,
            "data": data,
            "url": response.url,
            "blocked": False,
            "rate_limited": False,
            "request_number": request_number,
        }


    except requests.RequestException as exc:

        return {
            "ok": False,
            "status_code": 0,
            "data": {
                "errors": {
                    "network": str(exc)
                }
            },
            "url": url,
            "blocked": False,
            "rate_limited": False,
            "request_number": request_number,
        }


# ============================================================
# ERROR FORMATTER
# ============================================================

def format_api_error(
    result: Dict[str, Any]
) -> str:

    data = result.get(
        "data",
        {}
    )

    errors = data.get(
        "errors"
    )

    if isinstance(errors, dict):

        if errors:

            return " | ".join(
                f"{key}: {value}"
                for key, value in errors.items()
            )

    if isinstance(errors, list):

        return " | ".join(
            str(x)
            for x in errors
        )

    status_code = result.get(
        "status_code"
    )

    if status_code:

        return f"HTTP {status_code}"

    return "Unknown API error"


# ============================================================
# LOCAL LEAGUE SEARCH
# ============================================================

def search_local_leagues(
    query: str,
    country: str,
    league_type: str,
) -> List[Dict[str, Any]]:

    query = (
        query
        .strip()
        .lower()
    )

    results = []


    for league in LEAGUES:

        name = (
            league["name"]
            .lower()
        )

        league_country = (
            league["country"]
            .lower()
        )

        league_id = str(
            league["id"]
        )


        # ----------------------------------------------------
        # TEXT SEARCH
        # ----------------------------------------------------

        if query:

            if not (
                query in name
                or query in league_country
                or query in league_id
            ):

                continue


        # ----------------------------------------------------
        # COUNTRY
        # ----------------------------------------------------

        if country != "All Countries":

            if (
                league["country"]
                != country
            ):

                continue


        # ----------------------------------------------------
        # TYPE
        # ----------------------------------------------------

        if league_type != "All":

            if (
                league["type"]
                != league_type
            ):

                continue


        results.append(
            league
        )


    return results


# ============================================================
# ADD LEAGUE
# ============================================================

def add_league(
    league: Dict[str, Any]
):

    exists = any(
        x["id"] == league["id"]
        for x in st.session_state.selected_leagues
    )

    if not exists:

        st.session_state.selected_leagues.append(
            league
        )


# ============================================================
# REMOVE LEAGUE
# ============================================================

def remove_league(
    league_id: int
):

    st.session_state.selected_leagues = [
        x
        for x in st.session_state.selected_leagues
        if x["id"] != league_id
    ]


# ============================================================
# MMT SEARCH WINDOW
# ============================================================

def get_mmt_window():

    now_mmt = datetime.now(
        MMT_TZ
    )

    # --------------------------------------------------------
    # TODAY 12:00 PM MMT
    # --------------------------------------------------------

    start = datetime(
        now_mmt.year,
        now_mmt.month,
        now_mmt.day,
        12,
        0,
        0,
        tzinfo=MMT_TZ,
    )


    # --------------------------------------------------------
    # TOMORROW 12:00 PM MMT
    # --------------------------------------------------------

    end = (
        start
        + timedelta(days=1)
    )


    return start, end


# ============================================================
# FETCH FIXTURES FOR ONE LEAGUE
# ============================================================

def fetch_league_matches(
    league: Dict[str, Any],
    season: int,
    from_date: date,
    to_date: date,
):

    params = {

        "league": league["id"],

        "season": season,

        "from": (
            from_date
            .isoformat()
        ),

        "to": (
            to_date
            .isoformat()
        ),

        # ----------------------------------------------------
        # API-Football returns fixture times using this
        # timezone.
        # ----------------------------------------------------

        "timezone": "Asia/Yangon",
    }


    return api_get(
        "/fixtures",
        params,
    )


# ============================================================
# FILTER EXACT MMT WINDOW
# ============================================================

def filter_mmt_window(
    fixtures: List[Dict[str, Any]],
    start_mmt: datetime,
    end_mmt: datetime,
):

    filtered = []

    seen = set()


    for fixture in fixtures:

        fixture_id = (
            fixture
            .get("fixture", {})
            .get("id")
        )


        if fixture_id in seen:

            continue


        seen.add(
            fixture_id
        )


        fixture_date = (
            fixture
            .get("fixture", {})
            .get("date")
        )


        if not fixture_date:

            continue


        try:

            dt = datetime.fromisoformat(
                fixture_date
            )

        except Exception:

            continue


        # ----------------------------------------------------
        # API may return offset-aware datetime.
        # ----------------------------------------------------

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=MMT_TZ
            )

        else:

            dt = dt.astimezone(
                MMT_TZ
            )


        # ----------------------------------------------------
        # EXACT:
        #
        # TODAY 12:00 PM
        # TO
        # TOMORROW 12:00 PM
        # ----------------------------------------------------

        if (
            start_mmt
            <= dt
            < end_mmt
        ):

            filtered.append(
                fixture
            )


    return filtered


# ============================================================
# RENDER MATCH
# ============================================================

def render_match(
    match: Dict[str, Any]
):

    fixture = match.get(
        "fixture",
        {}
    )

    teams = match.get(
        "teams",
        {}
    )

    league = match.get(
        "league",
        {}
    )

    goals = match.get(
        "goals",
        {}
    )


    fixture_id = fixture.get(
        "id",
        "-"
    )


    timestamp = fixture.get(
        "date",
        ""
    )


    home = teams.get(
        "home",
        {}
    )

    away = teams.get(
        "away",
        {}
    )


    home_name = home.get(
        "name",
        "Home"
    )

    away_name = away.get(
        "name",
        "Away"
    )


    home_goals = goals.get(
        "home"
    )

    away_goals = goals.get(
        "away"
    )


    status = (
        fixture
        .get("status", {})
        .get("short", "")
    )


    league_name = league.get(
        "name",
        ""
    )

    country = league.get(
        "country",
        ""
    )


    # --------------------------------------------------------
    # Convert kickoff to MMT
    # --------------------------------------------------------

    display_kickoff = timestamp

    if timestamp:

        try:

            dt = datetime.fromisoformat(
                timestamp
            )

            if dt.tzinfo is None:

                dt = dt.replace(
                    tzinfo=timezone.utc
                )

            dt = dt.astimezone(
                MMT_TZ
            )

            display_kickoff = (
                dt.strftime(
                    "%Y-%m-%d %I:%M %p"
                )
                + " MMT"
            )

        except Exception:

            pass


    st.markdown(
        f"""
        <div class="match-card">

            <div class="small">
                {league_name}
                •
                {country}
                &nbsp;&nbsp;|&nbsp;&nbsp;
                Fixture ID: {fixture_id}
            </div>

            <br>

            <div class="team">
                {home_name}
            </div>

            <div class="score">
                {
                    home_goals
                    if home_goals is not None
                    else "-"
                }
                &nbsp; - &nbsp;
                {
                    away_goals
                    if away_goals is not None
                    else "-"
                }
            </div>

            <div class="team">
                {away_name}
            </div>

            <br>

            <div class="small">

                Status:
                {status}

                <br>

                Kickoff:
                {display_kickoff}

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HEADER
# ============================================================

st.title(
    "⚽ Football Prematch Dashboard"
)


st.markdown(
    """
    <div class="info-card">

        <b>Multi-League Prematch Mode</b>

        <br><br>

        ① League ကိုရွေးပါ<br>
        ② Season ကိုရွေးပါ<br>
        ③ GET MATCHES နှိပ်ပါ<br>
        ④ ရွေးထားတဲ့ League တွေကိုပဲ API က ဖတ်ပါမယ်

        <br><br>

        <b>Match Window:</b><br>
        Myanmar Time နဲ့
        <b>ဒီနေ့ 12:00 PM → နောက်နေ့ 12:00 PM</b>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API STATUS
# ============================================================

st.subheader(
    "🛡️ API Status"
)


if API_KEY:

    current_requests = (
        st.session_state.last_request_count
    )

    remaining_local = max(
        0,
        MAX_API_REQUESTS
        - current_requests
    )


    st.markdown(
        f"""
        <div class="success-card">

            🟢 API key detected.

            <br><br>

            Requests this run:
            <b>{current_requests}</b>
            / {MAX_API_REQUESTS}

            <br>

            Local safety remaining:
            <b>{remaining_local}</b>

        </div>
        """,
        unsafe_allow_html=True,
    )


else:

    st.markdown(
        """
        <div class="warning-card">

            🟡 API key မတွေ့သေးပါ။

            <br><br>

            Streamlit Secrets ထဲမှာ

            <br><br>

            <b>API_KEY = "YOUR_API_KEY"</b>

            <br><br>

            ထည့်ထားရပါမယ်။

            <br><br>

            League Search / Selection ကို
            API key မရှိဘဲ သုံးနိုင်ပါတယ်။

            <br><br>

            GET MATCHES အတွက် API key လိုပါတယ်။

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SEARCH LEAGUE
# ============================================================

st.header(
    "🏆 Search League"
)


st.caption(
    "League နာမည် အလွတ်ကျက်စရာမလိုပါ။ "
    "Search / Country / Type နဲ့ ရွေးနိုင်ပါတယ်။"
)


col1, col2, col3 = st.columns(
    [2.2, 1.2, 1.0]
)


with col1:

    search_query = st.text_input(
        "🔍 Search",
        placeholder=(
            "ဥပမာ: Premier, LaLiga, "
            "Champions, Serie..."
        ),
        key="league_search",
    )


with col2:

    countries = sorted(
        set(
            x["country"]
            for x in LEAGUES
        )
    )

    country_options = (
        ["All Countries"]
        + countries
    )

    selected_country = st.selectbox(
        "🌍 Country",
        country_options,
    )


with col3:

    selected_type = st.selectbox(
        "🏆 Type",
        [
            "All",
            "League",
            "Cup",
        ],
    )


# ============================================================
# SEARCH RESULTS
# ============================================================

search_results = search_local_leagues(
    search_query,
    selected_country,
    selected_type,
)


st.write(
    f"**Search Results: "
    f"{len(search_results)} leagues**"
)


if not search_results:

    st.warning(
        "League မတွေ့ပါ။ "
        "Search စာလုံးကို ပြောင်းပြီး "
        "ထပ်ရှာကြည့်ပါ။"
    )

else:

    display_results = (
        search_results[:50]
    )


    for league in display_results:

        already_selected = any(
            x["id"] == league["id"]
            for x in st.session_state.selected_leagues
        )


        c1, c2 = st.columns(
            [5, 1]
        )


        with c1:

            st.markdown(
                f"""
                <div class="league-card">

                    <div class="league-name">
                        🏆 {league["name"]}
                    </div>

                    <div class="league-meta">

                        🌍 {league["country"]}

                        &nbsp; • &nbsp;

                        {league["type"]}

                        &nbsp; • &nbsp;

                        League ID:
                        {league["id"]}

                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


        with c2:

            if already_selected:

                st.button(
                    "✓ Selected",
                    key=(
                        f"selected_"
                        f"{league['id']}"
                    ),
                    disabled=True,
                    use_container_width=True,
                )

            else:

                if st.button(
                    "＋ Select",
                    key=(
                        f"select_"
                        f"{league['id']}"
                    ),
                    use_container_width=True,
                ):

                    add_league(
                        league
                    )

                    st.rerun()


# ============================================================
# SELECTED LEAGUES
# ============================================================

st.header(
    "✅ Selected Leagues"
)


selected = (
    st.session_state.selected_leagues
)


if not selected:

    st.info(
        "အခုထိ League မရွေးရသေးပါ။ "
        "အပေါ်က Search Results ကနေ "
        "Select နှိပ်ပါ။"
    )


else:

    st.markdown(
        f"""
        <div class="info-card">

            <b>
                Selected leagues:
                {len(selected)}
            </b>

            <br><br>

            ဒီ League တွေကိုပဲ
            GET MATCHES နှိပ်တဲ့အခါ
            API က ဖတ်ပါမယ်။

        </div>
        """,
        unsafe_allow_html=True,
    )


    for league in selected:

        c1, c2 = st.columns(
            [6, 1]
        )


        with c1:

            st.markdown(
                f"""
                <div class="league-card">

                    <div class="league-name">
                        🏆 {league["name"]}
                    </div>

                    <div class="league-meta">

                        🌍 {league["country"]}

                        &nbsp; • &nbsp;

                        League ID:
                        {league["id"]}

                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


        with c2:

            if st.button(
                "✕ Remove",
                key=(
                    f"remove_"
                    f"{league['id']}"
                ),
                use_container_width=True,
            ):

                remove_league(
                    league["id"]
                )

                st.rerun()


# ============================================================
# SEASON
# ============================================================

st.header(
    "📅 Season"
)


season = st.selectbox(
    "API Season",
    FREE_SEASONS,
    index=FREE_SEASONS.index(
        2024
    ),
    format_func=lambda x:
        f"{x}/{str(x + 1)[-2:]}",
)


st.caption(
    "API-Football season ကို "
    "starting year နဲ့သတ်မှတ်ပါတယ်။ "
    "ဥပမာ 2024 = 2024/25."
)


# ============================================================
# AUTOMATIC MMT WINDOW
# ============================================================

st.header(
    "🕐 Myanmar Time Match Window"
)


start_mmt, end_mmt = (
    get_mmt_window()
)


start_display = start_mmt.strftime(
    "%Y-%m-%d %I:%M %p"
)

end_display = end_mmt.strftime(
    "%Y-%m-%d %I:%M %p"
)


st.markdown(
    f"""
    <div class="info-card">

        <b>Automatic Search Window</b>

        <br><br>

        🇲🇲 Myanmar Time

        <br><br>

        <b>
            {start_display}
        </b>

        <br>

        ↓

        <br>

        <b>
            {end_display}
        </b>

        <br><br>

        အဓိပ္ပါယ်က
        <b>ဒီနေ့ 12:00 PM ကနေ
        နောက်နေ့ 12:00 PM</b>
        အတွင်းကပွဲတွေကိုပဲ
        ရှာပါမယ်။

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# REQUEST ESTIMATE
# ============================================================

st.subheader(
    "📊 API Request Estimate"
)


league_count = len(
    selected
)


st.markdown(
    f"""
    <div class="quota-box">

        Selected Leagues:
        <b>{league_count}</b>

        <br><br>

        Fixture Requests:
        <b>{league_count}</b>

        <br><br>

        Safety Limit:
        <b>{MAX_API_REQUESTS}</b>

        <br><br>

        League Search / Filter / Select:
        <b>0 API requests</b>

        <br><br>

        GET MATCHES နှိပ်မှသာ
        selected leagues အတွက်
        API request ပို့ပါမယ်။

    </div>
    """,
    unsafe_allow_html=True,
)


if league_count > MAX_API_REQUESTS:

    st.error(
        "Selected leagues အရေအတွက်က "
        "80 ထက်ကျော်နေပါတယ်။ "
        "GET MATCHES မလုပ်နိုင်ပါ။"
    )


# ============================================================
# GET MATCHES
# ============================================================

st.header(
    "⚽ Get Matches"
)


if st.button(
    "⚽ GET MATCHES",
    type="primary",
    use_container_width=True,
):

    # --------------------------------------------------------
    # CHECK LEAGUES
    # --------------------------------------------------------

    if not selected:

        st.error(
            "အနည်းဆုံး League တစ်ခုရွေးပါ။"
        )

        st.stop()


    # --------------------------------------------------------
    # CHECK API KEY
    # --------------------------------------------------------

    if not API_KEY:

        st.error(
            "API key မတွေ့ပါ။ "
            "Streamlit Secrets ထဲမှာ "
            "API_KEY ထည့်ပါ။"
        )

        st.stop()


    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    st.session_state.matches = []

    st.session_state.api_errors = []

    st.session_state.last_request_count = 0

    st.session_state.quota_stop = False


    all_matches = []

    errors = []


    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    progress = st.progress(
        0
    )


    total = len(
        selected
    )


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Only SELECTED leagues are processed.
    #
    # No API request for unselected leagues.
    # --------------------------------------------------------

    for index, league in enumerate(
        selected,
        start=1
    ):


        # ----------------------------------------------------
        # HARD 80 REQUEST STOP
        # ----------------------------------------------------

        if (
            st.session_state
            .last_request_count
            >= MAX_API_REQUESTS
        ):

            st.session_state.quota_stop = True

            st.warning(
                "🛑 API request safety limit "
                "80 reached. "
                "Processing stopped."
            )

            break


        # ----------------------------------------------------
        # LOAD ONE LEAGUE
        # ----------------------------------------------------

        with st.spinner(
            f"Loading "
            f"{league['name']}..."
        ):

            result = fetch_league_matches(
                league,
                season,
                start_mmt.date(),
                end_mmt.date(),
            )


        # ----------------------------------------------------
        # API RESULT
        # ----------------------------------------------------

        if result.get(
            "blocked",
            False
        ):

            st.session_state.quota_stop = True

            break


        if result.get(
            "rate_limited",
            False
        ):

            errors.append(
                {
                    "league": league,
                    "error": (
                        "API rate limit "
                        "reached (HTTP 429)."
                    ),
                }
            )

            st.warning(
                "🛑 API returned HTTP 429. "
                "Processing stopped."
            )

            break


        if result["ok"]:

            data = result.get(
                "data",
                {}
            )


            response_errors = (
                data.get(
                    "errors"
                )
            )


            if response_errors:

                errors.append(
                    {
                        "league": league,
                        "error": (
                            format_api_error(
                                result
                            )
                        ),
                    }
                )


            else:

                fixtures = data.get(
                    "response",
                    []
                )


                # --------------------------------------------
                # EXACT MMT FILTER
                # --------------------------------------------

                filtered = (
                    filter_mmt_window(
                        fixtures,
                        start_mmt,
                        end_mmt,
                    )
                )


                all_matches.extend(
                    filtered
                )


        else:

            errors.append(
                {
                    "league": league,
                    "error": (
                        format_api_error(
                            result
                        )
                    ),
                }
            )


        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        progress.progress(
            min(
                100,
                int(
                    index
                    / total
                    * 100
                )
            )
        )


    progress.empty()


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    st.session_state.matches = (
        all_matches
    )

    st.session_state.api_errors = (
        errors
    )


    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    st.session_state.matches.sort(
        key=lambda x:
        x.get(
            "fixture",
            {}
        ).get(
            "date",
            ""
        )
    )


    st.rerun()


# ============================================================
# MATCH RESULTS
# ============================================================

st.header(
    "📋 Match Results"
)


matches = (
    st.session_state.matches
)


if not matches:

    st.info(
        "No match data loaded yet."
    )


else:

    st.success(
        f"{len(matches)} matches loaded."
    )


    # --------------------------------------------------------
    # SHOW EXACT WINDOW
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="success-card">

            🇲🇲 <b>Myanmar Time Window</b>

            <br><br>

            {start_display}

            →

            {end_display}

        </div>
        """,
        unsafe_allow_html=True,
    )


    for match in matches:

        render_match(
            match
        )


# ============================================================
# API ERRORS
# ============================================================

errors = (
    st.session_state.api_errors
)


if errors:

    st.header(
        "⚠️ League / API Errors"
    )


    for item in errors:

        league = item[
            "league"
        ]


        st.markdown(
            f"""
            <div class="error-card">

                <h3>
                    ❌ {league["name"]}
                </h3>

                <div class="small">

                    Country:
                    {league["country"]}

                    <br>

                    League ID:
                    {league["id"]}

                    <br>

                    Season:
                    {season}

                </div>

                <br>

                <b>API Error:</b>

                <br>

                {item["error"]}

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# SAFETY STATUS
# ============================================================

st.header(
    "🛡️ API Safety Status"
)


request_count = (
    st.session_state.last_request_count
)


if request_count >= MAX_API_REQUESTS:

    st.markdown(
        """
        <div class="error-card">

            🛑 <b>API SAFETY STOP</b>

            <br><br>

            80 requests reached.

            <br>

            No further API requests
            will be sent by this app.

        </div>
        """,
        unsafe_allow_html=True,
    )


else:

    remaining = (
        MAX_API_REQUESTS
        - request_count
    )


    st.markdown(
        f"""
        <div class="card">

            Requests used:
            <b>{request_count}</b>
            / {MAX_API_REQUESTS}

            <br><br>

            Local safety remaining:
            <b>{remaining}</b>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# IMPORTANT NOTES
# ============================================================

st.header(
    "ℹ️ How This Version Works"
)


st.markdown(
    """
    <div class="warning-card">

        <b>1. League Search</b>

        <br>

        Local catalogue ကိုပဲ search လုပ်တာဖြစ်လို့
        API request မစားပါ။

        <br><br>

        <b>2. League Selection</b>

        <br>

        ကိုယ်ရွေးထားတဲ့ League တွေကိုပဲ
        GET MATCHES လုပ်တဲ့အခါ API က ဖတ်ပါမယ်။

        <br><br>

        <b>3. Myanmar Time</b>

        <br>

        ပွဲရှာတဲ့ window က
        ဒီနေ့ 12:00 PM MMT →
        နောက်နေ့ 12:00 PM MMT ဖြစ်ပါတယ်။

        <br><br>

        <b>4. API Safety</b>

        <br>

        API request 80 ရောက်တာနဲ့
        နောက်ထပ် request မပို့တော့ပါ။

        <br><br>

        <b>5. xG</b>

        <br>

        ဒီ version မှာ xG မပါပါ။
        API က xG မပေးနိုင်တဲ့အတွက်
        မတွက်ထားပါ။

        <br><br>

        <b>6. Model</b>

        <br>

        ဒီ version ရဲ့ ရည်ရွယ်ချက်က
        အရင်ဆုံး League → Fixture
        fetching ကို တည်ငြိမ်အောင်လုပ်တာပါ။
        O2.5 / Under / BTTS model ကို
        ဒီအဆင့်မှာ API fixture fetching နဲ့
        မရောထားပါ။

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    "---"
)


st.caption(
    "Football Prematch Dashboard • "
    "API-Football • Myanmar Time"
)
