import streamlit as st
import requests
from datetime import datetime, timezone, timedelta

# Page Configuration
st.set_page_config(page_title="Football Intelligence", page_icon="⚽", layout="wide")

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1a2332;
        border: 1px solid #2e3e56;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 10px;
    }
    .radar-box {
        background: linear-gradient(145deg, #102336, #0e1c2b);
        border: 1px solid #1e456d;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .badge-live {
        background-color: #00c853;
        color: white;
        padding: 2px 7px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 12px;
    }
    .badge-radar {
        background-color: #ff3d00;
        color: white;
        padding: 3px 9px;
        border-radius: 15px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- API CONFIGURATION -----------------
# API Key များကို Streamlit Secrets မှ ယူမည် (မရှိပါက Default Key ထည့်ရန်)
DEFAULT_KEYS = [
    st.secrets.get("API_KEY_1", ""),
    st.secrets.get("API_KEY_2", ""),
    st.secrets.get("API_KEY_3", "")
]
API_KEYS = [k for k in DEFAULT_KEYS if k.strip()]

# API Key လုံးဝ မရှိသေးပါက ယာယီ ထည့်သွင်းရန် Sidebar
if not API_KEYS:
    user_key = st.sidebar.text_input("🔑 API-Sports Key ထည့်ပါ", type="password")
    if user_key:
        API_KEYS = [user_key.strip()]

# Major Leagues List
MAJOR_LEAGUES = {
    39: "Premier League (England)",
    140: "La Liga (Spain)",
    135: "Serie A (Italy)",
    78: "Bundesliga (Germany)",
    61: "Ligue 1 (France)",
    2: "UEFA Champions League",
    3: "UEFA Europa League",
    848: "UEFA Conference League"
}

# ----------------- API CALL WITH CACHING -----------------
@st.cache_data(ttl=45, show_spinner=False)
def fetch_live_matches(keys):
    return fetch_api_data("fixtures", {"live": "all"}, keys)

@st.cache_data(ttl=300, show_spinner=False)
def fetch_prematches(date_str, keys):
    return fetch_api_data("fixtures", {"date": date_str, "timezone": "Asia/Yangon"}, keys)

def fetch_api_data(endpoint, params, keys):
    if not keys:
        return [], "No API Key Found", {}

    for idx, key in enumerate(keys):
        # API-Sports direct key နှင့် RapidAPI Key ၂ မျိုးစလုံး အလုပ်လုပ်စေရန် Header ပေးပို့ခြင်း
        headers = {
            "x-apisports-key": key,
            "x-rapidapi-key": key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
        url = f"https://v3.football.api-sports.io/{endpoint}"
        try:
            res = requests.get(url, headers=headers, params=params, timeout=12)
            data = res.json()
            
            # API Errors စစ်ဆေးခြင်း
            errors = data.get("errors", {})
            if errors:
                return [], f"Key #{idx+1} Error", errors

            if res.status_code == 200 and "response" in data:
                return data["response"], f"Key #{idx+1} (OK)", {}
        except Exception as e:
            continue

    return [], "Connection / Timeout Error", {}

# Myanmar Time
MM_TZ = timezone(timedelta(hours=6, minutes=30))
now_mm = datetime.now(MM_TZ)

# Header Bar
col_t, col_b = st.columns([3, 1])
with col_t:
    st.title("⚽ Football Intelligence & Analysis")
with col_b:
    st.write("")
    if st.button("🔄 Force Refresh"):
        st.cache_data.clear()
        st.rerun()

tab_live, tab_prematch = st.tabs(["🔴 Live In-Play Intelligence", "⏳ Upcoming Pre-Matches"])

# ----------------- TAB 1: LIVE -----------------
with tab_live:
    live_matches, status_txt, errors = fetch_live_matches(tuple(API_KEYS))
    
    if errors:
        st.error(f"⚠️ API Error: {errors}")
    
    st.caption(f"Connection Status: **{status_txt}** | စုစုပေါင်း Live ပွဲစဉ်: **{len(live_matches)} ပွဲ**")

    if not live_matches:
        st.info("လတ်တလော ယှဉ်ပြိုင်ကစားနေသော Live ပွဲစဉ်များ မရှိသေးပါဗျာ။")
    else:
        radar_matches = []
        other_matches = []

        for m in live_matches:
            elapsed = m.get("fixture", {}).get("status", {}).get("elapsed", 0)
            if elapsed and 45 <= elapsed <= 65:
                radar_matches.append(m)
            else:
                other_matches.append(m)

        st.markdown(f"""
        <div class="radar-box">
            <h4 style="color:#00e5ff; margin:0 0 6px 0;">⚡ 50' MINUTE ACTION RADAR</h4>
            <span style="color:#90caf9;">မိနစ် ၄၅ မှ ၆၅ အတွင်း ရောက်ရှိနေသော ပွဲစဉ်များ ({len(radar_matches)} ပွဲ)</span>
        </div>
        """, unsafe_allow_html=True)

        if radar_matches:
            for match in radar_matches:
                fix = match["fixture"]
                league = match["league"]
                teams = match["teams"]
                goals = match["goals"]
                elapsed = fix.get("status", {}).get("elapsed", 0)

                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-weight:600; color:#ffd54f; font-size:13px;">🏆 {league.get('name')} ({league.get('country')})</div>
                    <div style="font-size:16px; font-weight:bold; margin:4px 0;">⚽ {teams['home']['name']} vs {teams['away']['name']}</div>
                    <div>
                        <span class="badge-live">⏱️ {elapsed}'</span> &nbsp;
                        <span style="font-weight:bold;">🥅 {goals['home'] if goals['home'] is not None else 0} - {goals['away'] if goals['away'] is not None else 0}</span> &nbsp;
                        <span class="badge-radar">🎯 50' Window Active ({elapsed}')</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("လက်ရှိတွင် မိနစ် ၄၅-၆၅ ကြား ပွဲစဉ် မရှိသေးပါ။")

        with st.expander(f"အခြား Live ပွဲစဉ်များ ကြည့်ရန် ({len(other_matches)} ပွဲ)"):
            for match in other_matches:
                fix = match["fixture"]
                league = match["league"]
                teams = match["teams"]
                goals = match["goals"]
                elapsed = fix.get("status", {}).get("elapsed", 0)
                st.write(f"🏆 **{league.get('name')}** | ⚽ **{teams['home']['name']}** {goals['home']} - {goals['away']} **{teams['away']['name']}** (⏱️ {elapsed}')")
                st.divider()

# ----------------- TAB 2: PRE-MATCHES -----------------
with tab_prematch:
    c_date, c_view = st.columns([1, 2])
    with c_date:
        selected_date = st.date_input("ရက်စွဲ ရွေးချယ်ရန်", now_mm.date())
    with c_view:
        view_mode = st.radio("ပွဲစဉ် အမျိုးအစား", ["ပွဲစဉ်အားလုံး (All Fixtures)", "ပွဲကြီးများသာ (Major Leagues)"], horizontal=True)

    date_str = selected_date.strftime('%Y-%m-%d')
    pre_matches, pre_status, pre_errors = fetch_prematches(date_str, tuple(API_KEYS))

    if pre_errors:
        st.error(f"⚠️ API Error: {pre_errors}")

    if not pre_matches:
        st.warning(f"ရက်စွဲ ({date_str}) အတွက် ပွဲစဉ်အချက်အလက် မရရှိနိုင်သေးပါဗျာ။")
    else:
        # Not Started / TBD matches
        upcoming = [m for m in pre_matches if m.get("fixture", {}).get("status", {}).get("short") in ["NS", "TBD"]]

        if view_mode == "ပွဲကြီးများသာ (Major Leagues)":
            display_list = [m for m in upcoming if m.get("league", {}).get("id") in MAJOR_LEAGUES]
        else:
            display_list = upcoming

        st.caption(f"ရှာတွေ့သော ပွဲစဉ်အရေအတွက်: **{len(display_list)} ပွဲ**")

        if not display_list:
            st.info("ဒီနေ့အတွက် ကစားရန်ကျန်ရှိသော ပွဲစဉ် မရှိသေးပါဗျာ။")
        else:
            for match in display_list:
                fix = match["fixture"]
                league = match["league"]
                teams = match["teams"]
                
                # Match start time (HH:MM)
                match_time_str = fix.get("date", "")
                try:
                    match_dt = datetime.fromisoformat(match_time_str)
                    formatted_time = match_dt.strftime("%I:%M %p")
                except Exception:
                    formatted_time = "TBD"

                st.markdown(f"""
                <div class="metric-card">
                    <div style="color:#64b5f6; font-size:13px; font-weight:600;">🏆 {league.get('name')} ({league.get('country')})</div>
                    <div style="font-size:16px; font-weight:bold; margin:4px 0;">⚽ {teams['home']['name']} vs {teams['away']['name']}</div>
                    <div style="color:#b0bec5; font-size:13px;">⏰ စတင်မည့်အချိန်: <b style="color:#ffffff;">{formatted_time} (မြန်မာစံတော်ချိန်)</b></div>
                </div>
                """, unsafe_allow_html=True)
