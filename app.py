from datetime import datetime, timedelta, timezone
import re
import time
import requests
import streamlit as st


# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Pre-Match Over/Under Intelligence Pro",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 2. CYBER DARK THEME
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
    box-shadow: 0 4px 20px rgba(0, 242, 254, 0.1);
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
    padding: 5px 12px;
    border-radius: 6px;
    font-weight: bold;
}

.badge-under {
    background-color: #ff1744;
    color: #ffffff;
    padding: 5px 12px;
    border-radius: 6px;
    font-weight: bold;
}

.badge-neutral {
    background-color: #59636e;
    color: #ffffff;
    padding: 5px 12px;
    border-radius: 6px;
    font-weight: bold;
}

.star-box {
    font-size: 20px;
    letter-spacing: 2px;
}

.stat-box {
    background-color: #172030;
    border: 1px solid #293850;
    border-radius: 8px;
    padding: 10px;
    text-align: center;
}

.score-box {
    background-color: #101722;
    border: 1px solid #293850;
    border-radius: 8px;
    padding: 8px;
    margin-bottom: 6px;
}

.edge-positive {
    color: #00e676;
    font-weight: 900;
}

.edge-negative {
    color: #ff1744;
    font-weight: 900;
}

.small-note {
    color: #8b949e;
    font-size: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 3. API KEYS
# ============================================================

raw_keys = st.secrets.get("API_KEY", "")

API_KEYS = [
    k.strip().replace('"', "").replace("'", "").lower()
    for k in raw_keys.replace("\n", ",").split(",")
    if k.strip()
]

if not API_KEYS:
    st.error(
        "⚠️ API Key မတွေ့ရှိပါ။ Streamlit Secrets ထဲမှာ API_KEY ထည့်ပေးပါ။"
    )
    st.stop()


# ============================================================
# 4. TIMEZONE
# ============================================================

MMT_TIMEZONE = timezone(timedelta(hours=6, minutes=30))


def convert_to_mmt(iso_time_str):
    try:
        utc_dt = datetime.fromisoformat(
            iso_time_str.replace("Z", "+00:00")
        )

        return utc_dt.astimezone(MMT_TIMEZONE).strftime("%I:%M %p")

    except Exception:
        return iso_time_str[11:16]


# ============================================================
# 5. API REQUEST ENGINE
# ============================================================

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_from_api_cached(endpoint):

    for idx, key in enumerate(API_KEYS):

        for attempt in range(2):

            try:

                url = f"https://v3.football.api-sports.io/{endpoint}"

                headers = {
                    "x-apisports-key": key
                }

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=15
                )

                data = response.json()

                # ------------------------------------------------
                # Successful API response
                # ------------------------------------------------

                if "response" in data:

                    errors = data.get("errors")

                    if not errors:

                        return (
                            data["response"],
                            f"Key #{idx + 1} Active"
                        )

                    error_text = str(errors).lower()

                    # Rate limit
                    if (
                        "ratelimit" in error_text
                        or "rate limit" in error_text
                    ):

                        time.sleep(6)
                        continue

                    return (
                        [],
                        f"Key #{idx + 1}: {errors}"
                    )

                return (
                    [],
                    f"Key #{idx + 1}: No Response Body"
                )

            except Exception:

                time.sleep(1)
                continue

    return (
        [],
        "Connection or API limit issue"
    )


# ============================================================
# 6. LEAGUE WHITELIST
# ============================================================

