from datetime import datetime
import requests
import streamlit as st

st.set_page_config(
    page_title="Corner Analytics",
    layout="wide"
)

st.title("⚽ Corner Analytics - Data Test Version")

API_KEY = st.secrets.get("API_KEY", "")

if not API_KEY:
    st.warning("⚠️ API Key မတွေ့ပါ")
    st.stop()

headers = {
    "x-apisports-key": API_KEY
}

today_date = datetime.now().strftime("%Y-%m-%d")

# ==================================
# API FUNCTIONS
# ==================================

@st.cache_data(ttl=1800)
def api_get(url):
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")

    except Exception as e:
        st.error(f"Connection Error: {e}")

    return {}


@st.cache_data(ttl=1800)
def get_today_fixtures():
    url = f"https://v3.football.api-sports.io/fixtures?date={today_date}"
    data = api_get(url)
    return data.get("response", [])


@st.cache_data(ttl=1800)
def get_fixture_statistics(fixture_id):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    data = api_get(url)
    return data.get("response", [])


@st.cache_data(ttl=1800)
def get_team_last_matches(team_id):
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5"
    data = api_get(url)
    return data.get("response", [])


# ==================================
# CORNER EXTRACTION
# ==================================

def extract_team_corner(stats, team_id):
    if not stats:
        return 0

    for team in stats:
        if team.get("team", {}).get("id") == team_id:
            for item in team.get("statistics", []):
                if item.get("type") == "Corner Kicks":
                    value = item.get("value")
                    if value is not None:
                        return float(value)

    return 0


def get_team_corner_average(team_id):
    matches = get_team_last_matches(team_id)
    corners = []

    for match in matches[:5]:
        fixture_id = match["fixture"]["id"]
        stats = get_fixture_statistics(fixture_id)
        corner = extract_team_corner(stats, team_id)

        if corner > 0:
            corners.append(corner)

    if not corners:
        return 0

    return round(sum(corners) / len(corners), 2)


def average(values):
    if not values:
        return 0
    return round(sum(values) / len(values), 2)


# ==================================
# ANALYSIS
# ==================================

st.divider()
st.header("🎯 Corner Under Analysis")

fixtures = get_today_fixtures()

if not fixtures:
    st.info("ဒီနေ့ Fixture မတွေ့ပါ")
    st.stop()

st.success(f"Fixture Found: {len(fixtures)}")

# ပထမ 3 ပွဲသာ စစ်ဆေးမည်
fixtures = fixtures[:3]

for fix in fixtures:
    fixture_id = fix["fixture"]["id"]
    home_id = fix["teams"]["home"]["id"]
    away_id = fix["teams"]["away"]["id"]

    home = fix["teams"]["home"]["name"]
    away = fix["teams"]["away"]["name"]

    home_corner = get_team_corner_average(home_id)
    away_corner = get_team_corner_average(away_id)

    expected_corner = round(home_corner + away_corner, 2)

    st.subheader(f"⚽ {home} vs {away}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Home Corner Average", home_corner)

    with col2:
        st.metric("Away Corner Average", away_corner)

    with col3:
        st.metric("Expected Corner", expected_corner)

    # ==============================
    # RATING
    # ==============================

    if expected_corner == 0:
        st.warning("⚠️ Corner Data မရသေးပါ - Rating မတွက်ပါ")
    else:
        rating = 50

        if expected_corner <= 8.5:
            rating += 25
        elif expected_corner <= 10:
            rating += 15
        elif expected_corner <= 12:
            rating += 5
        else:
            rating -= 20

        if rating > 100:
            rating = 100

        if rating < 0:
            rating = 0

        if rating >= 90:
            level = "⭐⭐⭐⭐⭐ HIGH CONFIDENCE"
        elif rating >= 80:
            level = "⭐⭐⭐⭐ GOOD"
        elif rating >= 70:
            level = "⭐⭐⭐ NORMAL"
        else:
            level = "⭐⭐ LOW"

        st.success(f"{level} | Under Rating {rating}%")

    st.divider()
