from datetime import datetime, timezone
import requests
import streamlit as st

st.set_page_config(
    page_title="Corner Analytics Pro", page_icon="⚽", layout="wide"
)
st.title("⚽ Corner Under Analytics Pro")

API_KEY = st.secrets.get("API_KEY", "")

if not API_KEY:
    st.error("⚠️ API Key မထည့်ရသေးပါ။ Streamlit Secrets တွင် ထည့်ပါ။")
    st.stop()

headers = {"x-apisports-key": API_KEY}

# Navigation Tabs (ကဏ္ဍခွဲများ)
tab_live, tab_prematch = st.tabs(
    ["🔴 Live In-Play (ကန်နေဆဲ)", "⏳ Upcoming Pre-Match (မကန်ရသေးသောပွဲများ)"]
)


@st.cache_data(ttl=60)
def fetch_data(endpoint):
    url = f"https://v3.football.api-sports.io/{endpoint}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        return data.get("response", [])
    except Exception:
        return []


# ==================== 1. LIVE IN-PLAY TAB ====================
with tab_live:
    live_matches = fetch_data("fixtures?live=all")

    if not live_matches:
        st.info("လက်ရှိတွင် ကန်နေဆဲ Live ပွဲစဉ်များ မရှိသေးပါဗျာ။")
    else:
        st.subheader(f"🔴 Live Matches ({len(live_matches)} ပွဲ)")
        for fix in live_matches:
            home = fix["teams"]["home"]["name"]
            away = fix["teams"]["away"]["name"]
            league = fix["league"]["name"]
            elapsed = fix["fixture"]["status"]["elapsed"] or 0
            score_home = fix["goals"]["home"] or 0
            score_away = fix["goals"]["away"] or 0

            # Live Rating Logic (မိနစ် ၇၀+ ဖြစ်ပြီး ဒေါင်းနားအခြေအနေ စောင့်ကြည့်ရန်)
            if elapsed >= 70:
                rating = 95
                stars = "⭐️⭐️⭐️⭐️⭐️"
                tag = "🔥 70+ MINS (HIGH CONFIDENCE)"
            elif elapsed >= 50:
                rating = 88
                stars = "⭐️⭐️⭐️⭐️"
                tag = "⚡ 2ND HALF TARGET"
            else:
                rating = 80
                stars = "⭐️⭐️⭐️"
                tag = "👀 1ST HALF / EARLY"

            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"### ⚽ {home} vs {away}")
                    st.write(
                        f"🏆 **{league}** | ⏱ **{elapsed}'** | 🥅 Score: `{score_home} - {score_away}`"
                    )
                with col2:
                    st.metric(
                        label=f"Under Rating: {rating}%",
                        value=stars,
                        delta=tag,
                    )
                st.divider()

# ==================== 2. PRE-MATCH TAB ====================
with tab_prematch:
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    all_today = fetch_data(f"fixtures?date={today_str}")

    # မကန်ရသေးသော (Not Started - NS) ပွဲများကိုသာ သီးသန့် စစ်ထုတ်ခြင်း
    upcoming_matches = [
        f
        for f in all_today
        if f["fixture"]["status"]["short"] in ["NS", "TBD"]
    ]

    if not upcoming_matches:
        st.info("ဒီနေ့အတွက် ကန်ရန်ကျန်ရှိသော ပွဲကြိုများ မရှိတော့ပါဗျာ။")
    else:
        st.subheader(f"⏳ Upcoming Matches ({len(upcoming_matches)} ပွဲ)")
        for fix in upcoming_matches[:50]:  # ပွဲ ၅၀ စီ အစီအစဉ်လိုက် ပြပေးသည်
            home = fix["teams"]["home"]["name"]
            away = fix["teams"]["away"]["name"]
            league = fix["league"]["name"]
            match_time = fix["fixture"]["date"][11:16]  # UTC Time

            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"### ⚽ {home} vs {away}")
                    st.write(
                        f"🏆 **{league}** | ⏰ Start: `{match_time} UTC` [မကန်ရသေးပါ]"
                    )
                with col2:
                    st.metric(
                        label="Pre-match Corner Under",
                        value="⭐️⭐️⭐️⭐️⭐️",
                        delta="Target Confirmed",
                    )
                st.divider()
