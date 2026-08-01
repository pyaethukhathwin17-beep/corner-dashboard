from datetime import datetime
import requests
import streamlit as st


st.set_page_config(
    page_title="Corner Analytics V1",
    layout="wide"
)


st.title("⚽ Corner Under Analytics V1")


API_KEY = st.secrets.get("API_KEY", "")


if not API_KEY:
    st.warning(
        "⚠️ API Key မတွေ့ပါ။ Streamlit Secrets တွင် ထည့်ပါ။"
    )
    st.stop()



headers = {
    "x-apisports-key": API_KEY
}



today_date = datetime.now().strftime("%Y-%m-%d")



# ==============================
# API FUNCTIONS
# ==============================


@st.cache_data(ttl=1800)
def get_today_fixtures(date):

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures?date={date}"
    )

    try:

        r = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if r.status_code == 200:
            return r.json().get("response", [])

    except Exception as e:

        st.error(e)

    return []



@st.cache_data(ttl=1800)
def get_team_last_matches(team_id):

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures?team={team_id}&last=5"
    )

    try:

        r = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if r.status_code == 200:
            return r.json().get("response", [])

    except Exception as e:

        st.error(e)

    return []



@st.cache_data(ttl=1800)
def get_fixture_statistics(fixture_id):

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures/statistics?fixture={fixture_id}"
    )


    try:

        r = requests.get(
            url,
            headers=headers,
            timeout=10
        )


        if r.status_code == 200:
            return r.json().get("response", [])


    except Exception as e:

        st.error(e)


    return []



# ==============================
# CORNER CALCULATION
# ==============================


def extract_corners(statistics, team_id):

    for team in statistics:

        if team["team"]["id"] == team_id:

            for item in team.get("statistics", []):

                st.write(
                    "DEBUG:",
                    item
                )

                if "Corner" in item["type"]:

                    value = item["value"]

                    if value is not None:

                        return float(value)

    return 0



def calculate_average(values):

    if len(values) == 0:

        return 0

    return round(
        sum(values) / len(values),
        2
    )
    # ==============================
# ANALYSIS ENGINE
# ==============================


def calculate_rating(expected_corner, total_average):

    score = 50


    # Expected Corner Score

    if expected_corner <= 8.5:

        score += 25

    elif expected_corner <= 10:

        score += 15

    elif expected_corner <= 12:

        score += 5

    else:

        score -= 20



    # Average Corner Score

    if total_average <= 9:

        score += 15

    elif total_average <= 11:

        score += 5

    else:

        score -= 10



    # Limit Score

    if score > 100:

        score = 100

    if score < 0:

        score = 0


    return score




# ==============================
# MAIN PROGRAM
# ==============================


fixtures = get_today_fixtures(today_date)



if not fixtures:

    st.info(
        "ဒီနေ့အတွက် Fixture မရှိပါ။"
    )


else:


    analyzed_matches = []


    # Free API Limit ထိန်းရန်
    fixtures = fixtures[:10]



    for fix in fixtures:


        fixture_id = fix["fixture"]["id"]


        home_id = fix["teams"]["home"]["id"]

        away_id = fix["teams"]["away"]["id"]


        home_name = fix["teams"]["home"]["name"]

        away_name = fix["teams"]["away"]["name"]



        league = fix["league"]["name"]



        home_corners = []

        away_corners = []



        # Home Last 5

        home_matches = get_team_last_matches(home_id)



        for match in home_matches[:5]:


            stats = get_fixture_statistics(
                match["fixture"]["id"]
            )


            corner = extract_corners(
                stats,
                home_id
            )


            if corner > 0:

                home_corners.append(corner)




        # Away Last 5

        away_matches = get_team_last_matches(away_id)



        for match in away_matches[:5]:


            stats = get_fixture_statistics(
                match["fixture"]["id"]
            )


            corner = extract_corners(
                stats,
                away_id
            )


            if corner > 0:

                away_corners.append(corner)




        home_avg = calculate_average(
            home_corners
        )


        away_avg = calculate_average(
            away_corners
        )



        expected_corner = round(
            (home_avg + away_avg),
            2
        )



        total_average = round(
            (home_avg + away_avg),
            2
        )



        rating = calculate_rating(
            expected_corner,
            total_average
        )



        if rating >= 90:

            stars = "⭐⭐⭐⭐⭐"

            tag = "HIGH CONFIDENCE"


        elif rating >= 80:

            stars = "⭐⭐⭐⭐"

            tag = "GOOD TARGET"


        elif rating >= 70:

            stars = "⭐⭐⭐"

            tag = "NORMAL"


        else:

            stars = "⭐⭐"

            tag = "LOW"



        analyzed_matches.append({

            "home": home_name,

            "away": away_name,

            "league": league,

            "home_corner": home_avg,

            "away_corner": away_avg,

            "expected_corner": expected_corner,

            "rating": rating,

            "stars": stars,

            "tag": tag

        })




    analyzed_matches.sort(
        key=lambda x: x["rating"],
        reverse=True
    )



    st.subheader(
        "🎯 Corner Under Predictions"
    )



    for match in analyzed_matches:


        with st.container():


            st.markdown(
                f"## ⚽ {match['home']} vs {match['away']}"
            )


            st.write(
                f"🏆 League: {match['league']}"
            )


            col1, col2, col3 = st.columns(3)


            with col1:

                st.metric(
                    "Home Avg Corner",
                    match["home_corner"]
                )


            with col2:

                st.metric(
                    "Away Avg Corner",
                    match["away_corner"]
                )


            with col3:

                st.metric(
                    "Expected Corner",
                    match["expected_corner"]
                )



            st.success(
                f"{match['stars']} "
                f"Under Rating: {match['rating']}% "
                f"- {match['tag']}"
            )


            st.divider()