ALLOWED_CONFIG = {

    "england": [
        "premier league",
        "championship"
    ],

    "spain": [
        "la liga",
        "segunda division",
        "laliga 2"
    ],

    "france": [
        "ligue 1",
        "ligue 2"
    ],

    "germany": [
        "bundesliga",
        "2. bundesliga"
    ],

    "italy": [
        "serie a",
        "serie b"
    ],

    "argentina": [
        "liga profesional",
        "primera division"
    ],

    "australia": [
        "a-league"
    ],

    "austria": [
        "bundesliga"
    ],

    "belgium": [
        "pro league",
        "first division a"
    ],

    "brazil": [
        "serie a"
    ],

    "chile": [
        "primera division"
    ],

    "china": [
        "super league"
    ],

    "colombia": [
        "primera a"
    ],

    "croatia": [
        "hnl",
        "1. hnl"
    ],

    "denmark": [
        "superliga"
    ],

    "ecuador": [
        "liga pro"
    ],

    "greece": [
        "super league"
    ],

    "japan": [
        "j1 league"
    ],

    "mexico": [
        "liga mx"
    ],

    "netherlands": [
        "eredivisie"
    ],

    "norway": [
        "eliteserien"
    ],

    "peru": [
        "liga 1"
    ],

    "poland": [
        "ekstraklasa"
    ],

    "portugal": [
        "primeira liga",
        "liga portugal"
    ],

    "saudi arabia": [
        "saudi pro league",
        "pro league"
    ],

    "scotland": [
        "premiership",
        "scottish premiership"
    ],

    "sweden": [
        "allsvenskan"
    ],

    "switzerland": [
        "super league"
    ],

    "turkey": [
        "super lig",
        "süper lig"
    ],

    "usa": [
        "major league soccer"
    ],

    "world": [
        "uefa champions league",
        "uefa europa league",
        "uefa conference league",
        "uefa nations league",
        "copa libertadores",
        "copa sudamericana"
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
    away_name
):

    combined = (
        f"{league_name} "
        f"{country_name} "
        f"{home_name} "
        f"{away_name}"
    ).lower()

    # --------------------------------------------------------
    # Blacklist
    # --------------------------------------------------------

    if any(
        word in combined
        for word in BLACKLIST_WORDS
    ):
        return False

    # --------------------------------------------------------
    # Team suffix filtering
    # --------------------------------------------------------

    if re.search(
        r"\b(ii|iii|b|c|u\s?-?\d{2})\b",
        home_name.lower()
    ):

        return False

    if re.search(
        r"\b(ii|iii|b|c|u\s?-?\d{2})\b",
        away_name.lower()
    ):

        return False

    league_low = league_name.lower()
    country_low = (
        country_name.lower()
        if country_name
        else ""
    )

    # MLS
    if (
        "major league soccer" in league_low
        or league_low == "mls"
    ):
        return True

    # Normal leagues
    for country, leagues in ALLOWED_CONFIG.items():

        if (
            country in country_low
            or country in league_low
        ):

            if any(
                league in league_low
                for league in leagues
            ):

                return True

    # World competitions
    for league in ALLOWED_CONFIG["world"]:

        if league in league_low:
            return True

    return False


# ============================================================
# 7. GET EXACT LAST 5 HOME / AWAY MATCHES
# ============================================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_team_last_home_away_fixtures(
    team_id,
    venue
):

    """
    venue = HOME
    -> Returns the team's latest 5 HOME matches

    venue = AWAY
    -> Returns the team's latest 5 AWAY matches

    IMPORTANT:
    We deliberately request historical fixtures and then
    filter by actual venue.

    The final returned list MUST contain exactly 5 matches.
    Otherwise None is returned.
    """

    fixtures, status = fetch_from_api_cached(
        f"fixtures?team={team_id}&last=50&status=FT"
    )

    if not fixtures:
        return None, status

    selected = []

    for fixture in fixtures:

        home_id = fixture["teams"]["home"]["id"]
        away_id = fixture["teams"]["away"]["id"]

        # ----------------------------------------------------
        # Home team's actual home matches
        # ----------------------------------------------------

        if venue == "HOME":

            if home_id == team_id:
                selected.append(fixture)

        # ----------------------------------------------------
        # Away team's actual away matches
        # ----------------------------------------------------

        elif venue == "AWAY":

            if away_id == team_id:
                selected.append(fixture)

        # Stop once EXACTLY 5 are collected
        if len(selected) == 5:
            break

    if len(selected) < 5:
        return None, (
            f"Only {len(selected)} {venue} matches found"
        )

    return selected, status


# ============================================================
# 8. CALCULATE EXACT L5 METRICS
# ============================================================

