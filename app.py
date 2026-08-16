from datetime import datetime, timedelta, timezone
import re
import requests
import streamlit as st

st.set_page_config(
    page_title="Corner Pulse Intelligence Pro",
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
    .radar-container {
        background: linear-gradient(135deg, #131b26 0%, #1c2636 100%);
        border: 1px solid #00f2fe44;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 242, 254, 0.1);
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
    .badge-minute {
        background-color: #00e676;
        color: #000000;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: 800;
        font-size: 12px;
    }
    .badge-ht {
        background-color: #2a364f;
        color: #c9d1d9;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 12px;
    }
    .stat-pill {
        background-color: #172030;
        border: 1px solid #293850;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    .badge-over {
        background-color: #00e676;
        color: #042410;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
    }
    .badge-under {
        background-color: #ff1744;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==================== 2. API KEY ENGINE ====================
raw_keys = st.secrets.get("API_KEY", "")
API_KEYS = [
    k.strip().replace('"', "").replace("'", "").lower()
    for k in raw_keys.replace("\n", ",").split(",")
    if k.strip()
]

if not API_KEYS:
    st.error("⚠️ API Key မတွေ့ရှိပါ။ Streamlit Secrets တွင် ထည့်သွင်းပေးပါ။")
    st.stop()


def fetch_from_api(endpoint):
    errors_log = []
    for idx, key in enumerate(API_KEYS):
        try:
            url = f"https://v3.football.api-sports.io/{endpoint}"
            headers = {"x-apisports-key": key}
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()

            if "response" in data:
                err = data.get("errors")
                if not err:
                    return data["response"], f"Key #{idx+1} (Active)"
                else:
                    errors_log.append(f"Key #{idx+1}: {err}")
            else:
                errors_log.append(f"Key #{idx+1}: No Response Body")
        except Exception as e:
            errors_log.append(f"Key #{idx+1}: {str(e)}")

    return [], " | ".join(errors_log)


MMT_TIMEZONE = timezone(timedelta(hours=6, minutes=30))


def convert_to_mmt(iso_time_str):
    try:
        utc_dt = datetime.fromisoformat(iso_time_str.replace("Z", "+00:00"))
        return utc_dt.astimezone(MMT_TIMEZONE).strftime("%I:%M %p")
    except Exception:
        return iso_time_str[11:16]


# ==================== 3. LEAGUE WHITELIST RULES ====================
ALLOWED_CONFIG = {
    # 5 Big Countries: Top Tier + 2nd Tier
    "england": ["premier league", "championship"],
    "spain": ["la liga", "segunda division", "laliga 2"],
    "france": ["ligue 1", "ligue 2"],
    "germany": ["bundesliga", "2. bundesliga"],
    "italy": ["serie a", "serie b"],
    # Top Tier Only Countries
    "argentina": ["liga profesional", "primera division"],
    "australia": ["a-league"],
    "austria": ["bundesliga"],
    "belgium": ["pro league", "first division a", "jupiler"],
    "brazil": ["serie a"],
    "chile": ["primera division"],
    "china": ["super league", "csl"],
    "colombia": ["primera a"],
    "croatia": ["hnl", "1. hnl"],
    "denmark": ["superliga"],
    "ecuador": ["liga pro", "serie a"],
    "greece": ["super league"],
    "japan": ["j1 league"],
    "mexico": ["liga mx"],
    "netherlands": ["eredivisie"],
    "norway": ["eliteserien"],
    "peru": ["liga 1", "primera division"],
    "poland": ["ekstraklasa"],
    "portugal": ["primeira liga", "liga portugal"],
    "saudi arabia": ["saudi pro league", "pro league"],
    "scotland": ["premiership", "scottish premiership"],
    "sweden": ["allsvenskan"],
    "switzerland": ["super league"],
    "turkey": ["super lig", "süper lig"],
    "usa": ["major league soccer", "mls"],
    # Major Tournaments
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
    if any(b in combined for b in BLACKLIST_WORDS) or re.search(
        r"\bu\s?-?\d{2}\b", combined
    ):
        return False

    l_low = league_name.lower()
    c_low = country_name.lower() if country_name else ""

    for c_key, valid_leagues in ALLOWED_CONFIG.items():
        if c_key in c_low or c_key in l_low:
            if any(vl in l_low for vl in valid_leagues):
                return True

    for wl in ALLOWED_CONFIG["world"]:
        if wl in l_low:
            return True

    return False


# ==================== 4. EVALUATE 50' STATS ====================
def evaluate_50min_signal(stats_data):
    def get_stat(team_idx, stat_type):
        for item in stats_data[team_idx].get("statistics", []):
            if item["type"] == stat_type:
                val = item.get("value")
                return 0 if val is None else int(str(val).replace("%", ""))
        return 0

    h_corn = get_stat(0, "Corner Kicks")
    a_corn = get_stat(1, "Corner Kicks")
    tot_corn = h_corn + a_corn

    h_sot = get_stat(0, "Shots on Goal")
    a_sot = get_stat(1, "Shots on Goal")
    tot_sot = h_sot + a_sot

    h_box = get_stat(0, "Shots insidebox")
    a_box = get_stat(1, "Shots insidebox")
    tot_box = h_box + a_box

    h_shots = get_stat(0, "Total Shots")
    a_shots = get_stat(1, "Total Shots")
    tot_shots = h_shots + a_shots

    sot_over_confirmed = tot_sot >= 3
    box_over_confirmed = tot_box >= 4
    sot_under_confirmed = tot_sot <= 2
    box_under_confirmed = tot_box <= 2

    signal_type = "NEUTRAL"
    stars = "⭐️⭐️⭐️"
    advice = "ပွဲအခြေအနေ သာမန်ဖြစ်နေသဖြင့် မိနစ် ၇၀ အထိ စောင့်ကြည့်ပါ"

    if (
        tot_corn >= 3
        and tot_shots >= 9
        and sot_over_confirmed
        and box_over_confirmed
    ):
        signal_type = "STRONG_OVER"
        stars = "⭐️⭐️⭐️⭐️⭐️"
        advice = "ဖိအားပြင်း၊ ကန်ချက်နှင့် Box ထိုးဖောက်မှု အလွန်များသဖြင့် ဒုတိယပိုင်း Over Line ဝင်ရောက်နိုင်ပါသည်"
    elif tot_corn >= 3 and (sot_over_confirmed or tot_shots >= 9):
        signal_type = "MODERATE_OVER"
        stars = "⭐️⭐️⭐️⭐️"
        advice = "Over အလားအလာကောင်းသော်လည်း Confirmation အပြည့်မရသေးပါ"
    elif (
        tot_corn <= 3
        and tot_shots <= 8
        and sot_under_confirmed
        and box_under_confirmed
    ):
        signal_type = "STRONG_UNDER"
        stars = "⭐️⭐️⭐️⭐️⭐️"
        advice = "ဒေါင်းနားအေးပြီး Box ထဲကန်ချက် လုံးဝနည်းပါးသဖြင့် Under 10.5 / 9.5 ဝင်ရောက်နိုင်ပါသည်"
    elif tot_corn <= 3 and (sot_under_confirmed or tot_shots <= 8):
        signal_type = "MODERATE_UNDER"
        stars = "⭐️⭐️⭐️⭐️"
        advice = "Under အလားအလာငြိမ်သော်လည်း နောက်ဆုံး မိနစ် ၆၀ အထိ စောင့်ကြည့်သင့်ပါသည်"

    return {
        "tot_corn": tot_corn,
        "h_corn": h_corn,
        "a_corn": a_corn,
        "tot_sot": tot_sot,
        "h_sot": h_sot,
        "a_sot": a_sot,
        "tot_box": tot_box,
        "h_box": h_box,
        "a_box": a_box,
        "tot_shots": tot_shots,
        "h_shots": h_shots,
        "a_shots": a_shots,
        "sot_over_confirmed": sot_over_confirmed,
        "box_over_confirmed": box_over_confirmed,
        "sot_under_confirmed": sot_under_confirmed,
        "box_under_confirmed": box_under_confirmed,
        "signal_type": signal_type,
        "stars": stars,
        "advice": advice,
    }


# ==================== MAIN UI TABS ====================
tab_live, tab_prematch = st.tabs(
    ["🔴 Live In-Play Intelligence", "⏳ Upcoming Pre-Matches"]
)

# ==================== TAB 1: LIVE IN-PLAY ====================
with tab_live:
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown(
            "## ⚽ Live Pulse <span style='color:#00f2fe;'>Radar & Analysis</span>",
            unsafe_allow_html=True,
        )
    with col_t2:
        if st.button("🔄 Force Refresh"):
            st.rerun()

    raw_live, status_msg = fetch_from_api("fixtures?live=all")

    if not raw_live:
        st.error(f"⚠️ Live Connection Info: `{status_msg}`")
    else:
        live_fixtures = [
            f
            for f in raw_live
            if is_allowed_league(
                f["league"]["name"],
                f["league"].get("country", ""),
                f["teams"]["home"]["name"],
                f["teams"]["away"]["name"],
            )
        ]

        st.caption(
            f"✅ Status: **{status_msg}** &nbsp;|&nbsp; Whitelist Live: **{len(live_fixtures)} ပွဲ** (စုစုပေါင်း Live: {len(raw_live)} ပွဲ)"
        )

        golden_window_matches = [
            f
            for f in live_fixtures
            if 45 <= (f["fixture"]["status"]["elapsed"] or 0) <= 65
        ]

        # Top Hero Radar
        st.markdown(
            """
        <div class="radar-container">
            <h4 style="margin:0; color:#00f2fe;">⚡ 50' MINUTE ACTION RADAR</h4>
            <p style="margin:5px 0 0 0; font-size:13px; color:#8b949e;">
                မိနစ် ၄၅ မှ ၆၅ အတွင်း ရောက်ရှိနေသော Whitelist Major ပွဲစဉ်များ
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if golden_window_matches:
            for g_fix in golden_window_matches:
                g_home = g_fix["teams"]["home"]["name"]
                g_away = g_fix["teams"]["away"]["name"]
                g_league = g_fix["league"]["name"]
                g_country = g_fix["league"].get("country", "")
                g_min = g_fix["fixture"]["status"]["elapsed"] or 0
                g_sh = (
                    g_fix["goals"]["home"]
                    if g_fix["goals"]["home"] is not None
                    else 0
                )
                g_sa = (
                    g_fix["goals"]["away"]
                    if g_fix["goals"]["away"] is not None
                    else 0
                )

                col_r1, col_r2, col_r3 = st.columns([3, 2, 2])
                with col_r1:
                    st.markdown(
                        f"🏆 **<span style='color:#00f2fe;'>{g_league} ({g_country})</span>**",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"⚽ **{g_home}** vs **{g_away}**")
                with col_r2:
                    st.markdown(
                        f"⏱ <span class='badge-minute'>{g_min}'</span> &nbsp; 🥅 **`{g_sh} - {g_sa}`**",
                        unsafe_allow_html=True,
                    )
                with col_r3:
                    st.info(f"🎯 50' Window Active ({g_min}')")
                st.divider()
        else:
            st.caption(
                "⚡ လောလောဆယ် မိနစ် ၄၅ မှ ၆၅ အတွင်း Whitelist ပွဲစဉ်များ မရှိသေးပါ။"
            )

        st.markdown(
            f"### 📋 Verified Live Directory ({len(live_fixtures)} ပွဲ)"
        )

        for fix in live_fixtures:
            f_id = fix["fixture"]["id"]
            home = fix["teams"]["home"]["name"]
            away = fix["teams"]["away"]["name"]
            league = fix["league"]["name"]
            country = fix["league"].get("country", "")
            elapsed = fix["fixture"]["status"]["elapsed"] or 0
            status_short = fix["fixture"]["status"]["short"]

            score_h = fix["goals"]["home"] if fix["goals"]["home"] is not None else 0
            score_a = fix["goals"]["away"] if fix["goals"]["away"] is not None else 0

            ht_obj = fix.get("score", {}).get("halftime", {}) or {}
            ht_h = ht_obj.get("home", 0) or 0
            ht_a = ht_obj.get("away", 0) or 0

            with st.container():
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.markdown(
                        f"<span class='league-badge'>🏆 {league} &nbsp;•&nbsp; {country}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"### ⚽ {home} vs {away}")
                with c2:
                    st.markdown(f"## 🥅 `{score_h} - {score_a}`")
                    st.markdown(
                        f"<span class='badge-ht'>Half-Time: {ht_h} - {ht_a}</span>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown(
                        f"⏱ <span class='badge-minute'>{elapsed}' [{status_short}]</span>",
                        unsafe_allow_html=True,
                    )

                with st.expander(
                    f"📊 View 50' Live Metrics & AI Signal ({home} vs {away})"
                ):
                    stats_data, s_status = fetch_from_api(
                        f"fixtures/statistics?fixture={f_id}"
                    )

                    if not stats_data or len(stats_data) < 2:
                        st.warning(
                            "ဤပွဲအတွက် Live Statistics အသေးစိတ် မရရှိသေးပါ (ဒိုင်များမှ Live Data Update လုပ်နေဆဲဖြစ်နိုင်သည်)။"
                        )
                    else:
                        eval_res = evaluate_50min_signal(stats_data)

                        st.markdown("#### 📈 50th-Minute Metrics Snapshot")
                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.markdown(
                                f"""<div class='stat-pill'>
                                <div style='font-size:12px; color:#8b949e;'>🚩 TOTAL CORNERS</div>
                                <div style='font-size:22px; font-weight:bold; color:#00f2fe;'>{eval_res['tot_corn']}</div>
                                <div style='font-size:11px;'>({home} {eval_res['h_corn']} - {eval_res['a_corn']} {away})</div>
                            </div>""",
                                unsafe_allow_html=True,
                            )
                        with m2:
                            st.markdown(
                                f"""<div class='stat-pill'>
                                <div style='font-size:12px; color:#8b949e;'>🎯 ON TARGET</div>
                                <div style='font-size:22px; font-weight:bold; color:#00e676;'>{eval_res['tot_sot']}</div>
                                <div style='font-size:11px;'>({home} {eval_res['h_sot']} - {eval_res['a_sot']} {away})</div>
                            </div>""",
                                unsafe_allow_html=True,
                            )
                        with m3:
                            st.markdown(
                                f"""<div class='stat-pill'>
                                <div style='font-size:12px; color:#8b949e;'>📦 SHOTS IN-BOX</div>
                                <div style='font-size:22px; font-weight:bold; color:#ff9100;'>{eval_res['tot_box']}</div>
                                <div style='font-size:11px;'>({home} {eval_res['h_box']} - {eval_res['a_box']} {away})</div>
                            </div>""",
                                unsafe_allow_html=True,
                            )
                        with m4:
                            st.markdown(
                                f"""<div class='stat-pill'>
                                <div style='font-size:12px; color:#8b949e;'>👟 TOTAL SHOTS</div>
                                <div style='font-size:22px; font-weight:bold; color:#ffffff;'>{eval_res['tot_shots']}</div>
                                <div style='font-size:11px;'>({home} {eval_res['h_shots']} - {eval_res['a_shots']} {away})</div>
                            </div>""",
                                unsafe_allow_html=True,
                            )

                        st.markdown("#### ⚡ Strong Confirmation Checklist")
                        ck1, ck2 = st.columns(2)
                        with ck1:
                            if eval_res["sot_over_confirmed"]:
                                st.write(
                                    f"✅ **Shots on Target ≥ 3:** ({eval_res['tot_sot']} ကြိမ် - Over Confirmed)"
                                )
                            elif eval_res["sot_under_confirmed"]:
                                st.write(
                                    f"✅ **Shots on Target ≤ 2:** ({eval_res['tot_sot']} ကြိမ် - Under Confirmed)"
                                )
                            else:
                                st.write(
                                    f"⚠️ **Shots on Target:** ({eval_res['tot_sot']} ကြိမ် - Moderate)"
                                )
                        with ck2:
                            if eval_res["box_over_confirmed"]:
                                st.write(
                                    f"✅ **Shots Inside Box ≥ 4:** ({eval_res['tot_box']} ကြိမ် - Over Confirmed)"
                                )
                            elif eval_res["box_under_confirmed"]:
                                st.write(
                                    f"✅ **Shots Inside Box ≤ 2:** ({eval_res['tot_box']} ကြိမ် - Under Confirmed)"
                                )
                            else:
                                st.write(
                                    f"⚠️ **Shots Inside Box:** ({eval_res['tot_box']} ကြိမ် - Moderate)"
                                )

                        st.divider()
                        if "OVER" in eval_res["signal_type"]:
                            st.markdown(
                                f"<span class='badge-over'>{eval_res['stars']} {eval_res['signal_type']}</span>",
                                unsafe_allow_html=True,
                            )
                            st.success(
                                f"💡 **Recommended Action:** {eval_res['advice']}"
                            )
                        elif "UNDER" in eval_res["signal_type"]:
                            st.markdown(
                                f"<span class='badge-under'>{eval_res['stars']} {eval_res['signal_type']}</span>",
                                unsafe_allow_html=True,
                            )
                            st.error(
                                f"💡 **Recommended Action:** {eval_res['advice']}"
                            )
                        else:
                            st.info(
                                f"⚖️ **{eval_res['stars']} NEUTRAL:** {eval_res['advice']}"
                            )

                st.divider()

# ==================== TAB 2: UPCOMING PRE-MATCH ====================
with tab_prematch:
    # MMT Date Sync
    mmt_today = datetime.now(MMT_TIMEZONE).strftime("%Y-%m-%d")
    raw_today, pre_status = fetch_from_api(f"fixtures?date={mmt_today}")

    if not raw_today:
        st.error(f"⚠️ Pre-Match Fetch Info: `{pre_status}`")
        st.info("💡 API Key Limit သို့မဟုတ် Connection Status ကို စစ်ဆေးပေးပါဗျာ။")
    else:
        upcoming_list = []
        for fix in raw_today:
            # Matches not started or in-play today
            if fix["fixture"]["status"]["short"] in [
                "NS",
                "TBD",
                "1H",
                "HT",
                "2H",
            ]:
                l_name = fix["league"]["name"]
                country_name = fix["league"].get("country", "")
                h_name = fix["teams"]["home"]["name"]
                a_name = fix["teams"]["away"]["name"]

                if is_allowed_league(l_name, country_name, h_name, a_name):
                    upcoming_list.append({
                        "home": h_name,
                        "away": a_name,
                        "league": l_name,
                        "country": country_name,
                        "time_mmt": convert_to_mmt(fix["fixture"]["date"]),
                        "status": fix["fixture"]["status"]["short"],
                    })

        st.caption(
            f"✅ Connection: **{pre_status}** &nbsp;|&nbsp; Whitelist ပွဲများ: **{len(upcoming_list)} ပွဲ** (ယနေ့ စုစုပေါင်းပွဲစဉ်: {len(raw_today)} ပွဲ)"
        )

        if not upcoming_list:
            st.warning(
                "ယနေ့အတွက် ရွေးချယ်ထားသော Whitelist လိဂ်များတွင် ပွဲစဉ် မရှိသေးပါဗျာ။"
            )
        else:
            st.subheader(
                f"⏳ Today's Verified Pre-Matches ({len(upcoming_list)} ပွဲ)"
            )
            for m in upcoming_list:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### ⚽ {m['home']} vs {m['away']}")
                        st.write(
                            f"🏆 **{m['league']} ({m['country']})** | ⏰ စတင်မည့်အချိန်: **`{m['time_mmt']} (MMT)`**"
                        )
                    with col2:
                        st.metric(
                            label="Match Status",
                            value=f"Pro ({m['status']})",
                        )
                    st.divider()
