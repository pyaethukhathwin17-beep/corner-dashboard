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
# 2. CYBER SPORTS LIVESCORE THEME (CSS)
# ============================================================
st.markdown(
    """
<style>
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    .header-card {
        background: linear-gradient(135deg, #161b22 0%, #21262d 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .match-card-header {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .league-title {
        color: #58a6ff;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .time-badge {
        background-color: #21262d;
        color: #00e676;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .team-title {
        font-size: 16px;
        font-weight: 700;
        color: #ffffff;
        margin: 4px 0;
    }
    .stat-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    .score-box {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 6px;
    }
    .badge-over {
        background-color: #00e676;
        color: #042410;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 800;
    }
    .badge-under {
        background-color: #ff1744;
        color: #ffffff;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 800;
    }
    .badge-neutral {
        background-color: #30363d;
        color: #8b949e;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 800;
    }
    .badge-win {
        background-color: #00e676;
        color: #042410;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 900;
        font-size: 13px;
    }
    .badge-loss {
        background-color: #ff1744;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 900;
        font-size: 13px;
    }
    .small-note {
        color: #8b949e;
        font-size: 12px;
    }
    .edge-positive {
        color: #00e676;
        font-weight: 800;
    }
    .edge-negative {
        color: #ff1744;
        font-weight: 800;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# 3. API KEYS & CONNECTION ENGINE
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

MMT_TIMEZONE = timezone(timedelta(hours=6, minutes=30))


def convert_to_mmt(iso_time_str):
    try:
        utc_dt = datetime.fromisoformat(iso_time_str.replace("Z", "+00:00"))
        return utc_dt.astimezone(MMT_TIMEZONE).strftime("%I:%M %p")
    except Exception:
        return iso_time_str[11:16]


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
                    if not errors or len(errors) == 0:
                        return (data["response"], f"Key #{idx + 1} Active")

                    err_str = str(errors).lower()
                    if "ratelimit" in err_str or "rate limit" in err_str:
                        time.sleep(6)
                        continue
                    return ([], f"Key #{idx + 1}: {errors}")

                return ([], f"Key #{idx + 1}: No Response Body")
            except Exception:
                time.sleep(1)
                continue

    return ([], "Connection or API limit issue")


# ============================================================
# 4. LEAGUE WHITELIST & BLACKLIST
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
    combined = f"{league_name} {country_name} {home_name} {away_name}".lower()

    if any(word in combined for word in BLACKLIST_WORDS):
        return False

    if re.search(r"\b(ii|iii|b|c|u\s?-?\d{2})\b", home_name.lower()) or re.search(
        r"\b(ii|iii|b|c|u\s?-?\d{2})\b", away_name.lower()
    ):
        return False

    l_low = league_name.lower()
    c_low = country_name.lower() if country_name else ""

    if "major league soccer" in l_low or l_low == "mls":
        return True

    for country, leagues in ALLOWED_CONFIG.items():
        if country in c_low or country in l_low:
            if any(league in l_low for league in leagues):
                return True

    for league in ALLOWED_CONFIG["world"]:
        if league in l_low:
            return True

    return False


# ============================================================
# 5. EXACT L5 HOME / AWAY STATS ENGINE
# ============================================================
@st.cache_data(ttl=86400, show_spinner=False)
def get_team_last_home_away_fixtures(team_id, venue):
    fixtures, status = fetch_from_api_cached(
        f"fixtures?team={team_id}&last=50&status=FT"
    )
    if not fixtures:
        return None, status

    selected = []
    for f in fixtures:
        h_id = f["teams"]["home"]["id"]
        a_id = f["teams"]["away"]["id"]

        if venue == "HOME" and h_id == team_id:
            selected.append(f)
        elif venue == "AWAY" and a_id == team_id:
            selected.append(f)

        if len(selected) == 5:
            break

    if len(selected) < 5:
        return None, f"Only {len(selected)} {venue} matches found"

    return selected, status


def calculate_l5_metrics(fixtures, team_id, venue):
    if not fixtures or len(fixtures) != 5:
        return None

    over_count = 0
    under_count = 0
    btts_count = 0
    gf_total = 0
    ga_total = 0
    scorelines = []

    for f in fixtures:
        h_name = f["teams"]["home"]["name"]
        a_name = f["teams"]["away"]["name"]
        gh = f["goals"]["home"]
        ga = f["goals"]["away"]

        if gh is None or ga is None:
            return None

        tot = gh + ga
        if tot >= 3:
            over_count += 1
        else:
            under_count += 1

        if gh > 0 and ga > 0:
            btts_count += 1

        if venue == "HOME":
            gf = gh
            ga_val = ga
        else:
            gf = ga
            ga_val = gh

        gf_total += gf
        ga_total += ga_val

        scorelines.append({
            "date": f["fixture"]["date"],
            "home": h_name,
            "away": a_name,
            "gh": gh,
            "ga": ga,
            "total": tot,
        })

    return {
        "over_pct": int((over_count / 5.0) * 100),
        "under_pct": int((under_count / 5.0) * 100),
        "btts_pct": int((btts_count / 5.0) * 100),
        "gf_avg": round(gf_total / 5.0, 2),
        "ga_avg": round(ga_total / 5.0, 2),
        "over_count": over_count,
        "under_count": under_count,
        "btts_count": btts_count,
        "scorelines": scorelines,
    }


def evaluate_fixture(home_id, away_id):
    home_matches, _ = get_team_last_home_away_fixtures(home_id, "HOME")
    away_matches, _ = get_team_last_home_away_fixtures(away_id, "AWAY")

    if not home_matches or not away_matches:
        return None

    home_stats = calculate_l5_metrics(home_matches, home_id, "HOME")
    away_stats = calculate_l5_metrics(away_matches, away_id, "AWAY")

    if not home_stats or not away_stats:
        return None

    # Over Criteria
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

    # Under Criteria
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

    # Model Probability
    over_comp = (home_stats["over_pct"] + away_stats["over_pct"]) / 2
    btts_comp = (home_stats["btts_pct"] + away_stats["btts_pct"]) / 2
    atk_comp = min(
        100, ((home_stats["gf_avg"] + away_stats["gf_avg"]) / 4.0) * 100
    )
    def_comp = min(
        100, ((home_stats["ga_avg"] + away_stats["ga_avg"]) / 3.2) * 100
    )
    over_prob = round(
        (
            over_comp * 0.40
            + btts_comp * 0.20
            + atk_comp * 0.20
            + def_comp * 0.20
        ),
        1,
    )

    under_comp = (home_stats["under_pct"] + away_stats["under_pct"]) / 2
    no_btts_comp = (
        (100 - home_stats["btts_pct"]) + (100 - away_stats["btts_pct"])
    ) / 2
    low_atk = max(
        0,
        min(
            100,
            100 - (((home_stats["gf_avg"] + away_stats["gf_avg"]) / 3.6) * 100),
        ),
    )
    low_def = max(
        0,
        min(
            100,
            100 - (((home_stats["ga_avg"] + away_stats["ga_avg"]) / 3.0) * 100),
        ),
    )
    under_prob = round(
        (
            under_comp * 0.40
            + no_btts_comp * 0.20
            + low_atk * 0.20
            + low_def * 0.20
        ),
        1,
    )

    over_edge = round(over_prob - 60, 1)
    under_edge = round(under_prob - 60, 1)

    signal = "NEUTRAL"
    probability = 0
    model_edge = 0
    stars = 0
    boosts = []

    if over_base_pass:
        signal = "OVER_2_5"
        probability = over_prob
        model_edge = over_edge
        stars = 5
        boosts.append("✅ Exact L5 Home O2.5 ≥ 60%")
        boosts.append("✅ Exact L5 Away O2.5 ≥ 60%")
        boosts.append("✅ Home & Away L5 BTTS ≥ 60%")
        boosts.append("✅ Home GF > 1.5 & GA > 1.0")
        boosts.append("✅ Away GF > 1.0 & GA > 1.0")
    elif under_base_pass:
        signal = "UNDER_2_5"
        probability = under_prob
        model_edge = under_edge
        stars = 5
        boosts.append("✅ Exact L5 Home U2.5 ≥ 60%")
        boosts.append("✅ Exact L5 Away U2.5 ≥ 60%")
        boosts.append("✅ Home & Away L5 BTTS ≤ 50%")
        boosts.append("✅ Home GF < 1.3 & GA < 1.0")
        boosts.append("✅ Away GF < 1.1 & GA < 1.2")
    else:
        signal = "NEUTRAL"
        stars = 0
        probability = max(over_prob, under_prob)
        model_edge = (
            over_edge if over_prob >= under_prob else under_edge
        )

    if stars == 5 and model_edge < 5:
        stars = 0
        signal = "NEUTRAL"
        boosts.append("⚠️ Base criteria met, but Model Edge < 5%")

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


def display_scorelines_ui(fixtures, venue):
    for idx, f in enumerate(fixtures, start=1):
        h = f["teams"]["home"]["name"]
        a = f["teams"]["away"]["name"]
        gh = f["goals"]["home"]
        ga = f["goals"]["away"]
        d_str = f["fixture"]["date"][:10]
        tot = gh + ga
        line = "OVER 2.5" if tot >= 3 else "UNDER 2.5"
        btts = "BTTS YES" if gh > 0 and ga > 0 else "BTTS NO"

        st.markdown(
            f"""
            <div class="score-box">
                <span class="small-note"><b>L{idx}</b> • {d_str}</span><br>
                <b>{h} {gh} - {ga} {a}</b><br>
                <span class="small-note">Total: <b>{tot}</b> | {line} | {btts}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# 6. MAIN UI (MATCH FEED & ON-DEMAND EVALUATION)
# ============================================================
st.markdown(
    """
    ## ⚽ MATCHES FEED
    <span style="color:#58a6ff; font-size:14px; font-weight:600;">Pre-Match Over/Under Intelligence Pro</span>
    """,
    unsafe_allow_html=True,
)

current_mmt_date = datetime.now(MMT_TIMEZONE).date()

if "target_date" not in st.session_state:
    st.session_state.target_date = current_mmt_date

# Date Controls
c_d1, c_d2, c_d3, c_d4 = st.columns([2, 1, 1, 2])
with c_d1:
    st.session_state.target_date = st.date_input(
        "📅 ရွေးချယ်ထားသော ရက်စွဲ", value=st.session_state.target_date
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
    show_upcoming_only = st.checkbox("⏳ Upcoming Only", value=False)

date_str = st.session_state.target_date.strftime("%Y-%m-%d")

st.markdown(
    f"""
    <div class="header-card" style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span class="small-note">DATE SELECTED (MMT)</span>
            <h4 style="margin:0; color:#00e676;">📅 {date_str}</h4>
        </div>
        <span class="time-badge">MMT (UTC+6:30)</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# 1 Single API Call to get Today's Fixtures List
with st.spinner("Fetching today's fixtures list..."):
    raw_matches, conn_status = fetch_from_api_cached(
        f"fixtures?date={date_str}&timezone=Asia/Yangon"
    )

if not raw_matches:
    st.error(f"⚠️ API Info: `{conn_status}`")
    st.info("API Rate Limit သို့မဟုတ် Connection ကို စစ်ဆေးပေးပါခင်ဗျာ။")
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
    st.warning(f"`{date_str}` တွင် Whitelist စံနှုန်းဝင် ပွဲစဉ်များ မရှိပါ။")
    st.stop()

st.caption(
    f"📋 စုစုပေါင်း Whitelist ပွဲစဉ် **{len(filtered_fixtures)}** ပွဲ တွေ့ရှိပါသည်။ အောက်ပါ ပွဲစဉ်များထဲမှ စစ်ဆေးလိုသောပွဲကို နှိပ်၍ **'⚡ Analyze Match'** ပြုလုပ်နိုင်ပါသည် -"
)

# Render Match Feed List
for idx, fix in enumerate(filtered_fixtures):
    f_id = fix["fixture"]["id"]
    h_id = fix["teams"]["home"]["id"]
    a_id = fix["teams"]["away"]["id"]
    h_name = fix["teams"]["home"]["name"]
    a_name = fix["teams"]["away"]["name"]
    l_name = fix["league"]["name"]
    c_name = fix["league"].get("country", "")
    match_time = convert_to_mmt(fix["fixture"]["date"])
    status_short = fix["fixture"]["status"]["short"]

    score_h = fix["goals"]["home"]
    score_a = fix["goals"]["away"]
    is_finished = status_short in [
        "FT",
        "AET",
        "PEN",
    ] and (score_h is not None and score_a is not None)

    # Clean Expander UI for each match
    status_label = (
        f"FT: {score_h}-{score_a}"
        if is_finished
        else f"{status_short}"
    )
    expander_title = (
        f"🏆 {l_name} ({c_name})  |  ⏰ {match_time}  |  ⚽ {h_name} vs {a_name}  [{status_label}]"
    )

    with st.expander(expander_title, expanded=False):
        c_m1, c_m2 = st.columns([3, 1])
        with c_m1:
            st.markdown(
                f"""
                <span class="league-title">🏆 {l_name} • {c_name}</span>
                <div class="team-title">⚽ {h_name} <span style="color:#58a6ff;">vs</span> {a_name}</div>
                <span class="small-note">⏰ Kick Off: <b>{match_time} (MMT)</b> | Status: <b>{status_short}</b></span>
                """,
                unsafe_allow_html=True,
            )
        with c_m2:
            analyze_btn = st.button(
                "⚡ Analyze Match",
                key=f"btn_eval_{f_id}",
                type="primary",
                use_container_width=True,
            )

        # On-Demand Execution for This Match
        eval_key = f"eval_result_{f_id}"
        if analyze_btn:
            with st.spinner(f"Analyzing exact L5 scorelines for {h_name} vs {a_name}..."):
                st.session_state[eval_key] = evaluate_fixture(h_id, a_id)

        if eval_key in st.session_state and st.session_state[eval_key]:
            res = st.session_state[eval_key]
            hs = res["h_stats"]
            as_ = res["a_stats"]
            is_over = res["signal"] == "OVER_2_5"
            is_under = res["signal"] == "UNDER_2_5"

            st.divider()

            # Signal & Metrics Row
            sc1, sc2, sc3 = st.columns([3, 2, 2])
            with sc1:
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
            with sc2:
                st.markdown(
                    f"<b>Model Probability:</b> <span style='color:#ffd600; font-size:18px; font-weight:800;'>{res['probability']}%</span>",
                    unsafe_allow_html=True,
                )
                e_val = res["model_edge"]
                e_cls = "edge-positive" if e_val >= 0 else "edge-negative"
                st.markdown(
                    f"<b>Model Edge:</b> <span class='{e_cls}'>{e_val:+.1f}%</span>",
                    unsafe_allow_html=True,
                )
            with sc3:
                if is_finished:
                    tot_goals = score_h + score_a
                    if (is_over and tot_goals >= 3) or (
                        is_under and tot_goals <= 2
                    ):
                        st.markdown(
                            f"<div class='badge-win'>✅ WON (Score: {score_h}-{score_a})</div>",
                            unsafe_allow_html=True,
                        )
                    elif res["stars"] == 5:
                        st.markdown(
                            f"<div class='badge-loss'>❌ LOST (Score: {score_h}-{score_a})</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"<div class='badge-neutral'>FT: {score_h}-{score_a}</div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("⏳ Match Upcoming")

            st.write("")

            # Home / Away Exact L5 Scorelines
            st.markdown(f"#### 🏠 {h_name} — Last 5 HOME Matches")
            hb1, hb2, hb3, hb4 = st.columns(4)
            with hb1:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>HOME L5 OVER</span><br><b style='color:#58a6ff; font-size:17px;'>{hs['over_pct']}%</b><br><span class='small-note'>{hs['over_count']}/5</span></div>",
                    unsafe_allow_html=True,
                )
            with hb2:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>HOME L5 BTTS</span><br><b style='color:#00e676; font-size:17px;'>{hs['btts_pct']}%</b><br><span class='small-note'>{hs['btts_count']}/5</span></div>",
                    unsafe_allow_html=True,
                )
            with hb3:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>HOME GF</span><br><b style='font-size:17px;'>{hs['gf_avg']}</b></div>",
                    unsafe_allow_html=True,
                )
            with hb4:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>HOME GA</span><br><b style='font-size:17px;'>{hs['ga_avg']}</b></div>",
                    unsafe_allow_html=True,
                )

            display_scorelines_ui(res["home_matches"], "HOME")

            st.write("")
            st.markdown(f"#### ✈️ {a_name} — Last 5 AWAY Matches")
            ab1, ab2, ab3, ab4 = st.columns(4)
            with ab1:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>AWAY L5 OVER</span><br><b style='color:#58a6ff; font-size:17px;'>{as_['over_pct']}%</b><br><span class='small-note'>{as_['over_count']}/5</span></div>",
                    unsafe_allow_html=True,
                )
            with ab2:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>AWAY L5 BTTS</span><br><b style='color:#00e676; font-size:17px;'>{as_['btts_pct']}%</b><br><span class='small-note'>{as_['btts_count']}/5</span></div>",
                    unsafe_allow_html=True,
                )
            with ab3:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>AWAY GF</span><br><b style='font-size:17px;'>{as_['gf_avg']}</b></div>",
                    unsafe_allow_html=True,
                )
            with ab4:
                st.markdown(
                    f"<div class='stat-box'><span class='small-note'>AWAY GA</span><br><b style='font-size:17px;'>{as_['ga_avg']}</b></div>",
                    unsafe_allow_html=True,
                )

            display_scorelines_ui(res["away_matches"], "AWAY")

            st.write("")
            st.markdown("#### 🔎 Strict Criteria Checklist:")
            chk = (
                res["over_criteria"]
                if is_over
                else res["under_criteria"]
                if is_under
                else {**res["over_criteria"], **res["under_criteria"]}
            )
            for k, val in chk.items():
                if val:
                    st.write(f"✅ `{k}`")
                else:
                    st.write(f"❌ `{k}`")

            if res["boosts"]:
                st.markdown("#### ⚡ Active Signals:")
                for b in res["boosts"]:
                    st.write(f"• {b}")

# ============================================================
# 7. FOOTER
# ============================================================
st.divider()
st.caption(
    """
    ⚽ Pre-Match Over/Under Intelligence Pro • Livescore Feed Engine
    Data Source: API-Football (Asia/Yangon Timezone)
    """
)