def calculate_l5_metrics(
    fixtures,
    team_id,
    venue
):

    if not fixtures or len(fixtures) != 5:
        return None

    over_count = 0
    under_count = 0
    btts_count = 0

    gf_total = 0
    ga_total = 0

    scorelines = []

    # --------------------------------------------------------
    # EXACT 5 MATCHES
    # --------------------------------------------------------

    for fixture in fixtures:

        home_team = fixture["teams"]["home"]
        away_team = fixture["teams"]["away"]

        home_goals = fixture["goals"]["home"]
        away_goals = fixture["goals"]["away"]

        if home_goals is None:
            return None

        if away_goals is None:
            return None

        total_goals = (
            home_goals +
            away_goals
        )

        # ----------------------------------------------------
        # O2.5 / U2.5
        # ----------------------------------------------------

        if total_goals >= 3:
            over_count += 1
        else:
            under_count += 1

        # ----------------------------------------------------
        # BTTS
        # ----------------------------------------------------

        if (
            home_goals > 0
            and away_goals > 0
        ):
            btts_count += 1

        # ----------------------------------------------------
        # GF / GA
        # ----------------------------------------------------

        if venue == "HOME":

            gf = home_goals
            ga = away_goals

        else:

            gf = away_goals
            ga = home_goals

        gf_total += gf
        ga_total += ga

        scorelines.append(
            {
                "date": fixture["fixture"]["date"],
                "home": home_team["name"],
                "away": away_team["name"],
                "home_goals": home_goals,
                "away_goals": away_goals,
                "total_goals": total_goals,
            }
        )

    total_matches = 5

    over_pct = (
        over_count /
        total_matches *
        100
    )

    under_pct = (
        under_count /
        total_matches *
        100
    )

    btts_pct = (
        btts_count /
        total_matches *
        100
    )

    gf_avg = gf_total / total_matches
    ga_avg = ga_total / total_matches

    return {

        "over_pct": round(over_pct),
        "under_pct": round(under_pct),
        "btts_pct": round(btts_pct),

        "gf_avg": round(gf_avg, 2),
        "ga_avg": round(ga_avg, 2),

        "sample": 5,

        "scorelines": scorelines,

        "over_count": over_count,
        "under_count": under_count,
        "btts_count": btts_count,

    }


# ============================================================
# 9. MODEL PROBABILITY
# ============================================================

def calculate_over_model_probability(
    home_stats,
    away_stats
):

    """
    Internal model.

    IMPORTANT:
    This is NOT bookmaker-market edge.

    It estimates probability from:
        - Home L5 O2.5
        - Away L5 O2.5
        - Home L5 BTTS
        - Away L5 BTTS
        - Home GF
        - Away GF
        - Home GA
        - Away GA

    Output = estimated model probability.
    """

    over_component = (
        home_stats["over_pct"] +
        away_stats["over_pct"]
    ) / 2

    btts_component = (
        home_stats["btts_pct"] +
        away_stats["btts_pct"]
    ) / 2

    # --------------------------------------------------------
    # Attack contribution
    # --------------------------------------------------------

    attack_score = (
        home_stats["gf_avg"] +
        away_stats["gf_avg"]
    ) / 2

    attack_component = min(
        100,
        attack_score / 2.0 * 100
    )

    # --------------------------------------------------------
    # Defensive concession contribution
    # --------------------------------------------------------

    defensive_concession = (
        home_stats["ga_avg"] +
        away_stats["ga_avg"]
    ) / 2

    defense_component = min(
        100,
        defensive_concession / 1.6 * 100
    )

    # --------------------------------------------------------
    # Weighted model
    # --------------------------------------------------------

    probability = (

        over_component * 0.40

        + btts_component * 0.20

        + attack_component * 0.20

        + defense_component * 0.20

    )

    # Reasonable limits
    probability = max(
        1,
        min(99, probability)
    )

    return round(probability, 1)


def calculate_under_model_probability(
    home_stats,
    away_stats
):

    """
    Internal Under 2.5 probability model.
    """

    under_component = (
        home_stats["under_pct"] +
        away_stats["under_pct"]
    ) / 2

    no_btts_component = (
        (100 - home_stats["btts_pct"]) +
        (100 - away_stats["btts_pct"])
    ) / 2

    # Low scoring attack
    low_attack_score = (
        home_stats["gf_avg"] +
        away_stats["gf_avg"]
    ) / 2

    attack_component = max(
        0,
        min(
            100,
            100 - (low_attack_score / 1.8 * 100)
        )
    )

    # Low conceding
    low_concession = (
        home_stats["ga_avg"] +
        away_stats["ga_avg"]
    ) / 2

    defense_component = max(
        0,
        min(
            100,
            100 - (low_concession / 1.5 * 100)
        )
    )

    probability = (

        under_component * 0.40

        + no_btts_component * 0.20

        + attack_component * 0.20

        + defense_component * 0.20

    )

    probability = max(
        1,
        min(99, probability)
    )

    return round(probability, 1)


# ============================================================
# 10. EVALUATE FIXTURE
# ============================================================

