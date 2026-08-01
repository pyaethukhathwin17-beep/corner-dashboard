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


headers = {
    "x-apisports-key": API_KEY
}



@st.cache_data(ttl=1800)
def get_today_fixtures(date_str):

    url = f"https://v3.football.api-sports.io/fixtures?date={date_str}"

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get("response", [])

    except Exception as e:

        st.error(f"Fixture Error: {e}")

    return []



@st.cache_data(ttl=1800)
def get_team_last_fixtures(team_id):

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures?team={team_id}&last=5"
    )

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get("response", [])

    except Exception as e:

        st.error(f"Team Fixture Error: {e}")

    return []



@st.cache_data(ttl=1800)
def get_fixture_statistics(fixture_id):

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures/statistics?fixture={fixture_id}"
    )

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get("response", [])

    except Exception as e:

        st.error(f"Statistics Error: {e}")

    return []




fixtures = get_today_fixtures(today_date)



if not fixtures:

    st.info(
        "ဒီနေ့အတွက် ပွဲစဉ်များ မရှိသေးပါ "
        "သို့မဟုတ် API Data မရရှိပါ။"
    )


else:


    analyzed_matches = []


    for fix in fixtures:


        fixture_id = fix["fixture"]["id"]


        home_team = fix["teams"]["home"]["name"]

        away_team = fix["teams"]["away"]["name"]


        home_id = fix["teams"]["home"]["id"]

        away_id = fix["teams"]["away"]["id"]


        league_name = fix["league"]["name"]

        status = fix["fixture"]["status"]["short"]

        match_time = fix["fixture"]["date"][11:16]



        # Team data test
        home_last_matches = get_team_last_fixtures(home_id)

        away_last_matches = get_team_last_fixtures(away_id)



        # Fixture statistics test
        statistics = get_fixture_statistics(fixture_id)



        # Base Rating
        rating = 50



        if len(home_last_matches) > 0 and len(away_last_matches) > 0:

            rating = 55



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

            "home_id": home_id,

            "away_id": away_id,

            "fixture_id": fixture_id,

            "league": league_name,

            "status": status,

            "time": match_time,

            "rating": rating,

            "stars": stars,

            "tag": tag

        })




    analyzed_matches.sort(
        key=lambda x: x["rating"],
        reverse=True
    )



    st.subheader("🎯 Filter Matches by Rating")



    filter_option = st.selectbox(

        "ရွေးချယ်လိုသော Star Rating စစ်ထုတ်ပါ -",

        [

            "🔥 All Recommended Matches",

            "⭐️⭐️⭐️⭐️⭐️ 5 Star Target Only (90%+ Rating)",

            "⭐️⭐️⭐️⭐️ 4 Star Target Only (80%+ Rating)"

        ]

    )



    filtered_list = analyzed_matches



    if "5 Star Target Only" in filter_option:

        filtered_list = [
            m for m in analyzed_matches
            if m["rating"] >= 90
        ]


    elif "4 Star Target Only" in filter_option:

        filtered_list = [
            m for m in analyzed_matches
            if m["rating"] >= 80
        ]



    st.write(
        f"📊 ရှာတွေ့သော ပွဲစဉ်ပေါင်း: **{len(filtered_list)}** ပွဲ"
    )


    st.divider()



    for m in filtered_list:


        with st.container():


            col1, col2 = st.columns([2,1])


            with col1:

                st.markdown(
                    f"### ⚽ {m['home']} vs {m['away']}"
                )


                st.write(

                    f"🏆 **League:** {m['league']} | "
                    f"⏰ **Time:** {m['time']} UTC "
                    f"[{m['status']}]"

                )


                st.caption(
                    f"Fixture ID: {m['fixture_id']}"
                )


            with col2:


                st.metric(

                    label=f"Under Rating: {m['rating']}%",

                    value=m["stars"],

                    delta=m["tag"]

                )


            if m["rating"] >= 90:

                st.success(
                    "✅ Recommendation: Prematch / Live Corner Under"
                )

            else:

                st.info(
                    "⚠️ Recommendation: Watch Live Odds for Corner Under"
                )


            st.divider()
