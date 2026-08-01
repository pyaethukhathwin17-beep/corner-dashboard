from datetime import datetime
import requests
import streamlit as st


st.set_page_config(
    page_title="Corner Analytics V3",
    layout="wide"
)


st.title("⚽ Corner Under Analytics V3")


# ==========================
# API KEY
# ==========================

API_KEY = st.secrets.get("API_KEY", "")


if not API_KEY:

    st.warning(
        "⚠️ API Key မတွေ့ပါ"
    )

    st.stop()



headers = {
    "x-apisports-key": API_KEY
}



today = datetime.now().strftime("%Y-%m-%d")



# ==========================
# API REQUEST WITH CACHE
# ==========================


@st.cache_data(ttl=3600)
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

            st.error(
                f"API Error: {response.status_code}"
            )

            return {}


    except Exception as e:

        st.error(e)

        return {}



# ==========================
# FIXTURE FETCH
# ==========================


@st.cache_data(ttl=3600)
def get_today_fixtures():


    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures?date={today}"
    )


    data = api_get(url)


    return data.get(
        "response",
        []
    )



# ==========================
# BASIC FILTER
# ==========================


def filter_matches(fixtures):


    candidates = []


    for match in fixtures:


        status = (
            match["fixture"]
            ["status"]
            ["short"]
        )


        home = (
            match["teams"]
            ["home"]
            ["name"]
        )


        away = (
            match["teams"]
            ["away"]
            ["name"]
        )


        home_id = (
            match["teams"]
            ["home"]
            ["id"]
        )


        away_id = (
            match["teams"]
            ["away"]
            ["id"]
        )


        league = (
            match["league"]
            ["name"]
        )



        # Remove finished matches

        if status in [
            "FT",
            "AET",
            "PEN"
        ]:

            continue



        # Remove missing team data

        if not home_id or not away_id:

            continue



        candidates.append({

            "fixture_id":
                match["fixture"]["id"],

            "home":
                home,

            "away":
                away,

            "league":
                league,

            "home_id":
                home_id,

            "away_id":
                away_id

        })


    return candidates



# ==========================
# MAIN
# ==========================


st.divider()

st.header(
    "🎯 Auto Fixture Scanner"
)



fixtures = get_today_fixtures()



if not fixtures:


    st.warning(
        "ဒီနေ့ Fixture Data မရပါ"
    )


    st.stop()



st.success(
    f"Total Fixtures Found: {len(fixtures)}"
)



# Free API Protection
# Statistics မခေါ်ခင် Candidate အနည်းငယ်သာထားမည်

candidates = filter_matches(
    fixtures
)



st.info(
    f"Candidate Matches: {len(candidates)}"
)



for match in candidates[:10]:


    st.write(
        f"⚽ {match['home']} vs {match['away']}"
    )


    st.write(
        f"🏆 {match['league']}"
    )


    st.write(
        f"Fixture ID: {match['fixture_id']}"
    )


    st.divider()
    # ==========================
# STATISTICS API
# ==========================


@st.cache_data(ttl=3600)
def get_statistics(fixture_id):

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures/statistics?fixture={fixture_id}"
    )


    data = api_get(url)


    return data.get(
        "response",
        []
    )



# ==========================
# STAT EXTRACTOR
# ==========================


def get_stat(stats, team_id, stat_name):


    for team in stats:


        if team["team"]["id"] == team_id:


            for item in team.get(
                "statistics",
                []
            ):


                if item["type"] == stat_name:


                    value = item["value"]


                    if value is None:

                        return 0


                    if isinstance(value, str):

                        value = (
                            value
                            .replace("%","")
                        )


                    try:

                        return float(value)

                    except:

                        return 0


    return 0



# ==========================
# UNDER RATING ENGINE
# ==========================


def calculate_under_rating(
    total_corner,
    total_sot,
    possession_diff
):


    rating = 100


    reasons = []



    # Corner Pressure

    if total_corner >= 12:

        rating -= 30

        reasons.append(
            "High Corner Volume"
        )


    elif total_corner >= 10:

        rating -= 15

        reasons.append(
            "Medium Corner Volume"
        )


    else:

        reasons.append(
            "Low Corner Volume"
        )



    # Shots On Target


    if total_sot >= 8:

        rating -= 20

        reasons.append(
            "High Shot Pressure"
        )


    elif total_sot >= 6:

        rating -= 10

        reasons.append(
            "Medium Shot Pressure"
        )


    else:

        reasons.append(
            "Low Shot Pressure"
        )



    # Possession


    if possession_diff >= 30:

        rating -= 15

        reasons.append(
            "One Side Dominance"
        )


    elif possession_diff >= 20:

        rating -= 10

        reasons.append(
            "Possession Difference"
        )


    else:

        reasons.append(
            "Balanced Possession"
        )



    if rating < 0:

        rating = 0



    return rating, reasons



# ==========================
# ANALYSIS START
# ==========================


st.divider()

st.header(
    "🎯 Corner Under Predictions"
)



results = []



for match in candidates[:10]:


    stats = get_statistics(
        match["fixture_id"]
    )


    if not stats:

        continue



    home_corner = get_stat(
        stats,
        match["home_id"],
        "Corner Kicks"
    )


    away_corner = get_stat(
        stats,
        match["away_id"],
        "Corner Kicks"
    )



    home_sot = get_stat(
        stats,
        match["home_id"],
        "Shots on Goal"
    )


    away_sot = get_stat(
        stats,
        match["away_id"],
        "Shots on Goal"
    )



    home_pos = get_stat(
        stats,
        match["home_id"],
        "Ball Possession"
    )


    away_pos = get_stat(
        stats,
        match["away_id"],
        "Ball Possession"
    )



    total_corner = (
        home_corner +
        away_corner
    )


    total_sot = (
        home_sot +
        away_sot
    )


    possession_diff = abs(
        home_pos -
        away_pos
    )



    rating, reasons = calculate_under_rating(
        total_corner,
        total_sot,
        possession_diff
    )



    results.append({

        "match":
            f"{match['home']} vs {match['away']}",

        "league":
            match["league"],

        "corner":
            total_corner,

        "shots":
            total_sot,

        "possession":
            possession_diff,

        "rating":
            rating,

        "reasons":
            reasons

    })



# Sort Highest Rating First

results.sort(
    key=lambda x:x["rating"],
    reverse=True
)



for item in results:


    st.subheader(
        f"⚽ {item['match']}"
    )


    st.write(
        f"🏆 League: {item['league']}"
    )


    col1,col2,col3,col4 = st.columns(4)


    with col1:

        st.metric(
            "Total Corner",
            item["corner"]
        )


    with col2:

        st.metric(
            "Shots On Target",
            item["shots"]
        )


    with col3:

        st.metric(
            "Possession Diff",
            item["possession"]
        )


    with col4:

        st.metric(
            "Under Rating",
            f"{item['rating']}%"
        )



    st.write(
        "Reason:"
    )


    for r in item["reasons"]:

        st.write(
            "✅",
            r
        )



    if item["rating"] >= 85:

        st.success(
            "⭐⭐⭐⭐⭐ HIGH CONFIDENCE UNDER"
        )


    elif item["rating"] >= 70:

        st.info(
            "⭐⭐⭐ GOOD UNDER TARGET"
        )


    else:

        st.warning(
            "LOW CONFIDENCE"
        )


    st.divider()
