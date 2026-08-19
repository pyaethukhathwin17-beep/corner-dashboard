import streamlit as st
import requests
from datetime import date, timedelta
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
# API CONFIG
# ============================================================

API_BASE = "https://v3.football.api-sports.io"

# Free-plan-friendly seasons.
# API-Football uses the starting year of a season:
# 2024 means 2024/25 for most European leagues.
FREE_SEASONS = [2022, 2023, 2024]


# ============================================================
# LOCAL LEAGUE CATALOGUE
# ============================================================
#
# IMPORTANT:
# This catalogue is intentionally local.
#
# Therefore:
# - Search League does NOT consume API requests.
# - Country filtering does NOT consume API requests.
# - Selecting leagues does NOT consume API requests.
#
# API is only called after GET MATCHES.
#
# You can add more leagues later.
#

LEAGUES = [
    # England
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

    # Spain
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

    # Italy
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

    # Germany
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

    # France
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

    # Netherlands
    {
        "id": 88,
        "name": "Eredivisie",
        "country": "Netherlands",
        "type": "League",
    },

    # Portugal
    {
        "id": 94,
        "name": "Primeira Liga",
        "country": "Portugal",
        "type": "League",
    },

    # Belgium
    {
        "id": 144,
        "name": "Jupiler Pro League",
        "country": "Belgium",
        "type": "League",
    },

    # Turkey
    {
        "id": 203,
        "name": "Süper Lig",
        "country": "Turkey",
        "type": "League",
    },

    # Scotland
    {
        "id": 179,
        "name": "Premiership",
        "country": "Scotland",
        "type": "League",
    },

    # Austria
    {
        "id": 218,
        "name": "Bundesliga",
        "country": "Austria",
        "type": "League",
    },

    # Switzerland
    {
        "id": 207,
        "name": "Super League",
        "country": "Switzerland",
        "type": "League",
    },

    # Greece
    {
        "id": 197,
        "name": "Super League 1",
        "country": "Greece",
        "type": "League",
    },

    # Denmark
    {
        "id": 119,
        "name": "Superliga",
        "country": "Denmark",
        "type": "League",
    },

    # Sweden
    {
        "id": 113,
        "name": "Allsvenskan",
        "country": "Sweden",
        "type": "League",
    },

    # Norway
    {
        "id": 103,
        "name": "Eliteserien",
        "country": "Norway",
        "type": "League",
    },

    # Poland
    {
        "id": 106,
        "name": "Ekstraklasa",
        "country": "Poland",
        "type": "League",
    },

    # Czech Republic
    {
        "id": 345,
        "name": "Czech Liga",
        "country": "Czech Republic",
        "type": "League",
    },

    # Romania
    {
        "id": 283,
        "name": "Liga I",
        "country": "Romania",
        "type": "League",
    },

    # Croatia
    {
        "id": 210,
        "name": "HNL",
        "country": "Croatia",
        "type": "League",
    },

    # Serbia
    {
        "id": 286,
        "name": "Super Liga",
        "country": "Serbia",
        "type": "League",
    },

    # Saudi Arabia
    {
        "id": 307,
        "name": "Saudi Pro League",
        "country": "Saudi-Arabia",
        "type": "League",
    },

    # USA
    {
        "id": 253,
        "name": "Major League Soccer",
        "country": "USA",
        "type": "League",
    },

    # Mexico
    {
        "id": 262,
        "name": "Liga MX",
        "country": "Mexico",
        "type": "League",
    },

    # Brazil
    {
        "id": 71,
        "name": "Serie A",
        "country": "Brazil",
        "type": "League",
    },

    # Argentina
    {
        "id": 128,
        "name": "Liga Profesional",
        "country": "Argentina",
        "type": "League",
    },

    # Japan
    {
        "id": 98,
        "name": "J1 League",
        "country": "Japan",
        "type": "League",
    },

    # South Korea
    {
        "id": 292,
        "name": "K League 1",
        "country": "South-Korea",
        "type": "League",
    },

    # Australia
    {
        "id": 188,
        "name": "A-League",
        "country": "Australia",
        "type": "League",
    },

    # China
    {
        "id": 169,
        "name": "Super League",
        "country": "China",
        "type": "League",
    },

    # India
    {
        "id": 323,
        "name": "Indian Super League",
        "country": "India",
        "type": "League",
    },

    # European competitions
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


# ============================================================
# API KEY
# ============================================================

def get_api_key() -> str:
    """
    Read API key from Streamlit secrets.

    .streamlit/secrets.toml

    API_KEY = "YOUR_API_KEY"
    """

    try:
        key = st.secrets.get("API_KEY", "")
    except Exception:
        key = ""

    if not key:
        return ""

    return str(key).strip()


API_KEY = get_api_key()


# ============================================================
# API REQUEST FUNCTION
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def api_get(endpoint: str, params_tuple: tuple):
    """
    Cached GET request.

    params_tuple is used instead of dict because Streamlit cache
    needs hashable arguments.
    """

    params = dict(params_tuple)

    headers = {
        "x-apisports-key": API_KEY
    }

    url = API_BASE + endpoint

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20,
        )

        status_code = response.status_code

        try:
            data = response.json()
        except Exception:
            data = {}

        return {
            "ok": response.ok,
            "status_code": status_code,
            "data": data,
            "url": response.url,
        }

    except requests.RequestException as e:
        return {
            "ok": False,
            "status_code": 0,
            "data": {
                "errors": {
                    "network": str(e)
                }
            },
            "url": url,
        }


