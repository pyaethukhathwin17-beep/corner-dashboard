from datetime import datetime, timedelta, timezone
import re
import time
import requests
import streamlit as st

# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Pre-Match Over/Under Intelligence Pro (Single Match)",
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
    padding: 6px 14px;
    border-radius: 6px;
    font-weight: bold;
}
.badge-under {
    background-color: #ff1744;
    color: #ffffff;
    padding: 6px 14px;
    border-radius: 6px;
    font-weight: bold;
}
.badge-neutral {
    background-color: #30363d;
    color: #8b949e;
    padding: 6px 14px;
    border-radius: 6px;
    font-weight: bold;
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
    st.error("⚠️ API Key မတွေ့ရှိပါ။ Streamlit Secrets ထဲမှာ API_KEY ထည့်ပေးပါ။")
    st.stop()

# ============================================================
# 4. TIMEZONE
# ============================================================

MMT_TIMEZONE = timezone(timedelta(hours=6, minutes=30))


def convert_to_mmt(iso_time_str):
    try:
        utc_dt = datetime.fromisoformat(iso_time_str.replace("Z", "+00:00"))
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
                headers = {"x-apisports-key": key}
                response = requests.get(url, headers=headers, timeout=15)
                data = response.json()

                if "response" in data:
                    errors = data.get("errors")
                    if not errors:
                        return (data["response"], f"Key #{idx + 1} Active")

                    error_text = str(errors).lower()
                    if "ratelimit" in error_text or "rate limit" in error_text:
                        time.sleep(6)
                        continue

                    return ([], f"Key #{idx + 1}: {errors}")

                return ([], f"Key #{idx + 1}: No Response Body")
            except Exception:
                time.sleep(1)
                continue

    return ([], "Connection or API limit issue")


# ============================================================
# 6. LEAGUE WHITELIST
# ============================================================

ALLOWED_CONFIG = {
    "england": ["premier league", "championship"],
    "spain": ["la liga", "segunda division", "laliga 2"],
    "france": ["ligue 1", "ligue 2"],
    "germany": ["bundesliga", "2. bundesliga"],
    "italy": ["serie a", "serie b"],
    "argentina": ["liga profesional", "primera division"],
    "australia": ["a-league"],
    "austria": ["bundesliga"],
    "belgium": ["pro league", "first division a"],
    "brazil": ["serie a"],
    "chile": ["primera division"],
    "china": ["super league"],
    "colombia": ["primera a"],
    "croatia": ["hnl", "1. hnl"],
    "denmark": ["superliga"],
    "ecuador": ["liga pro"],
    "greece": ["super league"],
    "japan": ["j1 league"],
    "mexico": ["liga mx"],
    "netherlands": ["eredivisie"],
    "norway": ["eliteserien"],
    "peru": ["liga 1"],
    "poland": ["ekstraklasa"],
    "portugal": ["primeira liga", "liga portugal"],
    "saudi arabia": ["saudi pro league", "pro league"],
    "scotland": ["premiership", "scottish premiership"],
    "sweden": ["allsvenskan"],
    "switzerland": ["super league"],
    "turkey": ["super lig", "süper lig"],
    "usa": ["major league soccer"],
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


def is_allowed_league(league_name, country_name, home_name, away_name):
    combined = (
        f"{league_name} {country_name} {home_name} {away_name}".lower()
    )

    if any(word in combined for word in BLACKLIST_WORDS):
        return False

    if re.search(r"\b(ii|iii|b|c|u\s?-?\d{2})\b", home_name.lower()) or re.search(
        r"\b(ii|iii|b|c|u\s?-?\d{2})\b", away_name.lower()
    ):
        return False

    league_low = league_name.lower()
    country_low = country_name.lower() if country_name else ""

    if "major league soccer" in league_low or league_low == "mls":
        return True

    for country, leagues in ALLOWED_CONFIG.items():
        if country in country_low or country in league_low:
            if any(league in league_low for league in leagues):
                return True

    for league in ALLOWED_CONFIG["world"]:
        if league in league_low:
            return True

    return False


# ============================================================
# 7. GET EXACT LAST 5 HOME / AWAY MATCHES
# ============================================================


@st.cache_data(ttl=86400, show_spinner=False)
def get_team_last_home_away_fixtures(team_id, venue):
    fixtures, status = fetch_from_api_cached(
        f"fixtures?team={team_id}&last=50&status=FT"
    )

    if not fixtures:
        return None, status

    selected = []
    for fixture in fixtures:
        home_id = fixture["teams"]["home"]["id"]
        away_id = fixture["teams"]["away"]["id"]

        if venue == "HOME" and home_id == team_id:
            selected.append(fixture)
        elif venue == "AWAY" and away_id == team_id:
            selected.append(fixture)

        if len(selected) == 5:
            break

    if len(selected) < 5:
        return None, f"Only {len(selected)} {venue} matches found"

    return selected, status


# ============================================================
# 8. CALCULATE EXACT L5 METRICS
# ============================================================


def calculate_l5_metrics(fixtures, team_id, venue):
    if not fixtures or len(fixtures) != 5:
        return None

    over_count = 0
    under_count = 0
    btts_count = 0
    gf_total = 0
    ga_total = 0
    scorelines = []

    for fixture in fixtures:
        home_team = fixture["teams"]["home"]
        away_team = fixture["teams"]["away"]
        home_goals = fixture["goals"]["home"]
        away_goals = fixture["goals"]["away"]

        if home_goals is None or away_goals is None:
            return None

        total_goals = home_goals + away_goals

        if total_goals >= 3:
            over_count += 1
        else:
            under_count += 1

        if home_goals > 0 and away_goals > 0:
            btts_count += 1

        if venue == "HOME":
            gf = home_goals
            ga = away_goals
        else:
            gf = away_goals
            ga = home_goals

        gf_total += gf
        ga_total += ga

        scorelines.append({
            "date": fixture["fixture"]["date"],
            "home": home_team["name"],
            "away": away_team["name"],
            "home_goals": home_goals,
            "away_goals": away_goals,
            "total_goals": total_goals,
        })

    total_matches = 5
    over_pct = (over_count / total_matches) * 100
    under_pct = (under_count / total_matches) * 100
    btts_pct = (btts_count / total_matches) * 100
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


def calculate_over_model_probability(home_stats, away_stats):
    over_component = (home_stats["over_pct"] + away_stats["over_pct"]) / 2
    btts_component = (home_stats["btts_pct"] + away_stats["btts_pct"]) / 2

    attack_score = (home_stats["gf_avg"] + away_stats["gf_avg"]) / 2
    attack_component = min(100, (attack_score / 2.0) * 100)

    defensive_concession = (home_stats["ga_avg"] + away_stats["ga_avg"]) / 2
    defense_component = min(100, (defensive_concession / 1.6) * 100)

    probability = (
        over_component * 0.40
        + btts_component * 0.20
        + attack_component * 0.20
        + defense_component * 0.20
    )
    return round(max(1, min(99, probability)), 1)


def calculate_under_model_probability(home_stats, away_stats):
    under_component = (home_stats["under_pct"] + away_stats["under_pct"]) / 2
    no_btts_component = (
        (100 - home_stats["btts_pct"]) + (100 - away_stats["btts_pct"])
    ) / 2

    low_attack_score = (home_stats["gf_avg"] + away_stats["gf_avg"]) / 2
    attack_component = max(0, min(100, 100 - (low_attack_score / 1.8 * 100)))

    low_concession = (home_stats["ga_avg"] + away_stats["ga_avg"]) / 2
    defense_component = max(0, min(100, 100 - (low_concession / 1.5 * 100)))

    probability = (
        under_component * 0.40
        + no_btts_component * 0.20
        + attack_component * 0.20
        + defense_component * 0.20
    )
    return round(max(1, min(99, probability)), 1)


# ============================================================
# 10. EVALUATE FIXTURE
# ============================================================


def evaluate_fixture(home_id, away_id):
    home_matches, home_status = get_team_last_home_away_fixtures(
        home_id, "HOME"
    )
    away_matches, away_status = get_team_last_home_away_fixtures(
        away_id, "AWAY"
    )

    if not home_matches or not away_matches:
        return None
    if len(home_matches) != 5 or len(away_matches) != 5:
        return None

    home_stats = calculate_l5_metrics(home_matches, home_id, "HOME")
    away_stats = calculate_l5_metrics(away_matches, away_id, "AWAY")

    if not home_stats or not away_stats:
        return None

    over_criteria = {
        "home_over_60": home_stats["over_pct"] >= 60,
        "away_over_60": away_stats["over_pct"] >= 60,
        "home_btts_60": home_stats["btts_pct"] >= 60,
        "away_btts_60": away_stats["btts_pct"] >= 60,
        "home_gf": home_stats["gf_avg"] > 1.5,
        "home_ga": home_stats["ga_avg"] > 1.0,
        "away_gf": away_stats["gf_avg"] > 1.0,
        "away_ga": away_stats["ga_avg"] > 1.0,
    }
    over_base_pass = all(over_criteria.values())

    under_criteria = {
        "home_under_60": home_stats["under_pct"] >= 60,
        "away_under_60": away_stats["under_pct"] >= 60,
        "home_btts_50": home_stats["btts_pct"] <= 50,
        "away_btts_50": away_stats["btts_pct"] <= 50,
        "home_gf": home_stats["gf_avg"] < 1.3,
        "home_ga": home_stats["ga_avg"] < 1.0,
        "away_gf": away_stats["gf_avg"] < 1.1,
        "away_ga": away_stats["ga_avg"] < 1.2,
    }
    under_base_pass = all(under_criteria.values())

    over_probability = calculate_over_model_probability(home_stats, away_stats)
    under_probability = calculate_under_model_probability(
        home_stats, away_stats
    )

    over_edge = round(over_probability - 60, 1)
    under_edge = round(under_probability - 60, 1)

    signal = "NEUTRAL"
    probability = 0
    model_edge = 0
    stars = 0
    boosts = []

    if over_base_pass:
        signal = "OVER_2_5"
        probability = over_probability
        model_edge = over_edge
        stars = 5
        boosts.append("✅ Exact L5 Home O2.5 ≥ 60%")
        boosts.append("✅ Exact L5 Away O2.5 ≥ 60%")
        boosts.append("✅ Home L5 BTTS ≥ 60%")
        boosts.append("✅ Away L5 BTTS ≥ 60%")
        boosts.append("✅ Home GF > 1.5 & GA > 1.0")
        boosts.append("✅ Away GF > 1.0 & GA > 1.0")
    elif under_base_pass:
        signal = "UNDER_2_5"
        probability = under_probability
        model_edge = under_edge
        stars = 5
        boosts.append("✅ Exact L5 Home U2.5 ≥ 60%")
        boosts.append("✅ Exact L5 Away U2.5 ≥ 60%")
        boosts.append("✅ Home L5 BTTS ≤ 50%")
        boosts.append("✅ Away L5 BTTS ≤ 50%")
        boosts.append("✅ Home GF < 1.3 & GA < 1.0")
        boosts.append("✅ Away GF < 1.1 & GA < 1.2")
    else:
        signal = "NEUTRAL"
        stars = 0
        if over_probability >= under_probability:
            probability = over_probability
            model_edge = over_edge
        else:
            probability = under_probability
            model_edge = under_edge

    if stars == 5 and model_edge < 5:
        stars = 0
        signal = "NEUTRAL"
        boosts.append("⚠️ Base criteria passed, but Model Edge < 5%")

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


def display_scorelines(fixtures, venue, team_id):
    if not fixtures:
        st.warning("L5 data မတွေ့ရှိပါ။")
        return

    for index, fixture in enumerate(fixtures, start=1):
        home = fixture["teams"]["home"]["name"]
        away = fixture["teams"]["away"]["name"]
        gh = fixture["goals"]["home"]
        ga = fixture["goals"]["away"]
        date_raw = fixture["fixture"]["date"]

        try:
            date_obj = datetime.fromisoformat(date_raw.replace("Z", "+00:00"))
            date_display = date_obj.astimezone(MMT_TIMEZONE).strftime(
                "%Y-%m-%d"
            )
        except Exception:
            date_display = date_raw[:10]

        total = gh + ga
        line = "OVER 2.5" if total >= 3 else "UNDER 2.5"
        btts = "BTTS YES" if gh > 0 and ga > 0 else "BTTS NO"

        st.markdown(
            f"""
            <div class="score-box">
            <b>L{index}</b> &nbsp; {date_display}<br>
            ⚽ <b>{home} {gh} - {ga} {away}</b><br>
            <span class="small-note">
            Total Goals: {total} &nbsp; | &nbsp; {line} &nbsp; | &nbsp; {btts}
            </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# 12. MAIN UI (ONE MATCH AT A TIME)
# ============================================================

st.markdown(
    """
    ## ⚽ Pre-Match <span style="color:#00f2fe;">Over/Under Intelligence Pro</span>
    """,
    unsafe_allow_html=True,
)
st.caption(
    "🛡️ Single Match Mode (Anti-Ban & Safe API Protection) • 1-Click Evaluation"
)

current_mmt_date = datetime.now(MMT_TIMEZONE).date()

if "target_date" not in st.session_state:
    st.session_state.target_date = current_mmt_date

c_d1, c_d2, c_d3, c_d4 = st.columns([2, 1, 1, 2])
with c_d1:
    st.session_state.target_date = st.date_input(
        "📅 စစ်ဆေးလိုသည့် ရက်စွဲ", value=st.session_state.target_date
    )
with c_d2:
    if st.button("⬅️ Yesterday"):
        st.session_state.target_date = current_mmt_date - timedelta(days=1)
        st.rerun()
with c_d3:
    if st.button("➡️ Tomorrow"):
        st.session_state.target_date = current_mmt_date + timedelta(days=1)
        st.rerun()
with c_d4:
    show_upcoming_only = st.checkbox(
        "⏳ Upcoming Matches Only", value=False
    )

date_str = st.session_state.target_date.strftime("%Y-%m-%d")

st.divider()

# Fetch Fixtures List for the Selected Date (1 Single API Call)
with st.spinner(f"Fetching fixtures list for {date_str}..."):
    raw_matches, conn_status = fetch_from_api_cached(
        f"fixtures?date={date_str}&timezone=Asia/Yangon"
    )

if not raw_matches:
    st.error(f"⚠️ API Info: `{conn_status}`")
    st.info(
        "API Rate Limit သို့မဟုတ် Connection Status ကို စစ်ဆေးပေးပါခင်ဗျာ။"
    )
    st.stop()

filtered_fixtures = [
    f
    for f in raw_matches
    if is_allowed_league(
        f["league"]["name"],
        f["league"].get("country", ""),
        f["teams"]["home"]["name"],
        f["teams"]["away"]["name"],
    )
]

if show_upcoming_only:
    filtered_fixtures = [
        f
        for f in filtered_fixtures
        if f["fixture"]["status"]["short"] in ["NS", "TBD"]
    ]

if not filtered_fixtures:
    st.warning(
        f"`{date_str}` တွင် Whitelist စံနှုန်းဝင် ပွဲစဉ်များ မတွေ့ရှိပါခင်ဗျာ။"
    )
    st.stop()

st.success(
    f"✅ `{date_str}` တွင် Whitelist ပွဲစဉ်ပေါင်း **`{len(filtered_fixtures)}`** ပွဲ စစ်ဆေးရန် အသင့်ရှိပါသည်။"
)

# Build Dropdown options
match_options = {
    f"🏆 {f['league']['name']} ➔ {f['teams']['home']['name']} vs {f['teams']['away']['name']} ({convert_to_mmt(f['fixture']['date'])} MMT)": f
    for f in filtered_fixtures
}

col_sel, col_btn = st.columns([3, 1])
with col_sel:
    selected_label = st.selectbox(
        "🎯 စစ်ဆေးလိုသည့် ပွဲစဉ်ကို ရွေးချယ်ပါ (Select Match to Evaluate):",
        options=list(match_options.keys()),
    )
with col_btn:
    st.write("")
    st.write("")
    evaluate_clicked = st.button("🔍 Evaluate Match", type="primary")

# Execute Evaluation ONLY for the Selected Match (Consumes only 2 cached API calls)
if evaluate_clicked:
    selected_fixture = match_options[selected_label]
    f_id = selected_fixture["fixture"]["id"]
    h_id = selected_fixture["teams"]["home"]["id"]
    a_id = selected_fixture["teams"]["away"]["id"]
    h_name = selected_fixture["teams"]["home"]["name"]
    a_name = selected_fixture["teams"]["away"]["name"]
    l_name = selected_fixture["league"]["name"]
    c_name = selected_fixture["league"].get("country", "")
    match_time = convert_to_mmt(selected_fixture["fixture"]["date"])
    status_short = selected_fixture["fixture"]["status"]["short"]
    score_home = selected_fixture["goals"]["home"]
    score_away = selected_fixture["goals"]["away"]

    is_finished = status_short in [
        "FT",
        "AET",
        "PEN",
    ] and (score_home is not None and score_away is not None)

    with st.spinner(
        f"Evaluating Exact L5 Scorelines for {h_name} vs {a_name}..."
    ):
        analysis = evaluate_fixture(h_id, a_id)

    if not analysis:
        st.warning(
            "⚠️ ဤအသင်းများအတွက် လုံလောက်သော L5 Home/Away သမိုင်းဝင်ပွဲစဉ် အချက်အလက် (၅ ပွဲပြည့်) မတွေ့ရှိပါဗျာ။"
        )
    else:
        home_stats = analysis["h_stats"]
        away_stats = analysis["a_stats"]
        is_over = analysis["signal"] == "OVER_2_5"
        is_under = analysis["signal"] == "UNDER_2_5"

        # Match Header Box
        st.markdown(
            f"""
            <div class="match-box">
                <span class="league-badge">🏆 {l_name} • {c_name}</span>
                <h3>⚽ {h_name} vs {a_name}</h3>
                <span class="small-note">⏰ Time: {match_time} (MMT) | Status: <b>{status_short}</b></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
            if is_over:
                st.markdown(
                    "<div class='badge-over' style='text-align:center;'>⭐⭐⭐⭐⭐ OVER 2.5 TARGET</div>",
                    unsafe_allow_html=True,
                )
            elif is_under:
                st.markdown(
                    "<div class='badge-under' style='text-align:center;'>⭐⭐⭐⭐⭐ UNDER 2.5 TARGET</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div class='badge-neutral' style='text-align:center;'>⚪ NEUTRAL (NO 5-STAR SIGNAL)</div>",
                    unsafe_allow_html=True,
                )

        with c2:
            st.markdown(
                f"<b>Model Probability:</b> <span style='color:#ffd600; font-size:20px; font-weight:900;'>{analysis['probability']}%</span>",
                unsafe_allow_html=True,
            )
            edge = analysis["model_edge"]
            edge_class = "edge-positive" if edge >= 0 else "edge-negative"
            st.markdown(
                f"<b>Model Edge:</b> <span class='{edge_class}'>{edge:+.1f}%</span> (vs 60% threshold)",
                unsafe_allow_html=True,
            )

        with c3:
            if is_finished:
                total_goals = score_home + score_away
                if (is_over and total_goals >= 3) or (
                    is_under and total_goals <= 2
                ):
                    st.markdown(
                        f"<div class='badge-win'>✅ WON — Score {score_home}-{score_away}</div>",
                        unsafe_allow_html=True,
                    )
                elif analysis["stars"] == 5:
                    st.markdown(
                        f"<div class='badge-loss'>❌ LOST — Score {score_home}-{score_away}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div class='badge-neutral'>FT Score: {score_home}-{score_away}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("⏳ Match Upcoming (စောင့်ကြည့်ရန်)")

        # L5 Stats Display
        st.write("")
        with st.expander(
            f"📈 View Exact L5 Match Scorelines ({h_name} vs {a_name})",
            expanded=True,
        ):
            st.markdown("#### 🏠 Home Team — Last 5 HOME Matches")
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>HOME L5 OVER 2.5</span><br><b style='color:#00f2fe; font-size:18px;'>{home_stats['over_pct']}%</b><br><span class='small-note'>{home_stats['over_count']}/5</span></div>",
                    unsafe_allow_html=True,
                )
            with b2:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>HOME L5 BTTS</span><br><b style='color:#00e676; font-size:18px;'>{home_stats['btts_pct']}%</b><br><span class='small-note'>{home_stats['btts_count']}/5</span></div>",
                    unsafe_allow_html=True,
                )
            with b3:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>HOME GF</span><br><b style='font-size:18px;'>{home_stats['gf_avg']}</b></div>",
                    unsafe_allow_html=True,
                )
            with b4:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>HOME GA</span><br><b style='font-size:18px;'>{home_stats['ga_avg']}</b></div>",
                    unsafe_allow_html=True,
                )

            display_scorelines(analysis["home_matches"], "HOME", h_id)

            st.divider()

            st.markdown("#### ✈️ Away Team — Last 5 AWAY Matches")
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>AWAY L5 OVER 2.5</span><br><b style='color:#00f2fe; font-size:18px;'>{away_stats['over_pct']}%</b><br><span class='small-note'>{away_stats['over_count']}/5</span></div>",
                    unsafe_allow_html=True,
                )
            with b2:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>AWAY L5 BTTS</span><br><b style='color:#00e676; font-size:18px;'>{away_stats['btts_pct']}%</b><br><span class='small-note'>{away_stats['btts_count']}/5</span></div>",
                    unsafe_allow_html=True,
                )
            with b3:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>AWAY GF</span><br><b style='font-size:18px;'>{away_stats['gf_avg']}</b></div>",
                    unsafe_allow_html=True,
                )
            with b4:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>AWAY GA</span><br><b style='font-size:18px;'>{away_stats['ga_avg']}</b></div>",
                    unsafe_allow_html=True,
                )

            display_scorelines(analysis["away_matches"], "AWAY", a_id)

            st.divider()
            st.markdown("#### 🧠 Strict Criteria Checklist")
            if is_over:
                criteria = analysis["over_criteria"]
            elif is_under:
                criteria = analysis["under_criteria"]
            else:
                criteria = {
                    **analysis["over_criteria"],
                    **analysis["under_criteria"],
                }

            for name, passed in criteria.items():
                if passed:
                    st.write(f"✅ {name}")
                else:
                    st.write(f"❌ {name}")

            if analysis["boosts"]:
                st.markdown("#### ⚡ Active Signals / Notes:")
                for b in analysis["boosts"]:
                    st.write(f"• {b}")

# ============================================================
# 13. FOOTER
# ============================================================

st.divider()
st.caption(
    """
    ⚽ Pre-Match Over/Under Intelligence Pro • Single Match Mode
    Data source: API-Football • L5 methodology: Exact Last 5 Home/Away scorelines
    """
)