def evaluate_fixture(
    home_id,
    away_id
):

    # --------------------------------------------------------
    # EXACT L5 HOME
    # --------------------------------------------------------

    home_matches, home_status = (
        get_team_last_home_away_fixtures(
            home_id,
            "HOME"
        )
    )

    # --------------------------------------------------------
    # EXACT L5 AWAY
    # --------------------------------------------------------

    away_matches, away_status = (
        get_team_last_home_away_fixtures(
            away_id,
            "AWAY"
        )
    )

    # --------------------------------------------------------
    # MUST HAVE EXACTLY 5 + 5
    # --------------------------------------------------------

    if not home_matches:
        return None

    if not away_matches:
        return None

    if len(home_matches) != 5:
        return None

    if len(away_matches) != 5:
        return None

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    home_stats = calculate_l5_metrics(
        home_matches,
        home_id,
        "HOME"
    )

    away_stats = calculate_l5_metrics(
        away_matches,
        away_id,
        "AWAY"
    )

    if not home_stats or not away_stats:
        return None

    # ========================================================
    # OVER CRITERIA
    # ========================================================

    over_criteria = {

        "home_over_60":
            home_stats["over_pct"] >= 60,

        "away_over_60":
            away_stats["over_pct"] >= 60,

        "home_btts_60":
            home_stats["btts_pct"] >= 60,

        "away_btts_60":
            away_stats["btts_pct"] >= 60,

        "home_gf":
            home_stats["gf_avg"] > 1.5,

        "home_ga":
            home_stats["ga_avg"] > 1.0,

        "away_gf":
            away_stats["gf_avg"] > 1.0,

        "away_ga":
            away_stats["ga_avg"] > 1.0,

    }

    over_base_pass = all(
        over_criteria.values()
    )

    # ========================================================
    # UNDER CRITERIA
    # ========================================================

    under_criteria = {

        "home_under_60":
            home_stats["under_pct"] >= 60,

        "away_under_60":
            away_stats["under_pct"] >= 60,

        "home_btts_50":
            home_stats["btts_pct"] <= 50,

        "away_btts_50":
            away_stats["btts_pct"] <= 50,

        "home_gf":
            home_stats["gf_avg"] < 1.3,

        "home_ga":
            home_stats["ga_avg"] < 1.0,

        "away_gf":
            away_stats["gf_avg"] < 1.1,

        "away_ga":
            away_stats["ga_avg"] < 1.2,

    }

    under_base_pass = all(
        under_criteria.values()
    )

    # ========================================================
    # MODEL PROBABILITY
    # ========================================================

    over_probability = calculate_over_model_probability(
        home_stats,
        away_stats
    )

    under_probability = calculate_under_model_probability(
        home_stats,
        away_stats
    )

    # ========================================================
    # MODEL EDGE
    #
    # This is:
    #
    # Model Probability - 60%
    #
    # It is NOT bookmaker market edge.
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
    # FINAL SIGNAL
    # ========================================================

    signal = "NEUTRAL"

    probability = 0
    model_edge = 0

    stars = 0

    boosts = []

    # --------------------------------------------------------
    # OVER
    # --------------------------------------------------------

    if over_base_pass:

        signal = "OVER_2_5"

        probability = over_probability

        model_edge = over_edge

        stars = 5

        boosts.append(
            "✅ Exact L5 Home O2.5 ≥ 60%"
        )

        boosts.append(
            "✅ Exact L5 Away O2.5 ≥ 60%"
        )

        boosts.append(
            "✅ Home L5 BTTS ≥ 60%"
        )

        boosts.append(
            "✅ Away L5 BTTS ≥ 60%"
        )

        boosts.append(
            "✅ Home GF > 1.5"
        )

        boosts.append(
            "✅ Home GA > 1.0"
        )

        boosts.append(
            "✅ Away GF > 1.0"
        )

        boosts.append(
            "✅ Away GA > 1.0"
        )

    # --------------------------------------------------------
    # UNDER
    # --------------------------------------------------------

    elif under_base_pass:

        signal = "UNDER_2_5"

        probability = under_probability

        model_edge = under_edge

        stars = 5

        boosts.append(
            "✅ Exact L5 Home U2.5 ≥ 60%"
        )

        boosts.append(
            "✅ Exact L5 Away U2.5 ≥ 60%"
        )

        boosts.append(
            "✅ Home L5 BTTS ≤ 50%"
        )

        boosts.append(
            "✅ Away L5 BTTS ≤ 50%"
        )

        boosts.append(
            "✅ Home GF < 1.3"
        )

        boosts.append(
            "✅ Home GA < 1.0"
        )

        boosts.append(
            "✅ Away GF < 1.1"
        )

        boosts.append(
            "✅ Away GA < 1.2"
        )

    # --------------------------------------------------------
    # If strict criteria don't pass
    # --------------------------------------------------------

    else:

        signal = "NEUTRAL"

        stars = 0

        if over_probability >= under_probability:

            probability = over_probability
            model_edge = over_edge

        else:

            probability = under_probability
            model_edge = under_edge

    # --------------------------------------------------------
    # 5-star is STRICT
    #
    # Base criteria + model edge >= 5
    #
    # If model probability is below 65,
    # don't call it a 5-star.
    # --------------------------------------------------------

    if stars == 5:

        if model_edge < 5:

            stars = 0

            signal = "NEUTRAL"

            boosts.append(
                "⚠️ Base criteria passed, but Model Edge < 5%"
            )

    return {

        "signal": signal,

        "stars": stars,

        "probability": probability,

        "model_edge": model_edge,

        "h_stats": home_stats,

        "a_stats": away_stats,

        "home_matches": home_matches,

        "away_matches": away_matches,

        "boosts": boosts,

        "over_criteria": over_criteria,

        "under_criteria": under_criteria,

    }


