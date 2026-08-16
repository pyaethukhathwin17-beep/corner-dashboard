from datetime import datetime, timedelta, timezone
import re
import time
import requests
import streamlit as st

st.set_page_config(
    page_title="Pre-Match Over/Under Intelligence Pro",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==================== 1. CYBER SPORTS DARK THEME (CSS) ====================
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
    .stat-box {
        background-color: #172030;
        border: 1px solid #293850;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
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
</style>
""",
    unsafe_allow_html=True,
)

# ==================== 2. API ENGINE & PRECISE ERROR LOGGING ====================
raw_keys = st.secrets.get("API_KEY", "")
API_KEYS = [
    k.strip().replace('"', "").replace("'", "").lower()
    for k in raw_keys.replace("\n", ",").split(",")
    if k.strip()
]

if not API_KEYS:
    st.error("⚠️ API Key မတွေ့ရှိပါ။ Streamlit Secrets တွင် ထည့်သွင်းပေးပါ။")
    st.stop()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_from_api_cached(endpoint):
    errors_log = []
    for idx, key in enumerate(API_KEYS):
        for attempt in range(2):
            try:
                url = f"https://v3.football.api-sports.io/{endpoint}"
                headers = {"x-apisports-key": key}
                res = requests.get(url, headers=headers, timeout=10)
                data = res.json()

                if "response" in data:
                    err = data.get("errors")
                    if not err or len(err) == 0:
                        return data["response"], f"Key #{idx+1} (Active)"
                    elif "rateLimit" in str(err):
                        time.sleep(6)
                        continue
                    else:
                        errors_log.append(f"Key #{idx+1}: {err}")
                else:
                    errors_log.append(f"Key #{idx+1}: No Response Body")
            except Exception as e:
                errors_log.append(f"Key #{idx+1}: {str(e)}")
                time.sleep(1)
                continue

    return [], " | ".join(errors_log) if errors_log else "No data returned"


MMT_TIMEZONE = timezone(timedelta(hours=6, minutes=30))


def convert_to_mmt(iso_time_str):
    try:
        utc_dt = datetime.fromisoformat(iso_time_str.replace("Z", "+00:00"))
        return utc_dt.astimezone(MMT_TIMEZONE).strftime("%I:%M %p")
    except Exception:
        return iso_time_str[11:16]


# ==================== 3. STRICT WHITELIST FILTER ====================
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

    if any(b in combined for b in BLACKLIST_WORDS):
        return False
    if re.search(r"\b(ii|iii|b|c|u\s?-?\d{2})\b", home_name.lower()) or re.search(
        r"\b(ii|iii|b|c|u\s?-?\d{2})\b", away_name.lower()
    ):
        return False

    l_low = league_name.lower()
    c_low = country_name.lower() if country_name else ""

    if "major league soccer" in l_low or l_low == "mls":
        return True

    for c_key, valid_leagues in ALLOWED_CONFIG.items():
        if c_key in c_low or c_key in l_low:
            if any(vl in l_low for vl in valid_leagues):
                return True

    for wl in ALLOWED_CONFIG["world"]:
        if wl in l_low:
            return True

    return False


# ==================== 4. REAL STATS ENGINE ====================
def analyze_real_l5_metrics(pred_payload):
    try:
        teams_data = pred_payload.get("teams", {})
        h_data = teams_data.get("home", {})
        a_data = teams_data.get("away", {})

        h_gf = float(
            h_data.get("league", {})
            .get("goals", {})
            .get("for", {})
            .get("average", {})
            .get("home", 0.0)
            or 0.0
        )
        h_ga = float(
            h_data.get("league", {})
            .get("goals", {})
            .get("against", {})
            .get("average", {})
            .get("home", 0.0)
            or 0.0
        )
        a_gf = float(
            a_data.get("league", {})
            .get("goals", {})
            .get("for", {})
            .get("average", {})
            .get("away", 0.0)
            or 0.0
        )
        a_ga = float(
            a_data.get("league", {})
            .get("goals", {})
            .get("against", {})
            .get("average", {})
            .get("away", 0.0)
            or 0.0
        )

        if h_gf == 0.0:
            h_gf = float(
                h_data.get("league", {})
                .get("goals", {})
                .get("for", {})
                .get("average", {})
                .get("total", 1.4)
                or 1.4
            )
        if h_ga == 0.0:
            h_ga = float(
                h_data.get("league", {})
                .get("goals", {})
                .get("against", {})
                .get("average", {})
                .get("total", 1.0)
                or 1.0
            )
        if a_gf == 0.0:
            a_gf = float(
                a_data.get("league", {})
                .get("goals", {})
                .get("for", {})
                .get("average", {})
                .get("total", 1.1)
                or 1.1
            )
        if a_ga == 0.0:
            a_ga = float(
                a_data.get("league", {})
                .get("goals", {})
                .get("against", {})
                .get("average", {})
                .get("total", 1.2)
                or 1.2
            )

        h_l5_gf_tot = float(
            h_data.get("last_5", {}).get("goals", {}).get("for", {}).get("total", 6)
            or 6
        )
        h_l5_ga_tot = float(
            h_data.get("last_5", {})
            .get("goals", {})
            .get("against", {})
            .get("total", 5)
            or 5
        )
        a_l5_gf_tot = float(
            a_data.get("last_5", {}).get("goals", {}).get("for", {}).get("total", 5)
            or 5
        )
        a_l5_ga_tot = float(
            a_data.get("last_5", {})
            .get("goals", {})
            .get("against", {})
            .get("total", 6)
            or 6
        )

        home_l5_avg_match_goals = (h_l5_gf_tot + h_l5_ga_tot) / 5.0
        away_l5_avg_match_goals = (a_l5_gf_tot + a_l5_ga_tot) / 5.0

        home_l5_over = int(
            min(100, max(20, (home_l5_avg_match_goals / 3.0) * 70))
        )
        away_l5_over = int(
            min(100, max(20, (away_l5_avg_match_goals / 3.0) * 70))
        )

        home_l5_under = 100 - home_l5_over
        away_l5_under = 100 - away_l5_over

        est_btts = int(min(92, max(18, (h_gf * a_gf * 36))))

        est_over_odds = round(
            max(
                1.72,
                min(
                    2.25,
                    1.0 / (((home_l5_over + away_l5_over) / 2.0) / 100.0)
                    * 1.06,
                ),
            ),
            2,
        )
        est_under_odds = round(
            max(
                1.72,
                min(
                    2.25,
                    1.0 / (((home_l5_under + away_l5_under) / 2.0) / 100.0)
                    * 1.06,
                ),
            ),
            2,
        )

        signal = "NEUTRAL"
        confidence = 50
        boosts = []

        is_over_base = (
            home_l5_over >= 60
            and away_l5_over >= 60
            and h_gf > 1.5
            and h_ga > 1.0
            and a_gf > 1.0
            and a_ga > 1.0
            and est_btts >= 60
        )

        if is_over_base:
            signal = "OVER_2_5"
            confidence = 70
            boosts.append("✅ All Base Requirements Met (70% Base)")
            if home_l5_over >= 80 and away_l5_over >= 80:
                confidence += 6
                boosts.append(
                    f"🚀 Home & Away L5 Over $\ge$ 80% (H: {home_l5_over}%, A: {away_l5_over}%) +6%"
                )
            if h_gf >= 2.0:
                confidence += 4
                boosts.append(f"⚽ Strong Home Attack (GF {h_gf:.2f}) +4%")
            if a_gf >= 1.5:
                confidence += 4
                boosts.append(f"👟 Active Away Attack (GF {a_gf:.2f}) +4%")
            if h_ga >= 1.3 and a_ga >= 1.4:
                confidence += 4
                boosts.append("🛡️ High Conceding Defense Line +4%")
            if est_btts >= 75:
                confidence += 4
                boosts.append(f"🎯 Extreme BTTS Expected ({est_btts}%) +4%")

        is_under_base = (
            home_l5_under >= 60
            and away_l5_under >= 60
            and h_gf < 1.3
            and h_ga < 1.0
            and a_gf < 1.1
            and a_ga < 1.2
            and est_btts < 50
        )

        if is_under_base and not is_over_base:
            signal = "UNDER_2_5"
            confidence = 70
            boosts.append("✅ All Base Requirements Met (70% Base)")
            if home_l5_under >= 80 and away_l5_under >= 80:
                confidence += 6
                boosts.append(
                    f"📉 Home & Away L5 Under $\ge$ 80% (H: {home_l5_under}%, A: {away_l5_under}%) +6%"
                )
            if h_ga <= 0.7:
                confidence += 4
                boosts.append(f"🧱 Steel Home Defense (GA {h_ga:.2f}) +4%")
            if a_gf <= 0.8:
                confidence += 4
                boosts.append(f"🧊 Cold Away Attack (GF {a_gf:.2f}) +4%")
            if est_btts <= 35:
                confidence += 5
                boosts.append(f"🚫 Low BTTS Probability ({est_btts}%) +5%")

        confidence = min(95, confidence)

        return {
            "signal": signal,
            "confidence": confidence,
            "h_gf": round(h_gf, 2),
            "h_ga": round(h_ga, 2),
            "a_gf": round(a_gf, 2),
            "a_ga": round(a_ga, 2),
            "home_l5_over": home_l5_over,
            "away_l5_over": away_l5_over,
            "home_l5_under": home_l5_under,
            "away_l5_under": away_l5_under,
            "est_btts": est_btts,
            "est_odds": est_over_odds if signal == "OVER_2_5" else est_under_odds,
            "boosts": boosts,
        }
    except Exception:
        return None


# ==================== MAIN UI ====================
st.markdown(
    "## ⚽ Pre-Match <span style='color:#00f2fe;'>Over/Under Intelligence Pro</span>",
    unsafe_allow_html=True,
)

current_mmt_date = datetime.now(MMT_TIMEZONE).date()

if "target_date" not in st.session_state:
    st.session_state.target_date = current_mmt_date

# Date Controls (Updates date only, DOES NOT call API)
c_d1, c_d2, c_d3, c_d4 = st.columns([2, 1, 1, 2])
with c_d1:
    st.session_state.target_date = st.date_input(
        "📅 စစ်ဆေးလိုသည့် ရက်စွဲ ရွေးပါ", value=st.session_state.target_date
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
        "⏳ Upcoming Matches Only (မကန်ရသေးသောပွဲများသာ)", value=False
    )

date_str = st.session_state.target_date.strftime("%Y-%m-%d")

st.divider()

# Primary Manual Trigger Button
col_b1, col_b2 = st.columns([3, 1])
with col_b1:
    st.markdown(f"### 📋 Selected Date: **`{date_str}`** (MMT)")
with col_b2:
    scan_clicked = st.button("🔍 Scan & Evaluate Matches", type="primary")

# Execute scan ONLY when user clicks the button
if not scan_clicked:
    st.info(
        f"💡 **`{date_str}`** ရက်စွဲရှိ Whitelist ပွဲစဉ်များကို စစ်ဆေးရန် **'🔍 Scan & Evaluate Matches'** ခလုတ်ကို နှိပ်ပေးပါဗျာ (API အလဟဿ မကုန်စေရန် ထိန်းသိမ်းထားပါသည်)။"
    )
else:
    with st.spinner(f"Analyzing Real L5 Stats for {date_str}..."):
        raw_matches, conn_status = fetch_from_api_cached(
            f"fixtures?date={date_str}&timezone=Asia/Yangon"
        )

        if not raw_matches:
            st.error(f"⚠️ API Info: `{conn_status}`")
            st.info(
                "💡 Rate Limit ဖြစ်နေပါက စက္ကန့် ၃၀ ခန့် စောင့်ပြီးမှ ခလုတ်ကို ပြန်နှိပ်ပေးပါဗျာ။"
            )
        else:
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
                    f"`{date_str}` တွင် Whitelist စံနှုန်းဝင် ပွဲစဉ်များ မရှိပါ (သို့မဟုတ် ပွဲများ အားလုံး ပြီးဆုံးသွားပါပြီ)။"
                )
            else:
                analyzed_cards = []
                won_count = 0
                lost_count = 0
                finished_evaluated = 0

                prog_bar = st.progress(0, text="Analyzing Whitelist Fixtures...")
                total_f = len(filtered_fixtures)

                for i, fix in enumerate(filtered_fixtures):
                    prog_bar.progress(
                        (i + 1) / total_f,
                        text=f"Analyzing {i+1}/{total_f}: {fix['teams']['home']['name']} vs {fix['teams']['away']['name']}",
                    )
                    f_id = fix["fixture"]["id"]
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

                    time.sleep(1.2)  # Respect 10 calls/min rate limit

                    pred_res, _ = fetch_from_api_cached(
                        f"predictions?fixture={f_id}"
                    )
                    analysis = None
                    if pred_res and len(pred_res) > 0:
                        analysis = analyze_real_l5_metrics(pred_res[0])

                    if analysis and analysis["signal"] != "NEUTRAL":
                        backtest_badge = None
                        if is_finished:
                            total_actual_goals = score_h + score_a
                            finished_evaluated += 1
                            if (
                                analysis["signal"] == "OVER_2_5"
                                and total_actual_goals >= 3
                            ):
                                won_count += 1
                                backtest_badge = (
                                    "WON",
                                    f"✅ WON [Score: {score_h}-{score_a} ({total_actual_goals} Goals)]",
                                )
                            elif (
                                analysis["signal"] == "UNDER_2_5"
                                and total_actual_goals <= 2
                            ):
                                won_count += 1
                                backtest_badge = (
                                    "WON",
                                    f"✅ WON [Score: {score_h}-{score_a} ({total_actual_goals} Goals)]",
                                )
                            else:
                                lost_count += 1
                                backtest_badge = (
                                    "LOSS",
                                    f"❌ LOST [Score: {score_h}-{score_a} ({total_actual_goals} Goals)]",
                                )

                        analyzed_cards.append({
                            "fixture": fix,
                            "home": h_name,
                            "away": a_name,
                            "league": l_name,
                            "country": c_name,
                            "time": match_time,
                            "status": status_short,
                            "analysis": analysis,
                            "is_finished": is_finished,
                            "backtest": backtest_badge,
                        })

                prog_bar.empty()

                # Summary Header
                st.markdown(
                    f"""
                <div class="hero-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0; color:#00f2fe;">📊 PERFORMANCE SUMMARY ({date_str})</h4>
                        <span style="font-size:12px; color:#8b949e;">API Status: {conn_status}</span>
                    </div>
                    <hr style="border-color:#222d3d; margin:10px 0;">
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:10px; text-align:center;">
                        <div><span style="color:#8b949e; font-size:12px;">WHITELIST MATCHES</span><br><b style="font-size:18px;">{len(filtered_fixtures)}</b></div>
                        <div><span style="color:#8b949e; font-size:12px;">5-STAR PICKS</span><br><b style="font-size:18px; color:#00f2fe;">{len(analyzed_cards)}</b></div>
                        <div><span style="color:#8b949e; font-size:12px;">EVALUATED (FT)</span><br><b style="font-size:18px;">{finished_evaluated}</b></div>
                        <div><span style="color:#8b949e; font-size:12px;">WON / LOST</span><br><b style="font-size:18px; color:#00e676;">{won_count}</b> / <b style="font-size:18px; color:#ff1744;">{lost_count}</b></div>
                        <div><span style="color:#8b949e; font-size:12px;">WIN RATE</span><br><b style="font-size:18px; color:#ffd600;">{round((won_count/finished_evaluated*100), 1) if finished_evaluated > 0 else 'N/A'} %</b></div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if not analyzed_cards:
                    st.info(
                        "သတ်မှတ်ထားသော စံနှုန်းပြည့် ၅ ကြယ်ပွဲစဉ် မတွေ့ရှိသေးပါဗျာ။"
                    )
                else:
                    for card in analyzed_cards:
                        ana = card["analysis"]
                        is_over = ana["signal"] == "OVER_2_5"

                        with st.container():
                            st.markdown(
                                '<div class="match-box">', unsafe_allow_html=True
                            )
                            c1, c2, c3 = st.columns([3, 2, 2])
                            with c1:
                                st.markdown(
                                    f"<span class='league-badge'>🏆 {card['league']} • {card['country']}</span>",
                                    unsafe_allow_html=True,
                                )
                                st.markdown(
                                    f"### ⚽ {card['home']} vs {card['away']}"
                                )
                                st.caption(
                                    f"⏰ Time: **`{card['time']} (MMT)` | Status: **"
                                )
                            with c2:
                                if is_over:
                                    st.markdown(
                                        "<span class='badge-over'>⭐️⭐️⭐️⭐️⭐️ OVER 2.5 TARGET</span>",
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(
                                        "<span class='badge-under'>⭐️⭐️⭐️⭐️⭐️ UNDER 2.5 TARGET</span>",
                                        unsafe_allow_html=True,
                                    )

                                st.markdown(
                                    f"#### Confidence: **<span style='color:#ffd600;'>{ana['confidence']}%</span>**",
                                    unsafe_allow_html=True,
                                )
                                st.caption(
                                    f"📊 Value Odds Line: **{ana['est_odds']}**"
                                )
                            with c3:
                                if card["backtest"]:
                                    res_type, res_text = card["backtest"]
                                    if res_type == "WON":
                                        st.markdown(
                                            f"<div class='badge-win'>{res_text}</div>",
                                            unsafe_allow_html=True,
                                        )
                                    else:
                                        st.markdown(
                                            f"<div class='badge-loss'>{res_text}</div>",
                                            unsafe_allow_html=True,
                                        )
                                else:
                                    st.info("⏳ Match Upcoming (စောင့်ကြည့်ရန်)")

                            with st.expander(
                                f"📈 View Real L5 Metrics ({card['home']} vs {card['away']})"
                            ):
                                b1, b2, b3, b4 = st.columns(4)
                                with b1:
                                    st.markdown(
                                        f"<div class='stat-box'><span style='font-size:11px; color:#8b949e;'>HOME (AT HOME)</span><br><b>GF {ana['h_gf']} / GA {ana['h_ga']}</b></div>",
                                        unsafe_allow_html=True,
                                    )
                                with b2:
                                    st.markdown(
                                        f"<div class='stat-box'><span style='font-size:11px; color:#8b949e;'>AWAY (ON ROAD)</span><br><b>GF {ana['a_gf']} / GA {ana['a_ga']}</b></div>",
                                        unsafe_allow_html=True,
                                    )
                                with b3:
                                    st.markdown(
                                        f"<div class='stat-box'><span style='font-size:11px; color:#8b949e;'>HOME L5 OVER</span><br><b style='color:#00f2fe;'>{ana['home_l5_over']}%</b></div>",
                                        unsafe_allow_html=True,
                                    )
                                Chipp = ana["away_l5_over"]
                                with b4:
                                    st.markdown(
                                        f"<div class='stat-box'><span style='font-size:11px; color:#8b949e;'>AWAY L5 OVER</span><br><b style='color:#00e676;'>{Chipp}%</b></div>",
                                        unsafe_allow_html=True,
                                    )

                                st.markdown("##### ⚡ Confidence Boost Factors:")
                                for r in ana["boosts"]:
                                    st.write(f"• {r}")

                            st.markdown("</div>", unsafe_allow_html=True)
