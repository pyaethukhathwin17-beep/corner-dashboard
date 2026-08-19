import streamlit as st
import requests
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

# =========================================================
# APP CONFIG
# =========================================================

st.set_page_config(
    page_title="Football Match Analyzer",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_BASE = "https://v3.football.api-sports.io"
MMT = ZoneInfo("Asia/Yangon")


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #0b0e14;
        color: #f2f5f8;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: #f4f6f8 !important;
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
        background: #171c24;
        border: 1px solid #303846;
        border-radius: 18px;
        padding: 20px;
        margin: 12px 0;
    }

    .info-card {
        background: #17283f;
        border: 1px solid #29415f;
        border-radius: 18px;
        padding: 20px;
        margin: 12px 0;
    }

    .success-card {
        background: #10251b;
        border: 1px solid #2f714b;
        border-radius: 18px;
        padding: 20px;
        margin: 12px 0;
    }

    .warning-card {
        background: #383b12;
        border: 1px solid #696d1e;
        border-radius: 18px;
        padding: 20px;
        margin: 12px 0;
    }

    .error-card {
        background: #32191d;
        border: 1px solid #78343d;
        border-radius: 18px;
        padding: 20px;
        margin: 12px 0;
    }

    .league-item {
        background: #151a22;
        border: 1px solid #323a47;
        border-radius: 14px;
        padding: 14px;
        margin: 8px 0;
    }

    .league-name {
        font-size: 18px;
        font-weight: 700;
        color: #f3f5f7;
    }

    .league-meta {
        color: #9aa4b2;
        font-size: 14px;
        margin-top: 4px;
    }

    .match-card {
        background: #151a22;
        border: 1px solid #303846;
        border-radius: 16px;
        padding: 18px;
        margin: 10px 0;
    }

    .team-name {
        font-size: 19px;
        font-weight: 700;
    }

    .match-time {
        font-size: 18px;
        font-weight: 700;
        color: #58a6ff;
    }

    .small {
        color: #9aa4b2;
        font-size: 13px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

if "league_results" not in st.session_state:
    st.session_state.league_results = []

if "selected_leagues" not in st.session_state:
    st.session_state.selected_leagues = []

if "matches" not in st.session_state:
    st.session_state.matches = []

if "last_search" not in st.session_state:
    st.session_state.last_search = ""

if "last_match_search" not in st.session_state:
    st.session_state.last_match_search = None


# =========================================================
# API KEY
# =========================================================

def get_secret_api_key():
    try:
        if "API_KEY" in st.secrets:
            return str(st.secrets["API_KEY"]).strip()

        if "api_key" in st.secrets:
            return str(st.secrets["api_key"]).strip()

    except Exception:
        pass

    return ""


secret_key = get_secret_api_key()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="title">⚽ Football Match Analyzer</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Multi-League Prematch Fixture Search • Myanmar Time'
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("🔐 API SETTINGS")

    if secret_key:
        st.success("API key loaded from Streamlit Secrets.")

        use_secret = st.checkbox(
            "Use stored API key",
            value=True,
        )

        if use_secret:
            api_key = secret_key
        else:
            api_key = st.text_input(
                "API-Football API Key",
                type="password",
            ).strip()

    else:
        api_key = st.text_input(
            "API-Football API Key",
            type="password",
            placeholder="Paste your API key here",
        ).strip()

    st.divider()

    st.caption(
        "API-Football Free plan currently provides "
        "100 requests/day."
    )

    st.caption(
        "Do not publish your API key inside public GitHub code."
    )


# =========================================================
# API HELPER
# =========================================================

def api_headers(key):
    return {
        "x-apisports-key": key,
        "Accept": "application/json",
    }


def api_get(endpoint, params, key, timeout=20):

    url = f"{API_BASE}{endpoint}"

    response = requests.get(
        url,
        headers=api_headers(key),
        params=params,
        timeout=timeout,
    )

    # HTTP error
    if response.status_code != 200:
        raise RuntimeError(
            f"HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    try:
        data = response.json()
    except Exception:
        raise RuntimeError(
            "API returned invalid JSON."
        )

    # API errors
    errors = data.get("errors")

    if errors:

        if isinstance(errors, dict):
            error_text = " | ".join(
                f"{k}: {v}"
                for k, v in errors.items()
            )
        else:
            error_text = str(errors)

        raise RuntimeError(error_text)

    return data


# =========================================================
# LEAGUE SEARCH
# =========================================================

@st.cache_data(ttl=600, show_spinner=False)
def search_leagues_cached(search_text, key):

    data = api_get(
        "/leagues",
        {
            "search": search_text,
        },
        key,
    )

    return data.get("response", [])


def search_leagues(search_text):

    search_text = search_text.strip()

    if len(search_text) < 3:
        st.warning(
            "League name အနည်းဆုံး 3 characters ရိုက်ပါ။ "
            "ဥပမာ: Premier / Champions / LaLiga"
        )
        return

    if not api_key:
        st.error(
            "API key မထည့်ရသေးပါ။ "
            "ဘယ်ဘက် API SETTINGS မှာ API key ထည့်ပါ။"
        )
        return

    try:

        with st.spinner(
            f"Searching leagues: {search_text}"
        ):

            results = search_leagues_cached(
                search_text,
                api_key,
            )

        cleaned = []

        for item in results:

            league = item.get("league", {})
            country = item.get("country", {})

            league_id = league.get("id")
            league_name = league.get("name")
            league_type = league.get("type")

            if not league_id or not league_name:
                continue

            cleaned.append(
                {
                    "id": league_id,
                    "name": league_name,
                    "type": league_type or "",
                    "country": country.get("name", "World"),
                    "logo": league.get("logo", ""),
                    "display": (
                        f"{league_name} "
                        f"— {country.get('name', 'World')} "
                        f"(ID: {league_id})"
                    ),
                }
            )

        st.session_state.league_results = cleaned
        st.session_state.last_search = search_text

        if not cleaned:
            st.warning(
                f"'{search_text}' နဲ့ ကိုက်တဲ့ league မတွေ့ပါ။"
            )

    except Exception as e:

        st.session_state.league_results = []

        st.error(
            f"League search error: {e}"
        )


# =========================================================
# LEAGUE SEARCH UI
# =========================================================

st.markdown(
    "## 🏆 Search League"
)

st.caption(
    "ကိုယ်ရှာချင်တဲ့ league နာမည်ကို ရိုက်ပြီး Search လုပ်ပါ။"
)

search_col1, search_col2 = st.columns(
    [4, 1],
    vertical_alignment="bottom",
)

with search_col1:

    league_query = st.text_input(
        "League name",
        value="",
        placeholder=(
            "ဥပမာ: Premier League, Champions League, "
            "LaLiga, Bundesliga"
        ),
        label_visibility="collapsed",
    )

with search_col2:

    search_button = st.button(
        "🔍 SEARCH",
        use_container_width=True,
        type="primary",
    )


if search_button:

    search_leagues(league_query)


# =========================================================
# SEARCH RESULTS
# =========================================================

if st.session_state.league_results:

    st.markdown(
        f"### 🔎 Search results for "
        f"`{st.session_state.last_search}`"
    )

    # Remove duplicate IDs
    unique_results = {}

    for league in st.session_state.league_results:
        unique_results[league["id"]] = league

    unique_results = list(unique_results.values())

    options = [
        league["id"]
        for league in unique_results
    ]

    option_labels = {
        league["id"]: league["display"]
        for league in unique_results
    }

    current_selected_ids = [
        item["id"]
        for item in st.session_state.selected_leagues
    ]

    valid_defaults = [
        x
        for x in current_selected_ids
        if x in options
    ]

    selected_ids = st.multiselect(
        "Select leagues",
        options=options,
        default=valid_defaults,
        format_func=lambda x: option_labels.get(
            x,
            str(x),
        ),
        key="league_selector",
        placeholder="Choose one or more leagues...",
    )

    # Update selected leagues
    selected_objects = [
        league
        for league in unique_results
        if league["id"] in selected_ids
    ]

    # Preserve previously selected leagues from other searches
    old_objects = {
        item["id"]: item
        for item in st.session_state.selected_leagues
    }

    for item in selected_objects:
        old_objects[item["id"]] = item

    # Only keep IDs currently selected in widget OR
    # previously selected leagues that were not part of
    # the current search results.
    current_result_ids = set(options)

    final_selected = []

    for item in st.session_state.selected_leagues:

        if (
            item["id"] not in current_result_ids
            and item["id"] not in selected_ids
        ):
            final_selected.append(item)

    final_selected.extend(selected_objects)

    # Remove duplicates
    final_map = {
        item["id"]: item
        for item in final_selected
    }

    st.session_state.selected_leagues = list(
        final_map.values()
    )


# =========================================================
# SELECTED LEAGUES
# =========================================================

st.markdown(
    "## ✅ Selected Leagues"
)

selected = st.session_state.selected_leagues

if selected:

    st.markdown(
        f"""
        <div class="info-card">
            <div style="font-size:24px;font-weight:700;">
                Selected leagues: {len(selected)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for league in selected:

        c1, c2 = st.columns(
            [5, 1],
            vertical_alignment="center",
        )

        with c1:

            st.markdown(
                f"""
                <div class="league-item">
                    <div class="league-name">
                        🏆 {league['name']}
                    </div>
                    <div class="league-meta">
                        Country: {league['country']}
                        &nbsp; • &nbsp;
                        League ID: {league['id']}
                        &nbsp; • &nbsp;
                        Type: {league['type']}
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

                st.session_state.selected_leagues = [
                    x
                    for x in st.session_state.selected_leagues
                    if x["id"] != league["id"]
                ]

                st.rerun()

    if st.button(
        "🗑️ Clear Selected Leagues",
        use_container_width=True,
    ):

        st.session_state.selected_leagues = []
        st.session_state.matches = []
        st.rerun()

else:

    st.markdown(
        """
        <div class="card">
            No league selected yet.
            <br><br>
            Search a league above and select it.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# SEARCH WINDOW
# =========================================================

st.markdown(
    "## 🕐 Search Window"
)

now_mmt = datetime.now(MMT)

today_mmt = now_mmt.date()

start_mmt = datetime.combine(
    today_mmt,
    time(12, 0),
    tzinfo=MMT,
)

# If current MMT time is before 12:00 PM,
# use today's 12 PM -> tomorrow 12 PM.
#
# If current MMT time is already after 12 PM,
# use today's 12 PM -> tomorrow 12 PM as requested.
end_mmt = start_mmt + timedelta(days=1)

st.markdown(
    f"""
    <div class="info-card">

        <div style="font-size:16px;color:#9aa4b2;">
            🇲🇲 Myanmar Standard Time (MMT)
        </div>

        <div style="font-size:25px;font-weight:700;margin-top:8px;">
            {start_mmt.strftime('%Y-%m-%d %I:%M %p')}
            →
            {end_mmt.strftime('%Y-%m-%d %I:%M %p')}
        </div>

        <div style="color:#9aa4b2;margin-top:8px;">
            Fixed search window:
            Today 12:00 PM → Tomorrow 12:00 PM
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API STATUS
# =========================================================

st.markdown(
    "## 🛡️ API Status"
)

if api_key:

    st.markdown(
        """
        <div class="success-card">
            🟢 API key is ready.
            <br>
            Fixture search can be started.
        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        """
        <div class="warning-card">
            ⚠️ API key မထည့်ရသေးပါ။
            <br>
            Sidebar → API SETTINGS မှာ API key ထည့်ပါ။
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# FIXTURE SEARCH
# =========================================================

@st.cache_data(ttl=120, show_spinner=False)
def get_fixtures_by_date_cached(
    from_date,
    to_date,
    timezone_name,
    key,
):

    data = api_get(
        "/fixtures",
        {
            "from": from_date,
            "to": to_date,
            "timezone": timezone_name,
        },
        key,
        timeout=30,
    )

    return data.get("response", [])


def get_matches():

    if not api_key:

        st.error(
            "API key မထည့်ရသေးပါ။"
        )

        return

    if not selected:

        st.warning(
            "အနည်းဆုံး league တစ်ခုရွေးပါ။"
        )

        return

    from_date = start_mmt.strftime(
        "%Y-%m-%d"
    )

    to_date = end_mmt.strftime(
        "%Y-%m-%d"
    )

    try:

        with st.spinner(
            "⚽ Getting matches..."
        ):

            all_fixtures = get_fixtures_by_date_cached(
                from_date,
                to_date,
                "Asia/Yangon",
                api_key,
            )

        selected_ids = {
            int(x["id"])
            for x in selected
        }

        filtered = []

        for fixture in all_fixtures:

            league = fixture.get(
                "league",
                {},
            )

            league_id = league.get("id")

            if league_id not in selected_ids:
                continue

            fixture_info = fixture.get(
                "fixture",
                {},
            )

            teams = fixture.get(
                "teams",
                {},
            )

            goals = fixture.get(
                "goals",
                {},
            )

            date_string = fixture_info.get(
                "date"
            )

            if not date_string:
                continue

            try:

                utc_dt = datetime.fromisoformat(
                    date_string.replace(
                        "Z",
                        "+00:00",
                    )
                )

                local_dt = utc_dt.astimezone(
                    MMT
                )

            except Exception:

                local_dt = None

            filtered.append(
                {
                    "fixture_id": fixture_info.get(
                        "id"
                    ),
                    "league_id": league_id,
                    "league_name": league.get(
                        "name",
                        "Unknown",
                    ),
                    "country": league.get(
                        "country",
                        "World",
                    ),
                    "round": league.get(
                        "round",
                        "",
                    ),
                    "home": teams.get(
                        "home",
                        {}
                    ).get(
                        "name",
                        "Home",
                    ),
                    "away": teams.get(
                        "away",
                        {}
                    ).get(
                        "name",
                        "Away",
                    ),
                    "home_logo": teams.get(
                        "home",
                        {}
                    ).get(
                        "logo",
                        "",
                    ),
                    "away_logo": teams.get(
                        "away",
                        {}
                    ).get(
                        "logo",
                        "",
                    ),
                    "status": fixture_info.get(
                        "status",
                        {}
                    ).get(
                        "long",
                        "",
                    ),
                    "short_status": fixture_info.get(
                        "status",
                        {}
                    ).get(
                        "short",
                        "",
                    ),
                    "local_datetime": local_dt,
                    "home_goals": goals.get(
                        "home"
                    ),
                    "away_goals": goals.get(
                        "away"
                    ),
                }
            )

        # Sort by Myanmar time
        filtered.sort(
            key=lambda x: (
                x["local_datetime"]
                if x["local_datetime"]
                else datetime.max.replace(
                    tzinfo=MMT
                )
            )
        )

        # Final exact 12PM -> 12PM filter
        exact_matches = []

        for match in filtered:

            dt = match["local_datetime"]

            if not dt:
                continue

            if start_mmt <= dt <= end_mmt:
                exact_matches.append(match)

        st.session_state.matches = exact_matches

        st.session_state.last_match_search = {
            "from": start_mmt,
            "to": end_mmt,
            "count": len(exact_matches),
        }

    except Exception as e:

        st.session_state.matches = []

        st.error(
            f"Fixture API error: {e}"
        )


# =========================================================
# GET MATCHES BUTTON
# =========================================================

st.markdown(
    "## ⚽ Get Matches"
)

if st.button(
    "⚽ GET MATCHES",
    use_container_width=True,
    type="primary",
):

    get_matches()


# =========================================================
# MATCH RESULTS
# =========================================================

if st.session_state.last_match_search:

    info = st.session_state.last_match_search

    st.markdown(
        f"""
        <div class="info-card">

            <div style="font-size:16px;color:#9aa4b2;">
                SEARCH WINDOW
            </div>

            <div style="font-size:22px;font-weight:700;">
                {info['from'].strftime('%Y-%m-%d %I:%M %p')}
                →
                {info['to'].strftime('%Y-%m-%d %I:%M %p')}
                MMT
            </div>

            <div style="margin-top:8px;">
                Matches found:
                <b>{info['count']}</b>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# DISPLAY MATCHES
# =========================================================

matches = st.session_state.matches

if matches:

    st.markdown(
        f"## 📋 Matches — {len(matches)}"
    )

    for match in matches:

        local_dt = match["local_datetime"]

        if local_dt:

            date_text = local_dt.strftime(
                "%Y-%m-%d"
            )

            time_text = local_dt.strftime(
                "%I:%M %p"
            )

        else:

            date_text = "-"
            time_text = "-"

        status = match["status"]

        if match["short_status"] in [
            "NS",
            "TBD",
        ]:

            status_text = "🕐 Not Started"

        else:

            status_text = status or "Unknown"

        st.markdown(
            f"""
            <div class="match-card">

                <div style="
                    display:flex;
                    justify-content:space-between;
                    gap:10px;
                    flex-wrap:wrap;
                ">

                    <div>
                        <div class="league-name">
                            🏆 {match['league_name']}
                        </div>

                        <div class="small">
                            {match['country']}
                            &nbsp; • &nbsp;
                            League ID: {match['league_id']}
                        </div>
                    </div>

                    <div class="small">
                        {date_text}
                    </div>

                </div>

                <hr style="
                    border:0;
                    border-top:1px solid #303846;
                    margin:15px 0;
                ">

                <div style="
                    display:grid;
                    grid-template-columns:
                    1fr 120px 1fr;
                    gap:10px;
                    align-items:center;
                ">

                    <div class="team-name">
                        {match['home']}
                    </div>

                    <div style="
                        text-align:center;
                    ">

                        <div class="match-time">
                            {time_text}
                        </div>

                        <div class="small">
                            MMT
                        </div>

                    </div>

                    <div class="team-name"
                         style="text-align:right;">
                        {match['away']}
                    </div>

                </div>

                <div class="small"
                     style="margin-top:14px;">
                    Status: {status_text}
                    &nbsp; • &nbsp;
                    Fixture ID: {match['fixture_id']}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


elif st.session_state.last_match_search:

    st.markdown(
        """
        <div class="warning-card">
            ⚠️ Selected leagues ထဲမှာ
            သတ်မှတ်ထားတဲ့ Myanmar Time
            12:00 PM → နောက်နေ့ 12:00 PM
            အတွင်း match မတွေ့ပါ။
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# DEBUG / API INFORMATION
# =========================================================

with st.expander("🔧 Debug / API Information"):

    st.write(
        "Current MMT:",
        now_mmt.strftime(
            "%Y-%m-%d %I:%M:%S %p"
        ),
    )

    st.write(
        "Search start MMT:",
        start_mmt.isoformat(),
    )

    st.write(
        "Search end MMT:",
        end_mmt.isoformat(),
    )

    st.write(
        "Selected league IDs:",
        [
            x["id"]
            for x in selected
        ],
    )

    st.write(
        "League search result count:",
        len(
            st.session_state.league_results
        ),
    )

    st.write(
        "Match result count:",
        len(matches),
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Football Match Analyzer • "
    "API-Football • Myanmar Standard Time (Asia/Yangon)"
)