# ============================================================
# 11. SCORELINE DISPLAY
# ============================================================

def display_scorelines(
    fixtures,
    venue,
    team_id
):

    if not fixtures:
        st.warning(
            "L5 data မတွေ့ရှိပါ။"
        )
        return

    for index, fixture in enumerate(
        fixtures,
        start=1
    ):

        home = fixture["teams"]["home"]["name"]
        away = fixture["teams"]["away"]["name"]

        gh = fixture["goals"]["home"]
        ga = fixture["goals"]["away"]

        date_raw = fixture["fixture"]["date"]

        try:

            date_obj = datetime.fromisoformat(
                date_raw.replace(
                    "Z",
                    "+00:00"
                )
            )

            date_display = (
                date_obj
                .astimezone(MMT_TIMEZONE)
                .strftime("%Y-%m-%d")
            )

        except Exception:

            date_display = date_raw[:10]

        total = gh + ga

        if total >= 3:
            line = "OVER 2.5"
        else:
            line = "UNDER 2.5"

        if gh > 0 and ga > 0:
            btts = "BTTS YES"
        else:
            btts = "BTTS NO"

        st.markdown(
            f"""
            <div class="score-box">

            <b>L{index}</b> &nbsp; {date_display}

            <br>

            ⚽ <b>{home} {gh} - {ga} {away}</b>

            <br>

            <span class="small-note">
            Total Goals: {total}
            &nbsp; | &nbsp;
            {line}
            &nbsp; | &nbsp;
            {btts}
            </span>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# 12. MAIN UI
# ============================================================

st.markdown(
    """
    ## ⚽ Pre-Match
    <span style="color:#00f2fe;">
    Over/Under Intelligence Pro
    </span>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 13. DATE CONTROL
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

    st.session_state.target_date = st.date_input(
        "📅 စစ်ဆေးလိုသည့် ရက်စွဲ",
        value=st.session_state.target_date
    )


with c_d2:

    if st.button("⬅️ Yesterday"):

        st.session_state.target_date = (
            current_mmt_date -
            timedelta(days=1)
        )

        st.rerun()


with c_d3:

    if st.button("➡️ Tomorrow"):

        st.session_state.target_date = (
            current_mmt_date +
            timedelta(days=1)
        )

        st.rerun()


with c_d4:

    show_upcoming_only = st.checkbox(
        "⏳ Upcoming Matches Only",
        value=False
    )


date_str = (
    st.session_state.target_date
    .strftime("%Y-%m-%d")
)


st.divider()


# ============================================================
# 14. SCAN BUTTON
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
        "🔍 Scan & Evaluate Matches",
        type="primary"
    )


if not scan_clicked:

    st.info(
        f"""
        💡 **{date_str}** ရက်စွဲရှိ
        Whitelist ပွဲစဉ်များကို စစ်ဆေးရန်
        **Scan & Evaluate Matches**
        ကိုနှိပ်ပါ။
        """
    )

    st.stop()


# ============================================================
# 15. FETCH DATE FIXTURES
# ============================================================

with st.spinner(
    f"Scanning fixtures for {date_str}..."
):

    raw_matches, conn_status = (
        fetch_from_api_cached(
            f"fixtures?date={date_str}&timezone=Asia/Yangon"
        )
    )


if not raw_matches:

    st.error(
        f"⚠️ API Error: `{conn_status}`"
    )

    st.info(
        """
        API rate limit ဖြစ်နေပါက
        ခဏစောင့်ပြီး ပြန် scan လုပ်ပါ။
        """
    )

    st.stop()


# ============================================================
# 16. WHITELIST FILTER
# ============================================================

filtered_fixtures = [

    fixture

    for fixture in raw_matches

    if is_allowed_league(

        fixture["league"]["name"],

        fixture["league"].get(
            "country",
            ""
        ),

        fixture["teams"]["home"]["name"],

        fixture["teams"]["away"]["name"]

    )
]


