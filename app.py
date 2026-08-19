import json
import os
from datetime import datetime, timedelta, timezone

import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Football Prematch Scanner",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# TIMEZONE
# Myanmar Standard Time = UTC + 6:30
# ============================================================

MMT_TZ = timezone(timedelta(hours=6, minutes=30))


# ============================================================
# FILE
# ============================================================

OUTPUT_FILE = "matches_data.json"


# ============================================================
# LEAGUE CONFIGURATION
# ============================================================
#
# API-SPORTS / API-FOOTBALL V3 league IDs
#
# These IDs are competition IDs.
# They remain stable across seasons.
#
# NOTE:
# Cross-division cup matches are NOT represented by the
# Premier League / Championship league ID.
#
# For example:
# Premier League vs Championship teams playing in FA Cup
# belongs to FA Cup, not Premier League.
#
# Therefore cups are included separately.
# ============================================================

LEAGUES = {

    # --------------------------------------------------------
    # ARGENTINA
    # --------------------------------------------------------

    "Argentina — Liga Profesional": {
        "id": 128,
        "country": "Argentina",
        "type": "League",
    },

    # --------------------------------------------------------
    # AUSTRALIA
    # --------------------------------------------------------

    "Australia — A-League": {
        "id": 188,
        "country": "Australia",
        "type": "League",
    },

    # --------------------------------------------------------
    # AUSTRIA
    # --------------------------------------------------------

    "Austria — Bundesliga": {
        "id": 218,
        "country": "Austria",
        "type": "League",
    },

    # --------------------------------------------------------
    # BELGIUM
    # --------------------------------------------------------

    "Belgium — Pro League": {
        "id": 144,
        "country": "Belgium",
        "type": "League",
    },

    # --------------------------------------------------------
    # BRAZIL
    # --------------------------------------------------------

    "Brazil — Serie A": {
        "id": 71,
        "country": "Brazil",
        "type": "League",
    },

    # --------------------------------------------------------
    # CHILE
    # --------------------------------------------------------

    "Chile — Primera División": {
        "id": 265,
        "country": "Chile",
        "type": "League",
    },

    # --------------------------------------------------------
    # CHINA
    # --------------------------------------------------------

    "China — Super League": {
        "id": 169,
        "country": "China",
        "type": "League",
    },

    # --------------------------------------------------------
    # COLOMBIA
    # --------------------------------------------------------

    "Colombia — Primera A": {
        "id": 239,
        "country": "Colombia",
        "type": "League",
    },

    # --------------------------------------------------------
    # CROATIA
    # --------------------------------------------------------

    "Croatia — HNL": {
        "id": 210,
        "country": "Croatia",
        "type": "League",
    },

    # --------------------------------------------------------
    # DENMARK
    # --------------------------------------------------------

    "Denmark — Superliga": {
        "id": 119,
        "country": "Denmark",
        "type": "League",
    },

    # --------------------------------------------------------
    # ECUADOR
    # --------------------------------------------------------

    "Ecuador — Liga Pro": {
        "id": 242,
        "country": "Ecuador",
        "type": "League",
    },

    # --------------------------------------------------------
    # GREECE
    # --------------------------------------------------------

    "Greece — Super League": {
        "id": 197,
        "country": "Greece",
        "type": "League",
    },

    # --------------------------------------------------------
    # JAPAN
    # --------------------------------------------------------

    "Japan — J1 League": {
        "id": 98,
        "country": "Japan",
        "type": "League",
    },

    # --------------------------------------------------------
    # MEXICO
    # --------------------------------------------------------

    "Mexico — Liga MX": {
        "id": 262,
        "country": "Mexico",
        "type": "League",
    },

    # --------------------------------------------------------
    # NETHERLANDS
    # --------------------------------------------------------

    "Netherlands — Eredivisie": {
        "id": 88,
        "country": "Netherlands",
        "type": "League",
    },

    # --------------------------------------------------------
    # NORWAY
    # --------------------------------------------------------

    "Norway — Eliteserien": {
        "id": 103,
        "country": "Norway",
        "type": "League",
    },

    # --------------------------------------------------------
    # PERU
    # --------------------------------------------------------

    "Peru — Liga 1": {
        "id": 281,
        "country": "Peru",
        "type": "League",
    },

    # --------------------------------------------------------
    # POLAND
    # --------------------------------------------------------

    "Poland — Ekstraklasa": {
        "id": 106,
        "country": "Poland",
        "type": "League",
    },

    # --------------------------------------------------------
    # PORTUGAL
    # --------------------------------------------------------

    "Portugal — Primeira Liga": {
        "id": 94,
        "country": "Portugal",
        "type": "League",
    },

    # --------------------------------------------------------
    # SAUDI ARABIA
    # --------------------------------------------------------

    "Saudi Arabia — Saudi Pro League": {
        "id": 307,
        "country": "Saudi-Arabia",
        "type": "League",
    },

    # --------------------------------------------------------
    # SCOTLAND
    # --------------------------------------------------------

    "Scotland — Premiership": {
        "id": 179,
        "country": "Scotland",
        "type": "League",
    },

    # --------------------------------------------------------
    # SWEDEN
    # --------------------------------------------------------

    "Sweden — Allsvenskan": {
        "id": 113,
        "country": "Sweden",
        "type": "League",
    },

    # --------------------------------------------------------
    # SWITZERLAND
    # --------------------------------------------------------

    "Switzerland — Super League": {
        "id": 207,
        "country": "Switzerland",
        "type": "League",
    },

    # --------------------------------------------------------
    # TURKEY
    # --------------------------------------------------------

    "Turkey — Süper Lig": {
        "id": 203,
        "country": "Turkey",
        "type": "League",
    },

    # --------------------------------------------------------
    # USA
    # --------------------------------------------------------

    "USA — MLS": {
        "id": 253,
        "country": "USA",
        "type": "League",
    },

    # ========================================================
    # ENGLAND
    # ========================================================

    "England — Premier League": {
        "id": 39,
        "country": "England",
        "type": "League",
    },

    "England — Championship": {
        "id": 40,
        "country": "England",
        "type": "League",
    },

    # FA CUP
    "England — FA Cup": {
        "id": 45,
        "country": "England",
        "type": "Cup",
    },

    # EFL CUP
    "England — EFL Cup": {
        "id": 48,
        "country": "England",
        "type": "Cup",
    },

    # ========================================================
    # SPAIN
    # ========================================================

    "Spain — La Liga": {
        "id": 140,
        "country": "Spain",
        "type": "League",
    },

    "Spain — La Liga 2": {
        "id": 141,
        "country": "Spain",
        "type": "League",
    },

    "Spain — Copa del Rey": {
        "id": 143,
        "country": "Spain",
        "type": "Cup",
    },

    # ========================================================
    # FRANCE
    # ========================================================

    "France — Ligue 1": {
        "id": 61,
        "country": "France",
        "type": "League",
    },

    "France — Ligue 2": {
        "id": 62,
        "country": "France",
        "type": "League",
    },

    "France — Coupe de France": {
        "id": 66,
        "country": "France",
        "type": "Cup",
    },

    # ========================================================
    # GERMANY
    # ========================================================

    "Germany — Bundesliga": {
        "id": 78,
        "country": "Germany",
        "type": "League",
    },

    "Germany — 2. Bundesliga": {
        "id": 79,
        "country": "Germany",
        "type": "League",
    },

    "Germany — DFB Pokal": {
        "id": 81,
        "country": "Germany",
        "type": "Cup",
    },

    # ========================================================
    # ITALY
    # ========================================================

    "Italy — Serie A": {
        "id": 135,
        "country": "Italy",
        "type": "League",
    },

    "Italy — Serie B": {
        "id": 136,
        "country": "Italy",
        "type": "League",
    },

    "Italy — Coppa Italia": {
        "id": 137,
        "country": "Italy",
        "type": "Cup",
    },

    # ========================================================
    # EUROPEAN CUPS
    # ========================================================

    "UEFA — Champions League": {
        "id": 2,
        "country": "World",
        "type": "Cup",
    },

    "UEFA — Europa League": {
        "id": 3,
        "country": "World",
        "type": "Cup",
    },

    "UEFA — Conference League": {
        "id": 848,
        "country": "World",
        "type": "Cup",
    },
}


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .sub-title {
        color: #9aa4b2;
        font-size: 15px;
        margin-bottom: 20px;
    }

    .info-box {
        background: #171b22;
        border: 1px solid #303640;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .warning-box {
        background: #35380c;
        border-radius: 14px;
        padding: 16px;
        margin-top: 15px;
    }

    .match-card {
        background: #171b22;
        border: 1px solid #303640;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 14px;
    }

    .team-name {
        font-size: 20px;
        font-weight: 700;
    }

    .match-time {
        font-size: 15px;
        color: #9aa4b2;
    }

    .signal-over {
        font-weight: 800;
        font-size: 18px;
    }

    .signal-under {
        font-weight: 800;
        font-size: 18px;
    }

    .signal-neutral {
        font-weight: 700;
        font-size: 18px;
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
    '<div class="sub-title">'
    'Over 2.5 / Under 2.5 • BTTS • GF / GA • Model Edge'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# LOAD JSON
# ============================================================

def load_matches_data():

    if not os.path.exists(OUTPUT_FILE):
        return None

    try:

        with open(
            OUTPUT_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception as exc:

        st.error(
            f"matches_data.json ဖတ်ရာတွင် error ဖြစ်နေပါတယ်: {exc}"
        )

    return None


data = load_matches_data()


# ============================================================
# CURRENT MMT TIME
# ============================================================

now_mmt = datetime.now(MMT_TZ)


# ============================================================
# CORRECT DAILY SEARCH WINDOW
#
# Today 12:00 PM MMT
#       ↓
# Tomorrow 12:00 PM MMT
#
# This is exactly one 24-hour window.
# ============================================================

today_noon = datetime(
    now_mmt.year,
    now_mmt.month,
    now_mmt.day,
    12,
    0,
    0,
    tzinfo=MMT_TZ,
)

if now_mmt < today_noon:

    window_start = today_noon - timedelta(days=1)

else:

    window_start = today_noon


window_end = window_start + timedelta(days=1)


# ============================================================
# HEADER INFO
# ============================================================

col1, col2, col3 = st.columns(3)


with col1:

    st.markdown(
        '<div class="info-box">'
        '<div style="color:#9aa4b2;">🕐 CURRENT MMT</div>'
        f'<div style="font-size:22px;font-weight:700;">'
        f'{now_mmt.strftime("%Y-%m-%d %I:%M %p")}'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


with col2:

    st.markdown(
        '<div class="info-box">'
        '<div style="color:#9aa4b2;">🕘 SEARCH WINDOW</div>'
        f'<div style="font-size:18px;font-weight:700;">'
        f'{window_start.strftime("%Y-%m-%d %I:%M %p")}'
        '<br>'
        f'→ {window_end.strftime("%Y-%m-%d %I:%M %p")} MMT'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


with col3:

    match_count = 0

    if data:

        matches_temp = data.get("matches", [])

        if isinstance(matches_temp, list):
            match_count = len(matches_temp)

    st.markdown(
        '<div class="info-box">'
        '<div style="color:#9aa4b2;">⚽ MATCHES</div>'
        f'<div style="font-size:28px;font-weight:800;">'
        f'{match_count}'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# MODE
# ============================================================

st.markdown(
    '<div class="info-box">'
    '<div style="color:#9aa4b2;">⚙️ MODE</div>'
    '<div style="font-size:20px;font-weight:800;">'
    'MULTI_LEAGUE_PREMATCH'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# LEAGUE FILTER
# ============================================================

st.markdown(
    "## 🏆 League Filter"
)


league_names = list(LEAGUES.keys())


selected_leagues = st.multiselect(
    "Select leagues / cups",
    options=league_names,
    default=league_names,
)


# ============================================================
# FILTER INFORMATION
# ============================================================

selected_ids = {
    LEAGUES[name]["id"]
    for name in selected_leagues
}


st.caption(
    f"Selected competitions: "
    f"{len(selected_leagues)} / {len(league_names)}"
)


# ============================================================
# SHOW LEAGUE LIST
# ============================================================

with st.expander(
    "📋 View selected league IDs",
    expanded=False,
):

    for league_name in selected_leagues:

        league = LEAGUES[league_name]

        st.write(
            f"**{league_name}** "
            f"— ID `{league['id']}` "
            f"— {league['type']}"
        )


# ============================================================
# IMPORTANT NOTE
# ============================================================

st.info(
    "ℹ️ Premier League / Championship, "
    "La Liga / La Liga 2, Ligue 1 / Ligue 2, "
    "Bundesliga / 2. Bundesliga နှင့် Serie A / Serie B "
    "တို့ကို သီးခြား competition အဖြစ် filter လုပ်ထားပါတယ်။ "
    "Cup ပွဲတွေကတော့ FA Cup, Copa del Rey, Coupe de France, "
    "DFB Pokal, Coppa Italia နှင့် UEFA cups အဖြစ် သီးခြားပါဝင်ပါတယ်။"
)


# ============================================================
# NO DATA
# ============================================================

if data is None:

    st.warning(
        "⚠️ matches_data.json မတွေ့ပါ။ "
        "API fetch script ကို run လုပ်ပြီး "
        "matches_data.json ထွက်လာအောင် အရင်လုပ်ပါ။"
    )

    st.stop()


# ============================================================
# DATA
# ============================================================

matches = data.get(
    "matches",
    []
)

if not isinstance(matches, list):

    matches = []


# ============================================================
# FILTER MATCHES BY LEAGUE
# ============================================================

filtered_matches = []


for match in matches:

    league_id = match.get("league_id")

    league_name = match.get(
        "league",
        ""
    )

    # --------------------------------------------------------
    # Prefer league_id
    # --------------------------------------------------------

    if league_id is not None:

        try:

            if int(league_id) not in selected_ids:
                continue

        except Exception:

            continue

    else:

        # ----------------------------------------------------
        # Fallback for older matches_data.json
        # ----------------------------------------------------

        matched = False

        for name, config in LEAGUES.items():

            if league_name == name:
                matched = True

                if config["id"] not in selected_ids:
                    continue

                break

            if (
                league_name
                == name.split(" — ")[-1]
            ):
                matched = True

                if config["id"] not in selected_ids:
                    continue

                break

        if not matched:

            # Do not silently discard old data.
            # Use league name matching where possible.
            if selected_leagues:

                allowed_names = set(
                    selected_leagues
                )

                if league_name not in allowed_names:

                    continue


    filtered_matches.append(match)


# ============================================================
# DATE FILTER
#
# IMPORTANT:
# matches_data.json stores date/time separately.
# We convert the displayed match time to MMT and then check
# whether it falls within:
#
# today 12 PM -> tomorrow 12 PM
# ============================================================

def match_is_in_window(match):

    date_value = str(
        match.get("date", "")
    ).strip()

    time_value = str(
        match.get("time", "")
    ).strip()

    if not date_value:

        return True

    if not time_value:

        return True

    try:

        naive_dt = datetime.strptime(
            f"{date_value} {time_value}",
            "%Y-%m-%d %H:%M",
        )

        match_dt = naive_dt.replace(
            tzinfo=MMT_TZ
        )

        return (
            window_start
            <= match_dt
            < window_end
        )

    except Exception:

        return True


window_matches = [
    match
    for match in filtered_matches
    if match_is_in_window(match)
]


# ============================================================
# SORT
# ============================================================

def signal_priority(signal):

    priorities = {
        "OVER_2_5": 0,
        "UNDER_2_5": 1,
        "NEUTRAL": 2,
        "DATA_UNAVAILABLE": 3,
    }

    return priorities.get(
        signal,
        4,
    )


window_matches.sort(
    key=lambda match: (
        signal_priority(
            match.get("signal", "")
        ),
        match.get("date", ""),
        match.get("time", ""),
    )
)


# ============================================================
# SUMMARY
# ============================================================

st.markdown(
    "## 📊 Scanner Result"
)


over_count = sum(
    1
    for match in window_matches
    if match.get("signal")
    == "OVER_2_5"
)

under_count = sum(
    1
    for match in window_matches
    if match.get("signal")
    == "UNDER_2_5"
)

neutral_count = sum(
    1
    for match in window_matches
    if match.get("signal")
    == "NEUTRAL"
)


c1, c2, c3, c4 = st.columns(4)


with c1:
    st.metric(
        "Total Matches",
        len(window_matches),
    )


with c2:
    st.metric(
        "OVER 2.5",
        over_count,
    )


with c3:
    st.metric(
        "UNDER 2.5",
        under_count,
    )


with c4:
    st.metric(
        "NEUTRAL",
        neutral_count,
    )


# ============================================================
# NO MATCH
# ============================================================

if not window_matches:

    st.warning(
        "⚠️ လက်ရှိ 12:00 PM MMT → နောက်နေ့ 12:00 PM MMT "
        "အတွင်း selected league တွေအတွက် match data မရှိသေးပါ။"
    )

    st.stop()


# ============================================================
# MATCH DISPLAY
# ============================================================

st.markdown(
    "## ⚽ Matches"
)


for match in window_matches:

    home = match.get(
        "home",
        "Unknown",
    )

    away = match.get(
        "away",
        "Unknown",
    )

    league = match.get(
        "league",
        "Unknown League",
    )

    country = match.get(
        "country",
        "",
    )

    date = match.get(
        "date",
        "",
    )

    time = match.get(
        "time",
        "",
    )

    signal = match.get(
        "signal",
        "DATA_UNAVAILABLE",
    )

    prob = match.get(
        "prob",
        None,
    )

    edge = match.get(
        "edge",
        None,
    )

    model_status = match.get(
        "model_status",
        "",
    )

    # --------------------------------------------------------
    # SIGNAL DISPLAY
    # --------------------------------------------------------

    if signal == "OVER_2_5":

        signal_text = "🟢 OVER 2.5"
        signal_class = "signal-over"

    elif signal == "UNDER_2_5":

        signal_text = "🔵 UNDER 2.5"
        signal_class = "signal-under"

    elif signal == "NEUTRAL":

        signal_text = "⚪ NEUTRAL"
        signal_class = "signal-neutral"

    else:

        signal_text = "⚠️ DATA UNAVAILABLE"
        signal_class = "signal-neutral"


    # --------------------------------------------------------
    # PROBABILITY
    # --------------------------------------------------------

    if prob is None:

        prob_text = "N/A"

    else:

        prob_text = f"{prob}%"


    # --------------------------------------------------------
    # EDGE
    # --------------------------------------------------------

    if edge is None:

        edge_text = "N/A"

    else:

        edge_text = f"{edge}%"


    # --------------------------------------------------------
    # CARD
    # --------------------------------------------------------

    st.markdown(
        '<div class="match-card">'
        f'<div style="color:#9aa4b2;">'
        f'🏆 {league}'
        f'{(" • " + country) if country else ""}'
        '</div>'
        '<br>'
        f'<div class="team-name">'
        f'{home}  vs  {away}'
        '</div>'
        '<div class="match-time">'
        f'📅 {date} &nbsp;&nbsp; '
        f'🕐 {time} MMT'
        '</div>'
        '<br>'
        f'<div class="{signal_class}">'
        f'{signal_text}'
        '</div>'
        '<br>'
        f'<div>Model Probability: <b>{prob_text}</b></div>'
        f'<div>Model Edge: <b>{edge_text}</b></div>'
        f'<div style="color:#9aa4b2;">'
        f'Model: {model_status}'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


    # ========================================================
    # STATS
    # ========================================================

    h_stats = match.get(
        "h_stats",
        {}
    )

    a_stats = match.get(
        "a_stats",
        {}
    )


    if h_stats or a_stats:

        with st.expander(
            f"📊 {home} / {away} L5 Data",
            expanded=False,
        ):

            left, right = st.columns(2)


            with left:

                st.markdown(
                    f"### 🏠 {home}"
                )

                st.write(
                    f"Sample: "
                    f"{h_stats.get('sample_size', 'N/A')}"
                )

                st.write(
                    f"O2.5: "
                    f"{h_stats.get('over_pct', 'N/A')}%"
                )

                st.write(
                    f"U2.5: "
                    f"{h_stats.get('under_pct', 'N/A')}%"
                )

                st.write(
                    f"BTTS: "
                    f"{h_stats.get('btts_pct', 'N/A')}%"
                )

                st.write(
                    f"GF Avg: "
                    f"{h_stats.get('gf_avg', 'N/A')}"
                )

                st.write(
                    f"GA Avg: "
                    f"{h_stats.get('ga_avg', 'N/A')}"
                )


            with right:

                st.markdown(
                    f"### ✈️ {away}"
                )

                st.write(
                    f"Sample: "
                    f"{a_stats.get('sample_size', 'N/A')}"
                )

                st.write(
                    f"O2.5: "
                    f"{a_stats.get('over_pct', 'N/A')}%"
                )

                st.write(
                    f"U2.5: "
                    f"{a_stats.get('under_pct', 'N/A')}%"
                )

                st.write(
                    f"BTTS: "
                    f"{a_stats.get('btts_pct', 'N/A')}%"
                )

                st.write(
                    f"GF Avg: "
                    f"{a_stats.get('gf_avg', 'N/A')}"
                )

                st.write(
                    f"GA Avg: "
                    f"{a_stats.get('ga_avg', 'N/A')}"
                )


# ============================================================
# MODEL RULES
# ============================================================

st.markdown(
    "## 🧠 Current Model Rules"
)


with st.expander(
    "View Over / Under rules",
    expanded=False,
):

    st.markdown(
        """
### 🟢 OVER 2.5

- Home L5 O2.5 ≥ 60%
- Away L5 O2.5 ≥ 60%
- Home GF > 1.5
- Home GA > 1.0
- Away GF > 1.0
- Away GA > 1.0
- BTTS ≥ 60%
- Model Edge ≥ 5%

### 🔵 UNDER 2.5

- Home L5 U2.5 ≥ 60%
- Away L5 U2.5 ≥ 60%
- Home GF < 1.3
- Home GA < 1.0
- Away GF < 1.1
- Away GA < 1.2
- BTTS < 50%
- Model Edge ≥ 5%

### Important

xG is **NOT used**.

The API data available in the current setup does not provide the required xG data, so the model does not calculate or invent xG.
"""
    )


# ============================================================
# DATA SOURCE
# ============================================================

st.markdown(
    "## 📡 Data Status"
)


source_col1, source_col2 = st.columns(2)


with source_col1:

    st.markdown(
        '<div class="info-box">'
        '<div style="color:#9aa4b2;">DATA FILE</div>'
        '<div style="font-size:18px;font-weight:700;">'
        f'{OUTPUT_FILE}'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


with source_col2:

    updated_at = data.get(
        "updated_at",
        "Unknown",
    )

    st.markdown(
        '<div class="info-box">'
        '<div style="color:#9aa4b2;">LAST UPDATE</div>'
        '<div style="font-size:18px;font-weight:700;">'
        f'{updated_at}'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# WARNING
# ============================================================

st.markdown(
    '<div class="warning-box">'
    '⚠️ Historical data / current-data limitations '
    'သည် matches_data.json ထုတ်ပေးတဲ့ fetch script ပေါ်မှာ '
    'မူတည်ပါတယ်။ '
    'xG ကို မသုံးထားပါ။'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("⚙️ Scanner")

    st.write(
        "Myanmar Time"
    )

    st.write(
        now_mmt.strftime(
            "%Y-%m-%d %I:%M %p"
        )
    )

    st.divider()

    st.write(
        "Search Window"
    )

    st.write(
        window_start.strftime(
            "%Y-%m-%d %I:%M %p"
        )
    )

    st.write("→")

    st.write(
        window_end.strftime(
            "%Y-%m-%d %I:%M %p"
        )
    )

    st.divider()

    st.write(
        "12:00 PM MMT → 12:00 PM MMT"
    )

    st.write(
        f"Selected Leagues: "
        f"{len(selected_leagues)}"
    )

    st.write(
        f"Matches Found: "
        f"{len(window_matches)}"
    )

    st.divider()

    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):

        st.rerun()
