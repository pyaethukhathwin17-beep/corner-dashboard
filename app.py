import hashlib
from datetime import datetime
import requests
import streamlit as st

st.set_page_config(page_title="Corner Analytics", layout="wide")
st.title("⚽ Corner Under Analytics")

API_KEY = st.secrets.get("API_KEY", "")

if not API_KEY:
    st.warning("⚠️ API Key မထည့်ရသေးပါ။ Streamlit Cloud Secrets တွင် ထည့်ပါ။")
    st.stop()

today_date = datetime.now().strftime("%Y-%m-%d")
headers = {"x-apisports-key": API_KEY}


@st.cache_data(ttl=1800)
def get_today_fixtures(date_str):
    url = f"https://v3.football.api-sports.io/fixtures?date={date_str}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("response", [])
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    return []


fixtures = get_today_fixtures(today_date)

if not fixtures:
    st.info("ဒီနေ့အတွက် ပွဲစဉ်များ မရှိသေးပါ သို့မဟုတ် API Data ခေါ်ယူ၍ မရသေးပါ။")
else:
    analyzed_matches = []

    for fix in fixtures:
    home_team = fix["teams"]["home"]["name"]
    away_team = fix["teams"]["away"]["name"]
    league_name = fix["league"]["name"]
    status = fix["fixture"]["status"]["short"]
    match_time = fix["fixture"]["date"][11:16]

    # Initial Rating (Statistics မထည့်ရသေးတဲ့ Base Version)
    rating = 50

    # နောက်ပိုင်းမှာ ဒီနေရာထဲကို
    # xG
    # Shots
    # Corners
    # Form
    # Home/Away Stats
    # တွေ ထည့်သွားမည်

    if rating >= 90:
        stars = "⭐️⭐️⭐️⭐️⭐️"
        tag = "HIGH CONFIDENCE (5 STAR)"
    elif rating >= 80:
        stars = "⭐️⭐️⭐️⭐️"
        tag = "MEDIUM CONFIDENCE (4 STAR)"
    elif rating >= 70:
        stars = "⭐️⭐️⭐️"
        tag = "NORMAL TARGET"
    else:
        stars = "⭐️⭐️"
        tag = "LOW CONFIDENCE"

    analyzed_matches.append({
        "home": home_team,
        "away": away_team,
        "league": league_name,
        "status": status,
        "time": match_time,
        "rating": rating,
        "stars": stars,
        "tag": tag,
    })

# Rating အမြင့်ဆုံးပွဲကို အပေါ်မှာထားခြင်း
analyzed_matches.sort(key=lambda x: x["rating"], reverse=True)

    # UI Filter Selector
    st.subheader("🎯 Filter Matches by Rating")
    filter_option = st.selectbox(
        "ရွေးချယ်လိုသော Star Rating စစ်ထုတ်ပါ -",
        [
            "🔥 All Recommended Matches",
            "⭐️⭐️⭐️⭐️⭐️ 5 Star Target Only (90%+ Rating)",
            "⭐️⭐️⭐️⭐️ 4 Star Target Only (80%+ Rating)",
        ],
    )

    filtered_list = analyzed_matches
    if "5 Star Target Only" in filter_option:
        filtered_list = [m for m in analyzed_matches if m["rating"] >= 90]
    elif "4 Star Target Only" in filter_option:
        filtered_list = [m for m in analyzed_matches if m["rating"] >= 80]

    st.write(f"📊 ရှာတွေ့သော ပွဲစဉ်ပေါင်း: **{len(filtered_list)}** ပွဲ")
    st.divider()

    # Cards Display
    for m in filtered_list:
        with st.container():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"### ⚽ {m['home']} vs {m['away']}")
                st.write(
                    f"🏆 **League:** {m['league']} | ⏰ **Time:** {m['time']} UTC [{m['status']}]"
                )
            with col2:
                st.metric(
                    label=f"Under Rating: {m['rating']}%",
                    value=m["stars"],
                    delta=m["tag"],
                )

            if m["rating"] >= 90:
                st.success("✅ **Recommendation:** Prematch / Live Corner Under")
            else:
                st.info("⚠️ **Recommendation:** Watch Live Odds for Corner Under")

            st.divider()