# ============================================================
# 17. UPCOMING FILTER
# ============================================================

if show_upcoming_only:

    filtered_fixtures = [

        fixture

        for fixture in filtered_fixtures

        if fixture["fixture"]["status"]["short"]
        in ["NS", "TBD"]

    ]


if not filtered_fixtures:

    st.warning(
        f"""
        `{date_str}` တွင်
        Whitelist စံနှုန်းဝင် ပွဲစဉ်မရှိပါ။
        """
    )

    st.stop()


# ============================================================
# 18. ANALYSIS
# ============================================================

analyzed_cards = []

won_count = 0
lost_count = 0

finished_evaluated = 0

total_fixtures = len(
    filtered_fixtures
)


progress = st.progress(
    0,
    text="Analyzing..."
)


for index, fixture in enumerate(
    filtered_fixtures
):

    progress.progress(
        (index + 1) /
        total_fixtures,

        text=(
            f"Analyzing "
            f"{index + 1}/{total_fixtures}: "
            f"{fixture['teams']['home']['name']} "
            f"vs "
            f"{fixture['teams']['away']['name']}"
        )
    )

    fixture_id = fixture["fixture"]["id"]

    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]

    home_name = fixture["teams"]["home"]["name"]
    away_name = fixture["teams"]["away"]["name"]

    league_name = fixture["league"]["name"]

    country_name = fixture["league"].get(
        "country",
        ""
    )

    match_time = convert_to_mmt(
        fixture["fixture"]["date"]
    )

    status_short = fixture["fixture"]["status"]["short"]

    score_home = fixture["goals"]["home"]
    score_away = fixture["goals"]["away"]

    is_finished = (

        status_short
        in ["FT", "AET", "PEN"]

        and score_home is not None

        and score_away is not None

    )

    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------

    analysis = evaluate_fixture(
        home_id,
        away_id
    )

    # --------------------------------------------------------
    # Only display 5-star picks
    # --------------------------------------------------------

    if analysis:

        if analysis["stars"] == 5:

            backtest_badge = None

            if is_finished:

                total_goals = (
                    score_home +
                    score_away
                )

                finished_evaluated += 1

                if (

                    analysis["signal"]
                    == "OVER_2_5"

                    and total_goals >= 3

                ):

                    won_count += 1

                    backtest_badge = (
                        "WON",
                        f"✅ WON — "
                        f"Score {score_home}-{score_away}"
                    )

                elif (

                    analysis["signal"]
                    == "UNDER_2_5"

                    and total_goals <= 2

                ):

                    won_count += 1

                    backtest_badge = (
                        "WON",
                        f"✅ WON — "
                        f"Score {score_home}-{score_away}"
                    )

                else:

                    lost_count += 1

                    backtest_badge = (
                        "LOSS",
                        f"❌ LOST — "
                        f"Score {score_home}-{score_away}"
                    )

            analyzed_cards.append(

                {

                    "fixture": fixture,

                    "fixture_id": fixture_id,

                    "home": home_name,

                    "away": away_name,

                    "league": league_name,

                    "country": country_name,

                    "time": match_time,

                    "status": status_short,

                    "analysis": analysis,

                    "is_finished": is_finished,

                    "backtest": backtest_badge,

                }

            )

    # Small throttle
    time.sleep(0.15)


progress.empty()


# ============================================================
# 19. SUMMARY
# ============================================================

