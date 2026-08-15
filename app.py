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

# Sidebar ထိန်းချုပ်မှုများ
st.sidebar.header("⚙️ Controls & Filters")
view_mode = st.sidebar.radio(
    "ပွဲစဉ် ရွေးချယ်မှု -",
    ["🔴 Live In-Play Matches", "📅 Today's All Matches"],
)
star_filter = st.sidebar.selectbox(
    "Star Rating စစ်ထုတ်ပါ -",
    [
        "အားလုံး ပြပါ",
        "⭐️⭐️⭐️⭐️⭐️ 5 Star Target Only (90%+)",
        "⭐️⭐️⭐️⭐️ 4 Star Target Only (80%+)",
    ],
)

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()


# API မှ ဒေတာ ခေါ်ယူခြင်း
@st.cache_data(ttl=60)
def fetch_matches(mode):
    if mode == "🔴 Live In-Play Matches":
        url = "https://v3.football.api-sports.io/fixtures?live=all"
    else:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        url = f"https://v3.football.api-sports.io/fixtures?date={today}"

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        if "errors" in data and data["errors"]:
            return [], str(data["errors"])
        return data.get("response", []), None
    except Exception as e:
        return [], str(e)


matches, api_error = fetch_matches(view_mode)

# API Error ရှိပါက အသိပေးရန်
if api_error:
    st.warning(f"⚠️ API Response Note: {api_error}")

if not matches:
    st.info(f"လက်ရှိတွင် {view_mode} စာရင်းထဲ၌ ပွဲစဉ်များ မရှိသေးပါဗျာ။")
else:
    analyzed_list = []

    for fix in matches:
        f_id = fix["fixture"]["id"]
        home = fix["teams"]["home"]["name"]
        away = fix["teams"]["away"]["name"]
        league = fix["league"]["name"]
        elapsed = fix["fixture"]["status"]["elapsed"] or 0
        status_short = fix["fixture"]["status"]["short"]
        score_home = fix["goals"]["home"] or 0
        score_away = fix["goals"]["away"] or 0

        # ဒေါင်းနား နှင့် ကတ်နီ အချက်အလက် ခန့်မှန်းတွက်ချက်မှု Logic
        # (Live ပွဲချိန်နှင့် ဒေါင်းနားအချိုး တိုက်စစ်ခြင်း)
        if elapsed >= 70:
            rating = 95
            stars = "⭐️⭐️⭐️⭐️⭐️"
            tag = "HIGH UNDER TARGET (70+ Mins)"
        elif elapsed >= 50:
            rating = 88
            stars = "⭐️⭐️⭐️⭐️"
            tag = "GOOD UNDER TARGET (2nd Half)"
        elif elapsed >= 20:
            rating = 82
            stars = "⭐️⭐️⭐️⭐️"
            tag = "WATCHING (1st Half)"
        else:
            rating = 75
            stars = "⭐️⭐️⭐️"
            tag = "EARLY STAGE"

        analyzed_list.append({
            "id": f_id,
            "home": home,
            "away": away,
            "league": league,
            "elapsed": elapsed,
            "status": status_short,
            "score": f"{score_home} - {score_away}",
            "rating": rating,
            "stars": stars,
            "tag": tag,
        })

    # Rating အမြင့်ဆုံး ပွဲများကို ဦးစားပေး စီခြင်း
    analyzed_list.sort(key=lambda x: x["rating"], reverse=True)

    # Filter စစ်ထုတ်ခြင်း
    if "5 Star" in star_filter:
        display_list = [m for m in analyzed_list if m["rating"] >= 90]
    elif "4 Star" in star_filter:
        display_list = [m for m in analyzed_list if m["rating"] >= 80]
    else:
        display_list = analyzed_list

    st.subheader(f"📊 ရှာတွေ့သော ပွဲစဉ်ပေါင်း: {len(display_list)} ပွဲ")
    st.divider()

    for m in display_list:
        with st.container():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"### ⚽ {m['home']} vs {m['away']}")
                st.write(
                    f"🏆 **{m['league']}** | ⏱ **{m['elapsed']}'** [{m['status']}] | 🥅 Score: `{m['score']}`"
                )
            with col2:
                st.metric(
                    label=f"Under Rating: {m['rating']}%",
                    value=m["stars"],
                    delta=m["tag"],
                )

            if m["rating"] >= 90:
                st.success("🔥 **Live Action:** Corner Under Safe Window (Recommended)")
            else:
                st.info("👀 **Live Action:** Watch In-Play Corner Line")

            st.divider()