# ============================================================
# API ERROR FORMATTER
# ============================================================

def format_api_error(result: Dict[str, Any]) -> str:
    data = result.get("data", {})

    errors = data.get("errors")

    if isinstance(errors, dict) and errors:
        parts = []

        for key, value in errors.items():
            parts.append(f"{key}: {value}")

        return " | ".join(parts)

    if isinstance(errors, list):
        return " | ".join(str(x) for x in errors)

    if result.get("status_code"):
        return f"HTTP {result['status_code']}"

    return "Unknown API error"


# ============================================================
# SEARCH LEAGUES LOCALLY
# ============================================================

def search_local_leagues(
    query: str,
    country: str,
    league_type: str,
) -> List[Dict[str, Any]]:

    query = query.strip().lower()

    results = []

    for league in LEAGUES:

        name = league["name"].lower()
        league_country = league["country"].lower()
        league_id = str(league["id"])

        # Search text
        if query:
            if (
                query not in name
                and query not in league_country
                and query not in league_id
            ):
                continue

        # Country filter
        if country != "All Countries":
            if league["country"] != country:
                continue

        # Type filter
        if league_type != "All":
            if league["type"] != league_type:
                continue

        results.append(league)

    return results


# ============================================================
# ADD LEAGUE
# ============================================================

def add_league(league: Dict[str, Any]):

    exists = any(
        x["id"] == league["id"]
        for x in st.session_state.selected_leagues
    )

    if not exists:
        st.session_state.selected_leagues.append(league)


# ============================================================
# REMOVE LEAGUE
# ============================================================

def remove_league(league_id: int):

    st.session_state.selected_leagues = [
        x
        for x in st.session_state.selected_leagues
        if x["id"] != league_id
    ]


# ============================================================
# FETCH FIXTURES
# ============================================================

def fetch_fixtures(
    league: Dict[str, Any],
    season: int,
    from_date: date,
    to_date: date,
):

    params = {
        "league": league["id"],
        "season": season,
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
    }

    result = api_get(
        "/fixtures",
        tuple(sorted(params.items())),
    )

    return result


# ============================================================
# RENDER MATCH
# ============================================================