win_rate = (

    round(
        won_count /
        finished_evaluated *
        100,
        1
    )

    if finished_evaluated > 0

    else "N/A"
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
                📊 PERFORMANCE SUMMARY
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
            repeat(auto-fit,minmax(130px,1fr));
            gap:10px;
            text-align:center;
        ">

            <div>
                <span style="
                    color:#8b949e;
                    font-size:12px;
                ">
                    WHITELIST
                </span>
                <br>
                <b style="font-size:18px;">
                    {len(filtered_fixtures)}
                </b>
            </div>

            <div>
                <span style="
                    color:#8b949e;
                    font-size:12px;
                ">
                    ⭐ 5-STAR
                </span>
                <br>
                <b style="
                    font-size:18px;
                    color:#00f2fe;
                ">
                    {len(analyzed_cards)}
                </b>
            </div>

            <div>
                <span style="
                    color:#8b949e;
                    font-size:12px;
                ">
                    EVALUATED
                </span>
                <br>
                <b style="font-size:18px;">
                    {finished_evaluated}
                </b>
            </div>

            <div>
                <span style="
                    color:#8b949e;
                    font-size:12px;
                ">
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
                <span style="
                    color:#8b949e;
                    font-size:12px;
                ">
                    WIN RATE
                </span>
                <br>
                <b style="
                    font-size:18px;
                    color:#ffd600;
                ">
                    {win_rate}%
                </b>
            </div>

        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 20. IMPORTANT MODEL EDGE NOTE
# ============================================================

st.warning(
    """
    ⚠️ **Model Edge မှတ်ချက်**

    ယခု Version တွင် bookmaker odds မထည့်ရသေးသောကြောင့်
    **Model Edge = Model Probability − 60% threshold**
    အဖြစ်တွက်ထားပါသည်။

    ဥပမာ Model Probability = 67%
    ဆိုလျှင် Model Edge = +7%.

    ၎င်းသည် bookmaker market edge မဟုတ်သေးပါ။
    နောက်ပိုင်း odds data ထည့်လျှင်
    **True Market Edge = Model Probability − Implied Probability**
    အဖြစ် ပြောင်းနိုင်ပါသည်။
    """
)


# ============================================================
# 21. DISPLAY RESULTS
# ============================================================

if not analyzed_cards:

    st.info(
        """
        ⭐⭐⭐⭐⭐ Strict criteria
        အားလုံးပြည့်ပြီး
        Model Edge ≥ 5% ဖြစ်သော
        ပွဲစဉ် မတွေ့ရှိပါ။
        """
    )

else:

    for card in analyzed_cards:

        analysis = card["analysis"]

        home_stats = analysis["h_stats"]
        away_stats = analysis["a_stats"]

        is_over = (
            analysis["signal"]
            == "OVER_2_5"
        )

        # ----------------------------------------------------
        # MATCH CARD
        # ----------------------------------------------------

        st.markdown(
            '<div class="match-box">',
            unsafe_allow_html=True
        )

        c1, c2, c3 = st.columns(
            [3, 2, 2]
        )

        # ====================================================
        # COLUMN 1
        # ====================================================

        with c1:

            st.markdown(
                f"""
                <span class="league-badge">
                🏆 {card['league']}
                • {card['country']}
                </span>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                ### ⚽ {card['home']}
                vs {card['away']}
                """
            )

            st.caption(
                f"""
                ⏰ {card['time']} (MMT)
                | Status: {card['status']}
                """
            )

        # ====================================================
        # COLUMN 2
        # ====================================================

        with c2:

            if is_over:

                st.markdown(
                    """
                    <span class="badge-over">
                    ⭐⭐⭐⭐⭐ OVER 2.5
                    </span>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    """
                    <span class="badge-under">
                    ⭐⭐⭐⭐⭐ UNDER 2.5
                    </span>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown(
                f"""
                #### Model Probability:
                <span style="
                    color:#ffd600;
                    font-size:22px;
                    font-weight:900;
                ">
                {analysis['probability']}%
                </span>
                """,
                unsafe_allow_html=True
            )

            edge = analysis["model_edge"]

            if edge >= 0:

                st.markdown(
                    f"""
                    **Model Edge:**
                    <span class="edge-positive">
                    +{edge}%
                    </span>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    f"""
                    **Model Edge:**
                    <span class="edge-negative">
                    {edge}%
                    </span>
                    """,
                    unsafe_allow_html=True
                )

            st.caption(
                "Model Edge vs 60% threshold"
            )

        # ====================================================
        # COLUMN 3
        # ====================================================

        with c3:

            if card["backtest"]:

                result_type, result_text = (
                    card["backtest"]
                )

                if result_type == "WON":

                    st.markdown(
                        f"""
                        <div class="badge-win">
                        {result_text}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                else:

                    st.markdown(
                        f"""
                        <div class="badge-loss">
                        {result_text}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:

                st.info(
                    "⏳ Upcoming Match"
                )

        # ====================================================
        # L5 DATA
        # ====================================================

        with st.expander(
            f"""
            📈 EXACT L5 DATA —
            {card['home']} vs {card['away']}
            """
        ):

            st.markdown(
                "### 🏠 Home Team — Last 5 HOME Matches"
            )

            b1, b2, b3, b4 = st.columns(4)

            with b1:

                st.markdown(
                    f"""
                    <div class="stat-box">

                    <span class="small-note">
                    HOME L5 OVER 2.5
                    </span>

                    <br>

                    <b style="
                        color:#00f2fe;
                        font-size:20px;
                    ">
                    {home_stats['over_pct']}%
                    </b>

                    <br>

                    <span class="small-note">
                    {home_stats['over_count']}/5
                    </span>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with b2:

                st.markdown(
                    f"""
                    <div class="stat-box">

                    <span class="small-note">
                    HOME L5 BTTS
                    </span>

                    <br>

                    <b style="
                        color:#00e676;
                        font-size:20px;
                    ">
                    {home_stats['btts_pct']}%
                    </b>

                    <br>

                    <span class="small-note">
                    {home_stats['btts_count']}/5
                    </span>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with b3:

                st.markdown(
                    f"""
                    <div class="stat-box">

                    <span class="small-note">
                    HOME GF
                    </span>

                    <br>

                    <b style="
                        font-size:20px;
                    ">
                    {home_stats['gf_avg']}
                    </b>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with b4:

                st.markdown(
                    f"""
                    <div class="stat-box">

                    <span class="small-note">
                    HOME GA
                    </span>

                    <br>

                    <b style="
                        font-size:20px;
                    ">
                    {home_stats['ga_avg']}
                    </b>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            display_scorelines(
                analysis["home_matches"],
                "HOME",
                card["fixture"]["teams"]["home"]["id"]
            )

            st.divider()

            st.markdown(
                "### ✈️ Away Team — Last 5 AWAY Matches"
            )

            b1, b2, b3, b4 = st.columns(4)

            with b1:

                st.markdown(
                    f"""
                    <div class="stat-box">

                    <span class="small-note">
                    AWAY L5 OVER 2.5
                    </span>

                    <br>

                    <b style="
                        color:#00f2fe;
                        font-size:20px;
                    ">
                    {away_stats['over_pct']}%
                    </b>

                    <br>

                    <span class="small-note">
                    {away_stats['over_count']}/5
                    </span>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with b2:

                st.markdown(
                    f"""
                    <div class="stat-box">

                    <span class="small-note">
                    AWAY L5 BTTS
                    </span>

                    <br>

                    <b style="
                        color:#00e676;
                        font-size:20px;
                    ">
                    {away_stats['btts_pct']}%
                    </b>

                    <br>

                    <span class="small-note">
                    {away_stats['btts_count']}/5
                    </span>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with b3:

                st.markdown(
                    f"""
                    <div class="stat-box">

                    <span class="small-note">
                    AWAY GF
                    </span>

                    <br>

                    <b style="
                        font-size:20px;
                    ">
                    {away_stats['gf_avg']}
                    </b>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with b4:

                st.markdown(
                    f"""
                    <div class="stat-box">

                    <span class="small-note">
                    AWAY GA
                    </span>

                    <br>

                    <b style="
                        font-size:20px;
                    ">
                    {away_stats['ga_avg']}
                    </b>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            display_scorelines(
                analysis["away_matches"],
                "AWAY",
                card["fixture"]["teams"]["away"]["id"]
            )

            # =================================================
            # MODEL DETAILS
            # =================================================

            st.divider()

            st.markdown(
                "### 🧠 Model Decision"
            )

            m1, m2, m3 = st.columns(3)

            with m1:

                st.metric(
                    "Model Probability",
                    f"{analysis['probability']}%"
                )

            with m2:

                st.metric(
                    "Model Edge",
                    f"{analysis['model_edge']:+.1f}%"
                )

            with m3:

                st.metric(
                    "Required Edge",
                    "≥ 5%"
                )

            st.markdown(
                "#### ✅ Criteria Passed"
            )

            for boost in analysis["boosts"]:

                st.write(
                    f"• {boost}"
                )

            # =================================================
            # RAW CRITERIA CHECK
            # =================================================

            st.markdown(
                "#### 🔎 Strict Criteria Check"
            )

            if is_over:

                criteria = analysis[
                    "over_criteria"
                ]

            else:

                criteria = analysis[
                    "under_criteria"
                ]

            for name, passed in criteria.items():

                if passed:

                    st.write(
                        f"✅ {name}"
                    )

                else:

                    st.write(
                        f"❌ {name}"
                    )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


# ============================================================
# 22. FOOTER
# ============================================================

st.divider()

st.caption(
    """
    ⚽ Pre-Match Over/Under Intelligence Pro

    Data source: API-Football

    L5 methodology:
    Home Team = Exact Last 5 Home Matches
    |
    Away Team = Exact Last 5 Away Matches

    xG = Not Used

    ⭐⭐⭐⭐⭐ =
    Strict Base Criteria + Model Edge ≥ 5%

    Note:
    Model Edge in this version is an internal
    probability edge against the 60% threshold,
    not bookmaker market value edge.
    """
)
