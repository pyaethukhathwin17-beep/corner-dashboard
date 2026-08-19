import streamlit as st
import requests
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
import pandas as pd

# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="Football Match Finder",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_BASE = "https://v3.football.api-sports.io"
MYANMAR_TZ = ZoneInfo("Asia/Yangon")

# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #0b0e14;
        color: #f4f6f8;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #9aa4b2;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .card {
        background: #171c25;
        border: 1px solid #303846;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 18px;
    }

    .card-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .blue-card {
        background: #172a42;
        border-radius: 16px;
        padding: 18px;
        margin: 15px 0;
    }

    .success-card {
        background: #142b20;
        border: 1px solid #2f6b4a;
        border-radius: 16px;
        padding: 18px;
        margin: 15px 0;
    }

    .warning-card {
        background: #3b3b0d;
        border: 1px solid #676719;
        border-radius: 16px;
        padding: 18px;
        margin: 15px 0;
    }

    .error-card {
        background: #3a1d22;
        border: 1px solid #7a343e;
        border-radius: 16px;
        padding: 18px;
        margin: 15px 0;
    }

    .match-card {
        background: #151a22;
        border: 1px solid #303846;
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 14px;
    }

    .team {
        font-size: 19px;
        font-weight: 700;
    }

    .league-name {
        color: #8db8ff;
        font-size: 14px;
        font-weight: 600;
    }

    .kickoff {
        font-size: 20px;
        font-weight: 800;
    }

    .small {
        color: #9aa4b2;
        font-size: 13px;
    }

    div[data-testid="stSelectbox"] label {
        font-weight: 700;
    }

    div[data-testid="stTextInput"] label {
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SESSION STATE
# ============================================================

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "league_results" not in st.session_state:
    st.session_state.league_results = []

if "selected_league" not in st.session_state:
    st.session_state.selected_league = None

if "matches" not in st.session_state:
    st.session_state.matches = []

if "last_search" not in st.session_state:
    st.session_state.last_search = ""

if "api_remaining" not in st.session_state:
    st.session_state.api_remaining = None

# ============================================================
# API KEY
# ============================================================

def get_api_key():
    """
    Priority:
    1. Streamlit secrets
    2. Session state
    3. User input
    """

    key = ""

    try:
        key = st.secrets.get("API_FOOTBALL_KEY", "")
    except Exception:
        key = ""

    if key:
        return key

    return st.session_state.api_key


# ============================================================
# API REQUEST
# ============================================================

def api_get(endpoint, params=None):
    """
    Safe API-Football GET request.

    Returns:
        data, headers, error
    """

    api_key = get_api_key()

    if not api_key:
        return None, {}, "API key မထည့်ရသေးပါ။"

    url = f"{API_BASE}/{endpoint}"

    headers = {
        "x-apisports-key": api_key,
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params or {},
            timeout=25,
        )

    except requests.exceptions.Timeout:
        return None, {}, "API request timeout ဖြစ်သွားပါတယ်။"

    except requests.exceptions.ConnectionError:
        return None, {}, "API server ကို ချိတ်ဆက်မရပါ။ Internet connection စစ်ပါ။"

    except Exception as e:
        return None, {}, f"Request error: {str(e)}"

    remaining = response.headers.get(
        "x-ratelimit-requests-remaining"
    )

    if remaining is not None:
        st.session_state.api_remaining = remaining

    try:
        data = response.json()
    except Exception:
        data = {}

    # --------------------------------------------------------
    # HTTP errors
    # --------------------------------------------------------

    if response.status_code == 429:
        return (
            None,
            response.headers,
            "API quota / rate limit ကျော်သွားပါတယ်။ "
            "ခဏစောင့်ပြီး ပြန်စမ်းပါ။",
        )

    if response.status_code >= 400:
        error_text = ""

        if isinstance(data, dict):
            error_text = str(data.get("errors", ""))

        return (
            None,
            response.headers,
            f"API HTTP {response.status_code}: {error_text}",
        )

    # --------------------------------------------------------
    # API internal errors
    # --------------------------------------------------------

    if isinstance(data, dict):

        errors = data.get("errors")

        if errors:
            return (
                None,
                response.headers,
                f"API error: {errors}",
            )

    return data, response.headers, None


# ============================================================
# MMT TIME
# ============================================================

def now_mmt():
    return datetime.now(MYANMAR_TZ)


def get_mmt_search_window():
    """
    EXACT WINDOW:

    Today 12:00 PM MMT
        ->
    Tomorrow 12:00 PM MMT
    """

    now = now_mmt()

    today = now.date()

    start_dt = datetime.combine(
        today,
        time(12, 0),
        tzinfo=MYANMAR_TZ,
    )

    end_dt = start_dt + timedelta(days=1)

    return start_dt, end_dt


# ============================================================
# CURRENT SEASON
# ============================================================

def guess_current_season():
    """
    API-Football season is represented by starting year.

    Example:
        2025/26 = 2025
        2026/27 = 2026

    This is only a default suggestion.
    """

    now = now_mmt()

    return now.year


# ============================================================
# SEARCH LEAGUES
# ============================================================

def search_leagues(search_text):
    """
    Search API-Football league catalogue.

    IMPORTANT:
    We DO NOT send season=current here.

    This prevents the previous:
        Free plans do not have access to this season
    error from breaking the League Filter.
    """

    search_text = search_text.strip()

    if len(search_text) < 3:
        return [], "အနည်းဆုံး စာလုံး 3 လုံး ရိုက်ပါ။"

    data, headers, error = api_get(
        "leagues",
        {
            "search": search_text,
        },
    )

    if error:
        return [], error

    if not data:
        return [], "API response မရပါ။"

    response = data.get("response", [])

    results = []

    for item in response:

        league = item.get("league", {})
        country = item.get("country", {})

        league_id = league.get("id")
        league_name = league.get("name")
        league_type = league.get("type")
        country_name = country.get("name")

        if league_id is None or not league_name:
            continue

        seasons = item.get("seasons", [])

        season_years = []

        for s in seasons:
            year = s.get("year")

            if year is not None:
                season_years.append(year)

        season_years = sorted(
            list(set(season_years)),
            reverse=True,
        )

        results.append(
            {
                "id": league_id,
                "name": league_name,
                "country": country_name or "",
                "type": league_type or "",
                "seasons": season_years,
            }
        )

    # Remove duplicates
    unique = {}

    for r in results:
        key = (r["id"], r["name"])

        if key not in unique:
            unique[key] = r

    results = list(unique.values())

    results.sort(
        key=lambda x: (
            x["name"].lower(),
            x["country"].lower(),
        )
    )

    return results, None


# ============================================================
# POPULAR LEAGUES
# ============================================================

POPULAR_LEAGUES = [
    {
        "id": 39,
        "name": "Premier League",
        "country": "England",
    },
    {
        "id": 140,
        "name": "La Liga",
        "country": "Spain",
    },
    {
        "id": 78,
        "name": "Bundesliga",
        "country": "Germany",
    },
    {
        "id": 135,
        "name": "Serie A",
        "country": "Italy",
    },
    {
        "id": 61,
        "name": "Ligue 1",
        "country": "France",
    },
    {
        "id": 88,
        "name": "Eredivisie",
        "country": "Netherlands",
    },
    {
        "id": 94,
        "name": "Primeira Liga",
        "country": "Portugal",
    },
    {
        "id": 203,
        "name": "Süper Lig",
        "country": "Turkey",
    },
    {
        "id": 119,
        "name": "Superliga",
        "country": "Denmark",
    },
    {
        "id": 103,
        "name": "Eliteserien",
        "country": "Norway",
    },
    {
        "id": 113,
        "name": "Allsvenskan",
        "country": "Sweden",
    },
    {
        "id": 106,
        "name": "Ekstraklasa",
        "country": "Poland",
    },
    {
        "id": 188,
        "name": "A-League",
        "country": "Australia",
    },
    {
        "id": 253,
        "name": "Major League Soccer",
        "country": "USA",
    },
    {
        "id": 262,
        "name": "Liga MX",
        "country": "Mexico",
    },
    {
        "id": 307,
        "name": "Saudi Pro League",
        "country": "Saudi Arabia",
    },
    {
        "id": 98,
        "name": "J1 League",
        "country": "Japan",
    },
    {
        "id": 292,
        "name": "K League 1",
        "country": "South Korea",
    },
    {
        "id": 71,
        "name": "Serie A",
        "country": "Brazil",
    },
    {
        "id": 128,
        "name": "Liga Profesional Argentina",
        "country": "Argentina",
    },
    {
        "id": 2,
        "name": "UEFA Champions League",
        "country": "World",
    },
    {
        "id": 3,
        "name": "UEFA Europa League",
        "country": "World",
    },
    {
        "id": 848,
        "name": "UEFA Europa Conference League",
        "country": "World",
    },
]

# ============================================================
# FORMAT LEAGUE OPTION
# ============================================================

def league_label(item):

    if item.get("country"):
        return (
            f'{item["name"]} — '
            f'{item["country"]} '
            f'(ID {item["id"]})'
        )

    return (
        f'{item["name"]} '
        f'(ID {item["id"]})'
    )


# ============================================================
# GET FIXTURES
# ============================================================

def get_fixtures_for_window(
    league_id,
    season,
    start_dt,
    end_dt,
):
    """
    Query two calendar dates because our actual window is:

        today 12:00 MMT
        ->
        tomorrow 12:00 MMT

    API-Football returns fixture timestamps using the requested
    timezone.
    """

    start_date = start_dt.date()
    end_date = end_dt.date()

    all_matches = []

    dates_to_query = [
        start_date,
        end_date,
    ]

    for d in dates_to_query:

        params = {
            "league": league_id,
            "season": season,
            "date": d.isoformat(),
            "timezone": "Asia/Yangon",
        }

        data, headers, error = api_get(
            "fixtures",
            params,
        )

        if error:
            return [], error

        if not data:
            continue

        response = data.get("response", [])

        all_matches.extend(response)

    # --------------------------------------------------------
    # Remove duplicate fixture IDs
    # --------------------------------------------------------

    unique = {}

    for match in all_matches:

        fixture = match.get("fixture", {})

        fixture_id = fixture.get("id")

        if fixture_id is not None:
            unique[fixture_id] = match

    all_matches = list(unique.values())

    # --------------------------------------------------------
    # EXACT MMT WINDOW FILTER
    # --------------------------------------------------------

    filtered = []

    for match in all_matches:

        fixture = match.get("fixture", {})

        fixture_date = fixture.get("date")

        if not fixture_date:
            continue

        try:
            dt = datetime.fromisoformat(
                fixture_date.replace(
                    "Z",
                    "+00:00",
                )
            )

            # API already returned Asia/Yangon timezone,
            # but normalize again for safety.
            dt_mmt = dt.astimezone(MYANMAR_TZ)

        except Exception:
            continue

        if start_dt <= dt_mmt < end_dt:

            match["_mmt_datetime"] = dt_mmt

            filtered.append(match)

    filtered.sort(
        key=lambda x: x["_mmt_datetime"]
    )

    return filtered, None


# ============================================================
# MATCH STATUS
# ============================================================

def get_status_text(match):

    status = (
        match
        .get("fixture", {})
        .get("status", {})
    )

    short = status.get("short", "")
    long_text = status.get("long", "")

    if short == "NS":
        return "NOT STARTED"

    if short == "TBD":
        return "TIME TBD"

    if short in ["1H", "HT", "2H", "ET", "BT", "P"]:
        return f"LIVE — {long_text}"

    if short in ["FT", "AET", "PEN"]:
        return f"FINISHED — {long_text}"

    if short == "PST":
        return "POSTPONED"

    if short == "CANC":
        return "CANCELLED"

    return long_text or short or "UNKNOWN"


# ============================================================
# MATCH CARD
# ============================================================

def render_match(match):

    fixture = match.get("fixture", {})
    league = match.get("league", {})
    teams = match.get("teams", {})
    goals = match.get("goals", {})

    home = teams.get("home", {})
    away = teams.get("away", {})

    home_name = home.get("name", "Home")
    away_name = away.get("name", "Away")

    home_logo = home.get("logo", "")
    away_logo = away.get("logo", "")

    league_name = league.get(
        "name",
        "Unknown League",
    )

    country = league.get(
        "country",
        "",
    )

    fixture_id = fixture.get(
        "id",
        "",
    )

    dt_mmt = match.get(
        "_mmt_datetime"
    )

    if dt_mmt:

        date_text = dt_mmt.strftime(
            "%Y-%m-%d"
        )

        time_text = dt_mmt.strftime(
            "%I:%M %p"
        )

    else:

        date_text = "-"
        time_text = "-"

    status = get_status_text(match)

    home_score = goals.get("home")
    away_score = goals.get("away")

    score_text = ""

    if home_score is not None or away_score is not None:

        home_score = (
            "-" if home_score is None
            else str(home_score)
        )

        away_score = (
            "-" if away_score is None
            else str(away_score)
        )

        score_text = (
            f'<div class="kickoff">'
            f'{home_score} : {away_score}'
            f'</div>'
        )

    else:

        score_text = (
            '<div class="small">'
            'PRE-MATCH'
            '</div>'
        )

    st.markdown(
        f"""
        <div class="match-card">

            <div class="league-name">
                🏆 {league_name}
                {" — " + country if country else ""}
            </div>

            <div style="margin-top:10px;">
                <span class="small">
                    Fixture ID: {fixture_id}
                </span>
            </div>

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:20px;
                margin-top:14px;
            ">

                <div style="flex:1;">
                    {
                        f'<img src="{home_logo}" width="35">'
                        if home_logo else ""
                    }
                    <span class="team">
                        {home_name}
                    </span>
                </div>

                <div style="
                    text-align:center;
                    min-width:100px;
                ">

                    <div class="small">
                        {date_text} MMT
                    </div>

                    {score_text}

                    <div class="small">
                        {time_text}
                    </div>

                </div>

                <div style="
                    flex:1;
                    text-align:right;
                ">

                    <span class="team">
                        {away_name}
                    </span>

                    {
                        f'<img src="{away_logo}" width="35">'
                        if away_logo else ""
                    }

                </div>

            </div>

            <div style="
                margin-top:14px;
                color:#9aa4b2;
                font-size:13px;
            ">
                Status: {status}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">⚽ Football Match Finder</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Myanmar Time based pre-match fixture search'
    '</div>',
    unsafe_allow_html=True,
)

# ============================================================
# API KEY SECTION
# ============================================================

with st.expander(
    "🔐 API KEY",
    expanded=False,
):

    secret_key = ""

    try:
        secret_key = st.secrets.get(
            "API_FOOTBALL_KEY",
            "",
        )
    except Exception:
        pass

    if secret_key:

        st.success(
            "API key ကို Streamlit Secrets ကနေ ရရှိထားပါတယ်။"
        )

        st.session_state.api_key = secret_key

    else:

        typed_key = st.text_input(
            "API-Football API Key",
            type="password",
            value=st.session_state.api_key,
            placeholder="x-apisports-key",
        )

        if typed_key:
            st.session_state.api_key = typed_key.strip()

        st.caption(
            "API key ကို code ထဲ hard-code မလုပ်ထားပါ။"
        )


# ============================================================
# STATUS BAR
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.markdown(
        """
        <div class="card">
            <div class="card-title">⚙️ MODE</div>
            <div>MULTI_LEAGUE_PREMATCH</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:

    start_dt, end_dt = get_mmt_search_window()

    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">🕛 MMT SEARCH WINDOW</div>
            <div>
                {start_dt.strftime("%Y-%m-%d %I:%M %p")}
                →
                {end_dt.strftime("%Y-%m-%d %I:%M %p")}
                MMT
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:

    remaining = st.session_state.api_remaining

    remaining_text = (
        str(remaining)
        if remaining is not None
        else "Not reported"
    )

    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">🛡️ API SAFETY</div>
            <div>Remaining: {remaining_text}</div>
            <div>Timezone: Asia/Yangon</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LEAGUE FILTER
# ============================================================

st.markdown(
    "## 🏆 League Filter"
)

st.markdown(
    """
    <div class="subtitle">
        Search league name → select league → select season → get matches
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Popular league quick selector
# ------------------------------------------------------------

st.markdown("### ⭐ Popular Leagues")

popular_labels = [
    league_label(x)
    for x in POPULAR_LEAGUES
]

popular_choice = st.selectbox(
    "Quick select",
    ["— Select from popular leagues —"]
    + popular_labels,
    index=0,
)

if popular_choice != "— Select from popular leagues —":

    selected_index = (
        popular_labels.index(
            popular_choice
        )
    )

    st.session_state.selected_league = (
        POPULAR_LEAGUES[selected_index]
        .copy()
    )


# ------------------------------------------------------------
# Search League
# ------------------------------------------------------------

st.markdown("### 🔎 Search League")

search_col1, search_col2 = st.columns(
    [4, 1]
)

with search_col1:

    search_text = st.text_input(
        "Search league",
        value=st.session_state.last_search,
        placeholder=(
            "Premier League / Bundesliga / "
            "Champions League / Serie A..."
        ),
        label_visibility="collapsed",
    )

with search_col2:

    search_clicked = st.button(
        "🔎 Search",
        use_container_width=True,
    )

if search_clicked:

    if not st.session_state.api_key:

        st.error(
            "API key ထည့်ပြီးမှ League Search လုပ်ပါ။"
        )

    elif len(search_text.strip()) < 3:

        st.warning(
            "League name အနည်းဆုံး 3 လုံး ရိုက်ပါ။"
        )

    else:

        with st.spinner(
            "League catalogue ရှာနေပါတယ်..."
        ):

            results, error = search_leagues(
                search_text
            )

        if error:

            st.session_state.league_results = []

            st.error(error)

        else:

            st.session_state.league_results = results
            st.session_state.last_search = (
                search_text
            )

            if results:

                st.success(
                    f"{len(results)} leagues found."
                )

            else:

                st.warning(
                    "ဒီနာမည်နဲ့ League မတွေ့ပါ။"
                )


# ------------------------------------------------------------
# Search results selector
# ------------------------------------------------------------

if st.session_state.league_results:

    st.markdown(
        "### 📋 Search Results"
    )

    result_labels = [
        league_label(x)
        for x in st.session_state.league_results
    ]

    selected_result_label = st.selectbox(
        "Choose league",
        result_labels,
        key="search_result_select",
    )

    selected_result_index = (
        result_labels.index(
            selected_result_label
        )
    )

    st.session_state.selected_league = (
        st.session_state.league_results[
            selected_result_index
        ]
    )


# ============================================================
# SELECTED LEAGUE
# ============================================================

selected_league = st.session_state.selected_league

if selected_league:

    st.markdown(
        "### ✅ Selected League"
    )

    st.markdown(
        f"""
        <div class="blue-card">

            <div style="
                font-size:24px;
                font-weight:800;
            ">
                🏆 {selected_league["name"]}
            </div>

            <div style="
                margin-top:8px;
                color:#9aa4b2;
            ">
                Country: {selected_league.get("country", "-")}
                <br>
                League ID: {selected_league["id"]}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # SEASON
    # ========================================================

    st.markdown(
        "### 📅 Season"
    )

    available_seasons = (
        selected_league.get(
            "seasons",
            []
        )
    )

    # If search result contains seasons
    if available_seasons:

        # Put current year first if available
        default_season = guess_current_season()

        season_options = available_seasons.copy()

        if default_season in season_options:

            default_index = season_options.index(
                default_season
            )

        else:

            default_index = 0

    else:

        # Popular local league doesn't have
        # season metadata.
        #
        # We still allow manual season selection.
        season_options = list(
            range(
                guess_current_season(),
                2019,
                -1,
            )
        )

        default_index = 0

    season = st.selectbox(
        "API season",
        season_options,
        index=default_index,
        format_func=lambda x: (
            f"{x}/{str(x + 1)[-2:]}"
        ),
    )

    st.caption(
        "ဥပမာ 2025 ဆိုရင် 2025/26 season ကို ဆိုလိုပါတယ်။"
    )

    # ========================================================
    # FREE PLAN NOTICE
    # ========================================================

    if season >= 2025:

        st.warning(
            "⚠️ သင့် screenshot အရ Free plan ဖြစ်နေပါတယ်။ "
            "Free plan က season access ကို ကန့်သတ်ထားနိုင်ပါတယ်။ "
            "2025/26 သို့မဟုတ် 2026/27 ကို API က ပယ်ချရင် "
            "code ပြဿနာမဟုတ်ဘဲ plan restriction ဖြစ်ပါတယ်။"
        )

    # ========================================================
    # SEARCH WINDOW
    # ========================================================

    st.markdown(
        "### 🕛 Myanmar Time Search Window"
    )

    start_dt, end_dt = (
        get_mmt_search_window()
    )

    st.markdown(
        f"""
        <div class="success-card">

            <b>START</b><br>
            {start_dt.strftime("%Y-%m-%d %I:%M %p")}
            MMT

            <br><br>

            <b>END</b><br>
            {end_dt.strftime("%Y-%m-%d %I:%M %p")}
            MMT

            <br><br>

            <b>Timezone</b><br>
            Asia/Yangon

        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # GET MATCHES BUTTON
    # ========================================================

    get_matches_clicked = st.button(
        "⚽ GET MATCHES",
        type="primary",
        use_container_width=True,
    )

    if get_matches_clicked:

        if not st.session_state.api_key:

            st.error(
                "API key မရှိပါ။"
            )

        else:

            with st.spinner(
                "Myanmar Time 12 PM → နောက်နေ့ 12 PM "
                "အတွင်းက matches ရှာနေပါတယ်..."
            ):

                matches, error = (
                    get_fixtures_for_window(
                        league_id=selected_league["id"],
                        season=season,
                        start_dt=start_dt,
                        end_dt=end_dt,
                    )
                )

            if error:

                st.session_state.matches = []

                error_text = str(error)

                # --------------------------------------------
                # Season restriction
                # --------------------------------------------

                if (
                    "Free plans" in error_text
                    or "season" in error_text.lower()
                ):

                    st.markdown(
                        f"""
                        <div class="error-card">

                            <h3>
                                ❌ API Season Access Error
                            </h3>

                            <p>
                                {error_text}
                            </p>

                            <p>
                                ဒီဟာက Streamlit / League Filter
                                error မဟုတ်ပါ။
                            </p>

                            <p>
                                API Free plan က ဒီ season ကို
                                access မပေးတာ ဖြစ်ပါတယ်။
                            </p>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                else:

                    st.error(
                        error_text
                    )

            else:

                st.session_state.matches = matches

                if matches:

                    st.success(
                        f"{len(matches)} matches found."
                    )

                else:

                    st.info(
                        "ဒီ 12 PM MMT → နောက်နေ့ 12 PM MMT "
                        "window အတွင်းမှာ match မတွေ့ပါ။"
                    )


# ============================================================
# MATCH RESULTS
# ============================================================

matches = st.session_state.matches

if matches:

    st.markdown(
        "## ⚽ Match Results"
    )

    st.markdown(
        f"""
        <div class="blue-card">
            <b>SEARCH WINDOW</b><br>
            {start_dt.strftime("%Y-%m-%d %I:%M %p")}
            →
            {end_dt.strftime("%Y-%m-%d %I:%M %p")}
            MMT

            <br><br>

            <b>TOTAL MATCHES</b><br>
            {len(matches)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    for match in matches:

        render_match(match)


# ============================================================
# DATA TABLE
# ============================================================

if matches:

    st.markdown(
        "## 📊 Match Table"
    )

    table_rows = []

    for match in matches:

        fixture = match.get(
            "fixture",
            {}
        )

        league = match.get(
            "league",
            {}
        )

        teams = match.get(
            "teams",
            {}
        )

        goals = match.get(
            "goals",
            {}
        )

        dt_mmt = match.get(
            "_mmt_datetime"
        )

        table_rows.append(
            {
                "Fixture ID": fixture.get(
                    "id"
                ),
                "Date MMT": (
                    dt_mmt.strftime(
                        "%Y-%m-%d"
                    )
                    if dt_mmt
                    else ""
                ),
                "Time MMT": (
                    dt_mmt.strftime(
                        "%I:%M %p"
                    )
                    if dt_mmt
                    else ""
                ),
                "League": league.get(
                    "name",
                    "",
                ),
                "Home": teams.get(
                    "home",
                    {}
                ).get(
                    "name",
                    "",
                ),
                "Away": teams.get(
                    "away",
                    {}
                ).get(
                    "name",
                    "",
                ),
                "Home Goals": goals.get(
                    "home"
                ),
                "Away Goals": goals.get(
                    "away"
                ),
                "Status": get_status_text(
                    match
                ),
            }
        )

    df = pd.DataFrame(
        table_rows
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# FOOTER / HELP
# ============================================================

st.markdown("---")

with st.expander(
    "ℹ️ ဒီ App ဘယ်လိုအလုပ်လုပ်သလဲ?"
):

    st.markdown(
        """
### 1. League Search

`Premier League`, `Bundesliga`,
`Champions League`, `Serie A` စသဖြင့်
**3 characters အထက်** ရိုက်ပြီး Search နှိပ်ပါ။

API က League ID ကိုရှာပေးပါမယ်။

---

### 2. League ID ကို Manual ရှာစရာ မလိုပါ

ဥပမာ:

`Premier League`

→ API Search

→ `Premier League — England (ID 39)`

→ ရွေး

ဒီလိုဖြစ်ပါတယ်။

---

### 3. Season

League ID နဲ့ Season ကို သီးခြားအသုံးပြုပါတယ်။

ဥပမာ:

`Premier League`

League ID = `39`

`2025`

ဆိုရင်

`2025/26`

season ဖြစ်ပါတယ်။

---

### 4. Myanmar Time

App က

**ဒီနေ့ 12:00 PM MMT**

မှ

**နောက်နေ့ 12:00 PM MMT**

အထိကို exact window အဖြစ်သတ်မှတ်ပါတယ်။

---

### 5. API Timezone

API request ထဲမှာ

`timezone=Asia/Yangon`

ကို အသုံးပြုထားပါတယ်။

ဒါကြောင့် match kickoff ကို
Myanmar Standard Time အဖြစ် ရယူပြီး
နောက်ဆုံးမှာ code က exact window ထပ်စစ်ပါတယ်။

---

### 6. Free Plan

API-Football Free plan မှာ
daily request limit ရှိပြီး
season access လည်း ကန့်သတ်ထားနိုင်ပါတယ်။

ဒါကြောင့် API က

`Free plans do not have access to this season`

လို့ ပြန်လာရင်
League Filter ကို ထပ်မပြင်ပါနဲ့။

အဲဒါက API plan restriction ဖြစ်ပါတယ်။
        """
    )

st.caption(
    "Football Match Finder • Asia/Yangon • API-Football"
)
