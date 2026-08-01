from datetime import datetime
import requests
import streamlit as st

st.set_page_config(page_title="Corner Analytics", layout="wide")
st.title("⚽ Corner Under Analytics")

# Streamlit Secrets မှ API Key ခေါ်ယူခြင်း
API_KEY = st.secrets.get("API_KEY", "")

if not API_KEY:
    st.warning("⚠️ API Key မထည့်ရသေးပါ။ Streamlit Cloud Secrets တွင် ထည့်ပါ။")
    st.stop()

# ဒီနေ့ ရက်စွဲ ရယူခြင်း
today_date = datetime.now().strftime("%Y-%m-%d")
st.subheader(f"🔥 Today's Live/Upcoming Matches ({today_date})")

# API-Sports Header
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


# API မှ ဒီနေ့ပွဲစဉ်များ ခေါ်ယူခြင်း
fixtures = get_today_fixtures(today_date)

if not fixtures:
    st.info(
        "ဒီနေ့အတွက် ပွဲစဉ်များ မရှိသေးပါ သို့မဟုတ် API Data ခေါ်ယူ၍ မရသေးပါ။"
    )
else:
    st.success(f"ဒီနေ့အတွက် စုစုပေါင်း **{len(fixtures)}** ပွဲ ရှာတွေ့ထားပါသည်။")

    # ပွဲစဉ်များကို စာရင်းလိုက် ပြသခြင်း
    for fix in fixtures[:30]:  # Free API Limit မကုန်အောင် ပွဲ ၃၀ စီ ခွဲပြထားသည်
        home_team = fix["teams"]["home"]["name"]
        away_team = fix["teams"]["away"]["name"]
        league_name = fix["league"]["name"]
        status = fix["fixture"]["status"]["short"]
        match_time = fix["fixture"]["date"][11:16]

        with st.expander(
            f"⚽ {home_team} vs {away_team} ({league_name}) - {match_time} UTC [{status}]"
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"• **League:** {league_name}")
                st.write(f"• **Status:** {status}")
            with col2:
                st.write(f"• **Match ID:** {fix['fixture']['id']}")
                st.info("Analysis: Pre-match Corner Data target")