def render_match(match: Dict[str, Any]):

    fixture = match.get("fixture", {})
    teams = match.get("teams", {})
    league = match.get("league", {})
    goals = match.get("goals", {})

    fixture_id = fixture.get("id", "-")

    timestamp = fixture.get("date", "")

    home = teams.get("home", {})
    away = teams.get("away", {})

    home_name = home.get("name", "Home")
    away_name = away.get("name", "Away")

    home_goals = goals.get("home")
    away_goals = goals.get("away")

    status = fixture.get("status", {}).get("short", "")

    league_name = league.get("name", "")
    country = league.get("country", "")

    st.markdown(
        f"""
        <div class="match-card">

            <div class="small">
                {league_name} • {country}
                &nbsp;&nbsp;|&nbsp;&nbsp;
                Fixture ID: {fixture_id}
            </div>

            <br>

            <div class="team">
                {home_name}
            </div>

            <div class="score">
                {home_goals if home_goals is not None else "-"}
                &nbsp; - &nbsp;
                {away_goals if away_goals is not None else "-"}
            </div>

            <div class="team">
                {away_name}
            </div>

            <br>

            <div class="small">
                Status: {status}
                <br>
                Kickoff: {timestamp}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HEADER
# ============================================================

st.title("⚽ Football Prematch Dashboard")

st.markdown(
    """
    <div class="info-card">
        <b>Multi-League Prematch Mode</b><br>
        League ကိုအရင်ရွေးပါ → Season ရွေးပါ → Date Window ရွေးပါ
        → GET MATCHES နှိပ်ပါ။
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API STATUS
# ============================================================

st.subheader("🛡️ API Status")

if API_KEY:

    st.markdown(
        """
        <div class="success-card">
            🟢 API key detected.<br>
            API calls are ready.
        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        """
        <div class="warning-card">
            🟡 API key မတွေ့သေးပါ။<br><br>
            League Search နဲ့ League Selection ကို
            API key မရှိဘဲ သုံးနိုင်ပါတယ်။
            <br><br>
            GET MATCHES အတွက်တော့ API key လိုပါတယ်။
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SEARCH LEAGUE
# ============================================================

st.header("🏆 Search League")

st.caption(
    "League နာမည် အလွတ်ကျက်စရာမလိုပါ။ "
    "Search / Country / Type နဲ့ ရွေးနိုင်ပါတယ်။"
)

col1, col2, col3 = st.columns([2.2, 1.2, 1.0])

with col1:

    search_query = st.text_input(
        "🔍 Search",
        placeholder="ဥပမာ: Premier, LaLiga, Champions...",
        key="league_search",
    )

with col2:

    countries = sorted(
        set(x["country"] for x in LEAGUES)
    )

    country_options = ["All Countries"] + countries

    selected_country = st.selectbox(
        "🌍 Country",
        country_options,
    )

with col3:

    selected_type = st.selectbox(
        "🏆 Type",
        ["All", "League", "Cup"],
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
    f"**Search Results: {len(search_results)} leagues**"
)


if not search_results:

    st.warning(
        "League မတွေ့ပါ။ Search စာလုံးကို ပြောင်းပြီး ထပ်ရှာကြည့်ပါ။"
    )

else:

    # Show max 50 results at a time
    display_results = search_results[:50]

    for league in display_results:

        already_selected = any(
            x["id"] == league["id"]
            for x in st.session_state.selected_leagues
        )

        c1, c2 = st.columns([5, 1])

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
                        League ID: {league["id"]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:

            if already_selected:

                st.button(
                    "✓ Selected",
                    key=f"selected_{league['id']}",
                    disabled=True,
                    use_container_width=True,
                )

            else:

                if st.button(
                    "＋ Select",
                    key=f"select_{league['id']}",
                    use_container_width=True,
                ):

                    add_league(league)
                    st.rerun()


# ============================================================
# SELECTED LEAGUES
# ============================================================

st.header("✅ Selected Leagues")

selected = st.session_state.selected_leagues

if not selected:

    st.info(
        "အခုထိ League မရွေးရသေးပါ။ "
        "အပေါ်က Search Results ကနေ Select နှိပ်ပါ။"
    )

else:

    st.markdown(
        f"""
        <div class="info-card">
            <b>Selected leagues: {len(selected)}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for league in selected:

        c1, c2 = st.columns([6, 1])

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
                        League ID: {league["id"]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:

            if st.button(
                "✕ Remove",
                key=f"remove_{league['id']}",
                use_container_width=True,
            ):

                remove_league(league["id"])
                st.rerun()


# ============================================================
# SEASON
# ============================================================

st.header("📅 Season")

season = st.selectbox(
    "API Season",
    FREE_SEASONS,
    index=FREE_SEASONS.index(2024),
    format_func=lambda x: f"{x}/{str(x + 1)[-2:]}",
)

st.caption(
    "API-Football season ကို starting year နဲ့သတ်မှတ်ပါတယ်။ "
    "ဥပမာ 2024 = 2024/25."
)

if season not in FREE_SEASONS:

    st.warning(
        "ဒီ season ကို Free plan မှာ မရနိုင်နိုင်တာကြောင့် "
        "request မပို့ပါ။"
    )


# ============================================================
# SEARCH WINDOW
# ============================================================

st.header("🕐 Search Window")

default_from = date(season, 1, 1)
default_to = date(season, 12, 31)

col1, col2 = st.columns(2)

with col1:

    from_date = st.date_input(
        "From",
        value=default_from,
        min_value=date(season, 1, 1),
        max_value=date(season, 12, 31),
    )

with col2:

    to_date = st.date_input(
        "To",
        value=default_to,
        min_value=date(season, 1, 1),
        max_value=date(season, 12, 31),
    )


# ============================================================
# DATE VALIDATION
# ============================================================

date_valid = from_date <= to_date

if not date_valid:

    st.error(
        "From date က To date ထက် မနောက်ကျရပါ။"
    )


# ============================================================
# API REQUEST ESTIMATE
# ============================================================

st.subheader("📊 Request Estimate")

league_count = len(selected)

st.markdown(
    f"""
    <div class="card">

        Selected leagues:
        <b>{league_count}</b>

        <br><br>

        GET MATCHES နှိပ်ရင် အများဆုံး API calls:
        <b>{league_count}</b>

        <br><br>

        Search League / Country / Select လုပ်တာတွေက
        API request မစားပါ။

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GET MATCHES
# ============================================================

st.header("⚽ Get Matches")

if st.button(
    "⚽ GET MATCHES",
    type="primary",
    use_container_width=True,
):

    # ----------------------------
    # Validate selected leagues
    # ----------------------------

    if not selected:

        st.error(
            "အနည်းဆုံး League တစ်ခုရွေးပါ။"
        )

        st.stop()

    # ----------------------------
    # Validate dates
    # ----------------------------

    if not date_valid:

        st.error(
            "Date range မမှန်ပါ။"
        )

        st.stop()

    # ----------------------------
    # API key
    # ----------------------------

    if not API_KEY:

        st.error(
            "API key မတွေ့ပါ။ "
            "Streamlit Secrets ထဲမှာ API_KEY ထည့်ပါ။"
        )

        st.stop()

    # ----------------------------
    # Clear previous data
    # ----------------------------

    st.session_state.matches = []
    st.session_state.api_errors = []
    st.session_state.last_request_count = 0

    all_matches = []
    errors = []

    # ----------------------------
    # API calls
    # ----------------------------

    progress = st.progress(0)

    total = len(selected)

    for index, league in enumerate(selected, start=1):

        with st.spinner(
            f"Loading {league['name']}..."
        ):

            result = fetch_fixtures(
                league,
                season,
                from_date,
                to_date,
            )

        st.session_state.last_request_count += 1

        if result["ok"]:

            data = result.get("data", {})

            response_errors = data.get("errors")

            if response_errors:

                errors.append(
                    {
                        "league": league,
                        "error": format_api_error(result),
                    }
                )

            else:

                fixtures = data.get(
                    "response",
                    [],
                )

                all_matches.extend(fixtures)

        else:

            errors.append(
                {
                    "league": league,
                    "error": format_api_error(result),
                }
            )

        progress.progress(
            int(index / total * 100)
        )

    progress.empty()

    # ----------------------------
    # Save
    # ----------------------------

    st.session_state.matches = all_matches
    st.session_state.api_errors = errors

    st.rerun()


# ============================================================
# MATCH RESULTS
# ============================================================

st.header("📋 Match Results")

matches = st.session_state.matches

if not matches:

    st.info(
        "No match data loaded yet."
    )

else:

    st.success(
        f"{len(matches)} matches loaded."
    )

    # Sort by fixture date
    matches = sorted(
        matches,
        key=lambda x: x.get(
            "fixture",
            {}
        ).get(
            "date",
            ""
        ),
    )

    for match in matches:

        render_match(match)


# ============================================================
# API ERRORS
# ============================================================

errors = st.session_state.api_errors

if errors:

    st.header("⚠️ League / API Errors")

    for item in errors:

        league = item["league"]

        st.markdown(
            f"""
            <div class="error-card">

                <h3>
                    ❌ {league["name"]}
                </h3>

                <div class="small">
                    Country: {league["country"]}
                    <br>
                    League ID: {league["id"]}
                    <br>
                    Season requested: {season}
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
# FREE PLAN NOTE
# ============================================================

st.header("ℹ️ Free Plan Information")

st.markdown(
    """
    <div class="warning-card">

        <b>API-Football Free Plan</b>

        <br><br>

        • Daily request quota ကန့်သတ်ထားပါတယ်။<br>
        • Available seasons ကလည်း Free plan အတွက် ကန့်သတ်ထားပါတယ်။<br>
        • League Search / Filter / Select တွေက API request မစားပါ။<br>
        • GET MATCHES နှိပ်တဲ့အချိန်မှာသာ API request ပို့ပါတယ်။<br>
        • League တစ်ခု error ဖြစ်ရင် အခြား League တွေကို မပျက်စီးစေဘဲ ဆက်လုပ်ပါတယ်။

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Football Prematch Dashboard • API-Football"
)
