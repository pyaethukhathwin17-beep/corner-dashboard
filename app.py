import streamlit as st
import requests
from datetime import datetime, timezone, timedelta

# Page Configuration
st.set_page_config(page_title="Football Radar & Pre-match", page_icon="⚽", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1a2332;
        border: 1px solid #2e3e56;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .radar-box {
        background: linear-gradient(145deg, #102336, #0e1c2b);
        border: 1px solid #1e456d;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 20px;
    }
    .badge-live {
        background-color: #00c853;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 13px;
    }
    .badge-radar {
        background-color: #ff3d00;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# API Keys Configuration
API_KEYS = [
    st.secrets.get("API_KEY_1", "YOUR_API_KEY_HERE"),
    st.secrets.get("API_KEY_2", ""),
]
API_KEYS = [k for k in API_KEYS if k and k != "YOUR_API_KEY_HERE"]
if not API_KEYS:
    API_KEYS = ["YOUR_API_KEY_HERE"]

# Major League IDs
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

def call_api(endpoint, params):
    for idx, key in enumerate(API_KEYS):
        headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            'x-rapidapi-key': key
        }
        url = f"https://v3.football.api-sports.io/{endpoint}"
        try:
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if "response" in data:
                    return data["response"], f"Key #{idx+1} (OK)"
        except Exception:
            continue
    return [], "Connection Error / Limit Exceeded"

# Built-in Myanmar Timezone (UTC + 6:30)
MM_TZ = timezone(timedelta(hours=6, minutes=30))
now_mm = datetime.now(MM_TZ)
today_str = now_mm.strftime('%Y-%m-%d')

# Header & Refresh Button
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.title("⚽ Football Intelligence & Analysis")
with col_btn:
    st.write("")
    if st.button("🔄 Force Refresh"):
        st.cache_data.clear()
        st.rerun()

# Navigation Tabs
tab_live, tab_prematch = st.tabs(["🔴 Live In-Play Intelligence", "⏳ Upcoming Pre-Matches"])

# ----------------- TAB 1: LIVE IN-PLAY INTELLIGENCE -----------------
with tab_live:
    live_data, status_msg = call_api("fixtures", {"live": "all"})
    st.caption(f"✅ Connection Status: **{status_msg}** | စုစုပေါင်း Live ပွဲစဉ်: **{len(live_data)} ပွဲ**")

    if not live_data:
        st.info("လတ်တလော ယှဉ်ပြိုင်ကစားနေသော Live ပွဲစဉ်များ မရှိသေးပါဗျာ။")
    else:
        radar_matches = []
        other_matches = []

        for match in live_data:
            elapsed = match.get("fixture", {}).get("status", {}).get("elapsed", 0)
            if elapsed and 45 <= elapsed <= 65:
                radar_matches.append(match)
            else:
                other_matches.append(match)

        # 50' Action Radar Section
        st.markdown(f"""
        <div class="radar-box">
            <h3 style="color:#00e5ff; margin-top:0;">⚡ 50' MINUTE ACTION RADAR</h3>
            <p style="color:#90caf9; margin-bottom:0;">မိနစ် ၄၅ မှ ၆၅ အတွင်း ရောက်ရှိနေသော ပွဲစဉ်များ ({len(radar_matches)} ပွဲ)</p>
        </div>
        """, unsafe_allow_html=True)

        if radar_matches:
            for match in radar_matches:
                fix = match["fixture"]
                league = match["league"]
                teams = match["teams"]
                goals = match["goals"]
                elapsed = fix.get("status", {}).get("elapsed", 0)

                with st.container():
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-weight:600; color:#ffd54f; margin-bottom:4px;">🏆 {league.get('name')} ({league.get('country')})</div>
                        <div style="font-size:17px; font-weight:bold; margin-bottom:6px;">⚽ {teams['home']['name']} vs {teams['away']['name']}</div>
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

# ----------------- TAB 2: UPCOMING PRE-MATCHES -----------------
with tab_prematch:
    col_date, col_filter = st.columns([1, 2])
    with col_date:
        selected_date = st.date_input("ရက်စွဲ ရွေးချယ်ရန်", now_mm.date())
    with col_filter:
        view_mode = st.radio("ပွဲစဉ် အမျိုးအစား", ["ပွဲကြီးများသာ (Major Leagues)", "ပွဲစဉ်အားလုံး (All Fixtures)"], horizontal=True)

    date_query_str = selected_date.strftime('%Y-%m-%d')
    
    prematch_data, pre_status = call_api("fixtures", {
        "date": date_query_str,
        "timezone": "Asia/Yangon"
    })

    if not prematch_data:
        st.warning(f"ရက်စွဲ ({date_query_str}) အတွက် ပွဲစဉ်အချက်အလက် မရရှိနိုင်သေးပါဗျာ။")
    else:
        upcoming = [m for m in prematch_data if m.get("fixture", {}).get("status", {}).get("short") in ["NS", "TBD"]]
        
        if view_mode == "ပွဲကြီးများသာ (Major Leagues)":
            display_list = [m for m in upcoming if m.get("league", {}).get("id") in MAJOR_LEAGUES]
        else:
            display_list = upcoming

        st.caption(f"ရှာတွေ့သော ပွဲစဉ်အရေအတွက်: **{len(display_list)} ပွဲ**")

        if not display_list:
            if view_mode == "ပွဲကြီးများသာ (Major Leagues)":
                st.info("ဒီနေ့အတွက် သတ်မှတ်ထားသော ပွဲကြီးများ မရှိသေးပါဗျာ။ (အပေါ်ရှိ **'ပွဲစဉ်အားလုံး'** ကို ရွေးပြီး အခြားပွဲများကို ကြည့်ရှုနိုင်ပါသည်)")
            else:
                st.info("ဒီနေ့အတွက် ကစားရန်ကျန်ရှိသော ပွဲစဉ်များ မရှိသေးပါဗျာ။")
        else:
            for match in display_list:
                fix = match["fixture"]
                league = match["league"]
                teams = match["teams"]
                
                match_time_str = fix.get("date", "")
                try:
                    match_dt = datetime.fromisoformat(match_time_str)
                    formatted_time = match_dt.strftime("%I:%M %p")
                except Exception:
                    formatted_time = "TBD"

                with st.container():
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="color:#64b5f6; font-size:13px; font-weight:600;">🏆 {league.get('name')} ({league.get('country')})</div>
                        <div style="font-size:16px; font-weight:bold; margin:6px 0;">⚽ {teams['home']['name']} vs {teams['away']['name']}</div>
                        <div style="color:#b0bec5; font-size:14px;">⏰ စတင်မည့်အချိန်: <b style="color:#ffffff;">{formatted_time} (မြန်မာစံတော်ချိန်)</b></div>
                    </div>
                    """, unsafe_allow_html=True)
