import streamlit as st
import requests
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Football Match Finder",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_URL = "https://v3.football.api-sports.io"
MMT = ZoneInfo("Asia/Yangon")

# =========================================================
# CSS
# =========================================================

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
        color: #f4f6fa !important;
    }

    .title {
        font-size: 46px;
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
        margin: 12px 0;
    }

    .info-card {
        background: #192b45;
        border-radius: 16px;
        padding: 18px;
        margin: 10px 0;
    }

    .success-card {
        background: #123523;
        border: 1px solid #2d7950;
        border-radius: 16px;
        padding: 18px;
        margin: 12px 0;
    }

    .warning-card {
        background: #3b3e0d;
        border-radius: 16px;
        padding: 18px;
        margin: 12px 0;
        color: #fff7a6;
    }

    .error-card {
        background: #3a1d23;
        border: 1px solid #81404d;
        border-radius: 16px;
        padding: 18px;
        margin: 12px 0;
    }

    .league-item {
        background: #171c25;
        border: 1px solid #303846;
        border-radius: 14px;
        padding: 15px;
        margin: 8px 0;
    }

    .league-name {
        font-size: 20px;
        font-weight: 700;
    }

    .league-meta {
        color: #9aa4b2;
        font-size: 14px;
        margin-top: 5px;
    }

    .match-card {
        background: #151a22;
        border: 1px solid #303846;
        border-radius: 18px;
        padding: 18px;
        margin: 12px 0;
    }

    .team {
        font-size: 20px;
        font-weight: 700;
    }

    .kickoff {
        color: #62a5ff;
        font-size: 17px;
        font-weight: 700;
    }

    .small {
        color: #9aa4b2;
        font-size: 14px;
    }

    div[data-testid="stButton"] > button {
        border-radius: 12px;
        min-height: 45px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# API FUNCTIONS
# =========================================================

def get_api_key():
    """
    Priority:
    1. Streamlit secrets
    2. Sidebar input
    """

    key = ""

    try:
        key = st.secrets.get("API_FOOTBALL_KEY", "")
    except Exception:
        key = ""

    return key.strip()


def api_headers(api_key):
    return {
        "x-apisports-key": api_key,
        "Accept": "application/json",
    }


def api_get(endpoint, params, api_key, timeout=30):
    """
    Central API request function.
    """

    url = f"{API_URL}/{endpoint}"

    try:
        response = requests.get(
            url,
            headers=api_headers(api_key),
            params=params,
            timeout=timeout,
        )

        # Try JSON regardless of status
        try:
            data = response.json()
        except Exception:
            data = {
                "errors": {
                    "http": f"HTTP {response.status_code}"
                }
            }

        return response.status_code, data

    except requests.exceptions.Timeout:
        return 0, {
            "errors": {
                "timeout": "API request timed out."
            }
        }

    except requests.exceptions.RequestException as e:
        return 0, {
            "errors": {
                "network": str(e)
            }
        }


def extract_api_error(data):
    errors = data.get("errors", {})

    if not errors:
        return ""

    if isinstance(errors, dict):
        parts = []

        for key, value in errors.items():
            parts.append(f"{key}: {value}")

        return " | ".join(parts)

    return str(errors)


# =========================================================
# LEAGUE CATALOGUE
# =========================================================

@st.cache_data(ttl=3600, show_spinner=False)
def load_current_leagues(api_key):
    """
    Load current competitions from API.

    Important:
    We DO NOT request season=2026 here.
    This avoids the Free-plan season restriction during
    the league catalogue stage.
    """

    status, data = api_get(
        "leagues",
        {
            "current": "true"
        },
        api_key,
    )

    if status != 200:
        return {
            "ok": False,
            "error": extract_api_error(data),
            "status": status,
            "response": [],
        }

    error = extract_api_error(data)

    if error:
        return {
            "ok": False,
            "error": error,
            "status": status,
            "response": [],
        }

    response = data.get("response", [])

    if not isinstance(response, list):
        response = []

    return {
        "ok": True,
        "error": "",
        "status": status,
        "response": response,
    }


def normalize_leagues(raw):
    """
    Convert API response to clean catalogue.
    """

    result = []

    for item in raw:

        league = item.get("league", {})
        country = item.get("country", {})
        seasons = item.get("seasons", [])

        league_id = league.get("id")
        name = league.get("name", "Unknown League")
        league_type = league.get("type", "")

        country_name = country.get("name", "World")

        current_season = None
        coverage = {}

        # Find current season if API marks it
        for s in seasons:
            if s.get("current") is True:
                current_season = s.get("year")
                coverage = s.get("coverage", {}) or {}
                break

        # fallback
        if current_season is None and seasons:
            current_season = seasons[0].get("year")
            coverage = seasons[0].get("coverage", {}) or {}

        if league_id is None:
            continue

        result.append(
            {
                "id": int(league_id),
                "name": str(name),
                "country": str(country_name),
                "type": str(league_type),
                "season": current_season,
                "coverage": coverage,
                "logo": league.get("logo", ""),
            }
        )

    # Remove duplicates
    unique = {}

    for x in result:
        key = (
            x["id"],
            x["name"],
            x["country"],
        )

        unique[key] = x

    result = list(unique.values())

    result.sort(
        key=lambda x: (
            x["country"].lower(),
            x["name"].lower(),
        )
    )

    return result


# =========================================================
# SEARCH / FILTER
# =========================================================

def filter_leagues(leagues, search_text, country_filter, type_filter):

    search_text = search_text.strip().lower()

    output = []

    for league in leagues:

        if search_text:
            combined = (
                f"{league['name']} "
                f"{league['country']} "
                f"{league['id']}"
            ).lower()

            if search_text not in combined:
                continue

        if country_filter != "All countries":
            if league["country"] != country_filter:
                continue

        if type_filter != "All types":
            if league["type"] != type_filter:
                continue

        output.append(league)

    return output


# =========================================================
# MATCH FUNCTIONS
# =========================================================

def fetch_matches_for_league(
    api_key,
    league_id,
    season,
    from_date,
    to_date,
):
    """
    Fetch fixtures for one league.

    API-Football fixtures supports from/to.
    """

    if season is None:
        return {
            "ok": False,
            "error": "No season information is available for this league.",
            "matches": [],
        }

    params = {
        "league": league_id,
        "season": season,
        "from": from_date,
        "to": to_date,
        "timezone": "Asia/Yangon",
    }

    status, data = api_get(
        "fixtures",
        params,
        api_key,
    )

    if status != 200:
        return {
            "ok": False,
            "error": extract_api_error(data),
            "status": status,
            "matches": [],
        }

    error = extract_api_error(data)

    if error:
        return {
            "ok": False,
            "error": error,
            "status": status,
            "matches": [],
        }

    return {
        "ok": True,
        "error": "",
        "status": status,
        "matches": data.get("response", []) or [],
    }


# =========================================================
# MATCH DISPLAY
# =========================================================

def display_match(match, league_name):

    fixture = match.get("fixture", {})
    teams = match.get("teams", {})
    goals = match.get("goals", {})

    fixture_id = fixture.get("id", "-")

    home = teams.get("home", {}).get("name", "Home")
    away = teams.get("away", {}).get("name", "Away")

    home_logo = teams.get("home", {}).get("logo", "")
    away_logo = teams.get("away", {}).get("logo", "")

    status = fixture.get("status", {})
    status_short = status.get("short", "NS")
    status_long = status.get("long", "")

    date_string = fixture.get("date")

    kickoff = "Unknown"

    if date_string:
        try:
            dt = datetime.fromisoformat(
                date_string.replace("Z", "+00:00")
            )

            dt = dt.astimezone(MMT)

            kickoff = dt.strftime(
                "%Y-%m-%d %I:%M %p MMT"
            )

        except Exception:
            kickoff = date_string

    home_goals = goals.get("home")
    away_goals = goals.get("away")

    score = ""

    if home_goals is not None or away_goals is not None:
        score = f"{home_goals} - {away_goals}"

    venue = fixture.get("venue", {}) or {}
    venue_name = venue.get("name", "")

    referee = fixture.get("referee", "")

    html = f"""
    <div class="match-card">

        <div class="small">
            {league_name} &nbsp; | &nbsp; Fixture ID: {fixture_id}
        </div>

        <div style="margin-top:10px;" class="kickoff">
            🕒 {kickoff}
        </div>

        <div style="margin-top:15px; text-align:center;">
            <div class="team">
                {home}
            </div>

            <div style="
                font-size:25px;
                font-weight:800;
                margin:8px 0;
            ">
                {score if score else "VS"}
            </div>

            <div class="team">
                {away}
            </div>
        </div>

        <div style="margin-top:15px;" class="small">
            Status: {status_short} — {status_long}
        </div>

        <div class="small">
            Venue: {venue_name if venue_name else "N/A"}
        </div>

        <div class="small">
            Referee: {referee if referee else "N/A"}
        </div>

    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

    with st.expander("📦 Raw JSON"):
        st.json(match)


# =========================================================
# SESSION STATE
# =========================================================

if "selected_leagues" not in st.session_state:
    st.session_state.selected_leagues = {}

if "league_catalogue" not in st.session_state:
    st.session_state.league_catalogue = []

if "matches" not in st.session_state:
    st.session_state.matches = []

if "match_errors" not in st.session_state:
    st.session_state.match_errors = []

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Settings")

    secret_key = get_api_key()

    if secret_key:
        st.success("API key loaded from Streamlit Secrets.")

        api_key = secret_key

    else:
        api_key = st.text_input(
            "API-Football API Key",
            type="password",
            placeholder="Paste your x-apisports-key here",
            help="Your API key is not displayed.",
        ).strip()

    st.divider()

    st.caption(
        "API-Football Free plan has a daily request limit. "
        "Use Refresh / Get Matches only when needed."
    )

# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="title">⚽ Football Match Finder</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
    Search leagues from the API catalogue, select the leagues you want,
    then retrieve matches using Myanmar Standard Time (MMT).
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# API KEY CHECK
# =========================================================

if not api_key:

    st.markdown(
        """
        <div class="warning-card">
        ⚠️ API Key မထည့်ရသေးပါ။<br><br>
        Sidebar မှာ API-Football API Key ထည့်ပါ။
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()

# =========================================================
# LOAD LEAGUES
# =========================================================

st.markdown("## 🏆 Search League")

col1, col2 = st.columns([3, 1])

with col1:

    load_button = st.button(
        "🔄 LOAD / REFRESH LEAGUE LIST",
        use_container_width=True,
    )

with col2:

    clear_button = st.button(
        "🗑️ CLEAR",
        use_container_width=True,
    )

if clear_button:
    st.session_state.selected_leagues = {}
    st.session_state.matches = []
    st.session_state.match_errors = []
    st.rerun()


if load_button or not st.session_state.league_catalogue:

    with st.spinner("League catalogue ကို API ကနေယူနေပါတယ်..."):

        league_result = load_current_leagues(api_key)

    if not league_result["ok"]:

        st.markdown(
            f"""
            <div class="error-card">
            ❌ <b>League catalogue မရပါ</b><br><br>
            {league_result["error"]}<br><br>
            HTTP Status: {league_result["status"]}
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.session_state.league_catalogue = normalize_leagues(
            league_result["response"]
        )

        st.success(
            f"✅ {len(st.session_state.league_catalogue)} "
            "competitions loaded."
        )

leagues = st.session_state.league_catalogue

# =========================================================
# LEAGUE SEARCH UI
# =========================================================

if leagues:

    countries = sorted(
        list(
            {
                x["country"]
                for x in leagues
                if x["country"]
            }
        )
    )

    types = sorted(
        list(
            {
                x["type"]
                for x in leagues
                if x["type"]
            }
        )
    )

    c1, c2 = st.columns([2, 1])

    with c1:

        search_text = st.text_input(
            "🔎 Search / Filter",
            placeholder="League name, country, or ID...",
        )

    with c2:

        country_filter = st.selectbox(
            "🌍 Country",
            ["All countries"] + countries,
        )

    type_filter = st.selectbox(
        "🏷️ Competition Type",
        ["All types"] + types,
    )

    filtered = filter_leagues(
        leagues,
        search_text,
        country_filter,
        type_filter,
    )

    st.caption(
        f"Showing {len(filtered)} of {len(leagues)} competitions"
    )

    # -----------------------------------------------------
    # Selectbox
    # -----------------------------------------------------

    if filtered:

        league_options = []

        option_map = {}

        for league in filtered:

            label = (
                f"{league['name']} "
                f"— {league['country']} "
                f"(ID {league['id']})"
            )

            league_options.append(label)
            option_map[label] = league

        selected_label = st.selectbox(
            "🏆 Select League",
            league_options,
            index=None,
            placeholder="Choose a league from the list...",
        )

        if selected_label:

            selected = option_map[selected_label]

            st.markdown(
                f"""
                <div class="info-card">
                <b>Selected League</b><br><br>
                🏆 {selected['name']}<br>
                🌍 {selected['country']}<br>
                🆔 League ID: {selected['id']}<br>
                📅 API Current Season:
                {selected['season'] if selected['season'] else 'N/A'}
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "➕ ADD THIS LEAGUE",
                use_container_width=True,
            ):

                st.session_state.selected_leagues[
                    selected["id"]
                ] = selected

                st.success(
                    f"✅ {selected['name']} added."
                )

    else:

        st.warning(
            "ဒီ filter နဲ့ ကိုက်ညီတဲ့ league မတွေ့ပါ။"
        )

# =========================================================
# SELECTED LEAGUES
# =========================================================

st.markdown("## ✅ Selected Leagues")

selected_leagues = list(
    st.session_state.selected_leagues.values()
)

if not selected_leagues:

    st.info(
        "အပေါ်က League list ထဲက league တစ်ခုရွေးပြီး "
        "ADD THIS LEAGUE နှိပ်ပါ။"
    )

else:

    st.write(
        f"**Selected: {len(selected_leagues)} leagues**"
    )

    for league in selected_leagues:

        col1, col2 = st.columns([5, 1])

        with col1:

            st.markdown(
                f"""
                <div class="league-item">
                    <div class="league-name">
                        🏆 {league['name']}
                    </div>

                    <div class="league-meta">
                        🌍 {league['country']}
                        &nbsp; | &nbsp;
                        🆔 ID {league['id']}
                        &nbsp; | &nbsp;
                        📅 Season {league['season']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:

            if st.button(
                "❌ Remove",
                key=f"remove_{league['id']}",
                use_container_width=True,
            ):

                del st.session_state.selected_leagues[
                    league["id"]
                ]

                st.rerun()

# =========================================================
# SEARCH WINDOW
# =========================================================

st.markdown("## 🕒 Search Window")

st.markdown(
    """
    <div class="info-card">
    🇲🇲 <b>Myanmar Standard Time (MMT)</b><br>
    Match search ကို MMT အချိန်အတိုင်းတွက်ပြီး API ကို date range ပို့ပါမယ်။
    </div>
    """,
    unsafe_allow_html=True,
)

today_mmt = datetime.now(MMT).date()

default_start = today_mmt
default_end = today_mmt + timedelta(days=1)

c1, c2 = st.columns(2)

with c1:

    start_date = st.date_input(
        "Start date (MMT)",
        value=default_start,
        key="start_date",
    )

with c2:

    end_date = st.date_input(
        "End date (MMT)",
        value=default_end,
        key="end_date",
    )

st.markdown(
    f"""
    <div class="success-card">
    🕛 Search Window<br><br>
    <b>
    {start_date.strftime('%Y-%m-%d 12:00 PM MMT')}
    →
    {end_date.strftime('%Y-%m-%d 12:00 PM MMT')}
    </b>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# GET MATCHES
# =========================================================

st.markdown("## ⚽ Get Matches")

if start_date > end_date:

    st.error(
        "Start date က End date ထက် နောက်ကျနေပါတယ်။"
    )

else:

    if st.button(
        "⚽ GET MATCHES",
        type="primary",
        use_container_width=True,
    ):

        if not selected_leagues:

            st.warning(
                "အရင်ဆုံး league တစ်ခု ရွေးပါ။"
            )

        else:

            st.session_state.matches = []
            st.session_state.match_errors = []

            progress = st.progress(0)

            total = len(selected_leagues)

            for index, league in enumerate(
                selected_leagues,
                start=1,
            ):

                with st.spinner(
                    f"Loading {league['name']}..."
                ):

                    result = fetch_matches_for_league(
                        api_key=api_key,
                        league_id=league["id"],
                        season=league["season"],
                        from_date=start_date.strftime(
                            "%Y-%m-%d"
                        ),
                        to_date=end_date.strftime(
                            "%Y-%m-%d"
                        ),
                    )

                if result["ok"]:

                    for match in result["matches"]:

                        st.session_state.matches.append(
                            {
                                "league": league,
                                "match": match,
                            }
                        )

                else:

                    st.session_state.match_errors.append(
                        {
                            "league": league,
                            "error": result["error"],
                        }
                    )

                progress.progress(
                    index / total
                )

            progress.empty()

# =========================================================
# RESULTS
# =========================================================

st.markdown("## 📋 Match Results")

matches = st.session_state.matches

if matches:

    st.success(
        f"✅ Total Matches: {len(matches)}"
    )

    # Sort by kickoff time
    def match_timestamp(item):

        dt_string = item["match"].get(
            "fixture", {}
        ).get("date")

        if not dt_string:
            return ""

        return dt_string

    matches = sorted(
        matches,
        key=match_timestamp,
    )

    for item in matches:

        display_match(
            item["match"],
            item["league"]["name"],
        )

else:

    st.info(
        "No match data loaded yet."
    )

# =========================================================
# API ERRORS
# =========================================================

if st.session_state.match_errors:

    st.markdown("## ⚠️ League/API Errors")

    for item in st.session_state.match_errors:

        league = item["league"]

        error = item["error"]

        st.markdown(
            f"""
            <div class="error-card">

            ❌ <b>{league['name']}</b><br><br>

            League ID: {league['id']}<br>
            Season requested: {league['season']}<br><br>

            API Error:<br>
            {error}

            </div>
            """,
            unsafe_allow_html=True,
        )

# =========================================================
# IMPORTANT API LIMITATION NOTICE
# =========================================================

st.markdown(
    """
    <div class="warning-card">

    ⚠️ <b>Free Plan Season Limitation</b><br><br>

    API-Football Free plan မှာ competition အားလုံးကို
    endpoint အနေနဲ့သုံးလို့ရပေမယ့် available seasons က
    ကန့်သတ်ထားပါတယ်။<br><br>

    ဒါကြောင့် League list ပေါ်လာတာနဲ့
    အဲဒီ league ရဲ့ <b>2026/27 fixtures</b> ကို
    Free plan က အမြဲရမယ်လို့ မဆိုလိုပါဘူး။<br><br>

    အခု code က season error ကို
    League Search error အဖြစ် မပြဘဲ
    သက်ဆိုင်ရာ league အောက်မှာ သီးခြားပြပေးထားပါတယ်။

    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# API STATUS
# =========================================================

with st.expander("🔧 API Status / Debug"):

    st.write(
        "API Host:",
        API_URL,
    )

    st.write(
        "Myanmar Time:",
        datetime.now(MMT).strftime(
            "%Y-%m-%d %I:%M:%S %p MMT"
        ),
    )

    st.write(
        "Loaded Leagues:",
        len(st.session_state.league_catalogue),
    )

    st.write(
        "Selected Leagues:",
        len(st.session_state.selected_leagues),
    )

    st.write(
        "Loaded Matches:",
        len(st.session_state.matches),
    )
