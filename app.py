import json
import os
import streamlit as st


# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Pre-Match Over/Under Intelligence Pro",
    page_icon="⚽",
    layout="wide",
)


# ============================================================
# 2. CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background-color: #0b0e14;
    color: #e6edf3;
}

.header-card {
    background: linear-gradient(
        135deg,
        #161b22 0%,
        #21262d 100%
    );
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
}

.badge-over {
    background-color: #00e676;
    color: #042410;
    padding: 7px 14px;
    border-radius: 6px;
    font-weight: 800;
    display: inline-block;
}

.badge-under {
    background-color: #ff1744;
    color: #ffffff;
    padding: 7px 14px;
    border-radius: 6px;
    font-weight: 800;
    display: inline-block;
}

.badge-neutral {
    background-color: #30363d;
    color: #8b949e;
    padding: 7px 14px;
    border-radius: 6px;
    font-weight: 800;
    display: inline-block;
}

.badge-unavailable {
    background-color: #5a2028;
    color: #ff7b72;
    padding: 7px 14px;
    border-radius: 6px;
    font-weight: 800;
    display: inline-block;
}

.stat-box {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    min-height: 82px;
}

.stat-box-warning {
    background-color: #161b22;
    border: 1px solid #5a2028;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    min-height: 82px;
}

.score-box {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 6px;
}

.small-note {
    color: #8b949e;
    font-size: 12px;
}

.data-warning {
    background-color: #2d1b1e;
    border: 1px solid #5a2028;
    color: #ff7b72;
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
}

.data-success {
    background-color: #12251a;
    border: 1px solid #238636;
    color: #56d364;
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
}

.info-box {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
}

.league-box {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
}

.filter-title {
    color: #58a6ff;
    font-weight: 700;
    font-size: 15px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 3. HEADER
# ============================================================

st.markdown(
    """
## ⚽ MATCHES FEED

<span style="
    color:#58a6ff;
    font-size:14px;
">
Pre-Match Intelligence Pro
</span>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 4. CHECK JSON FILE
# ============================================================

if not os.path.exists("matches_data.json"):

    st.error(
        "⚠️ `matches_data.json` ဖိုင် မတွေ့ရှိသေးပါ။ "
        "ကျေးဇူးပြု၍ GitHub Actions Workflow ကို "
        "အရင် Run ပေးပါ။"
    )

    st.stop()


# ============================================================
# 5. LOAD JSON
# ============================================================

try:

    with open(
        "matches_data.json",
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

except json.JSONDecodeError as exc:

    st.error(
        "❌ `matches_data.json` ကို JSON အဖြစ် "
        "ဖတ်မရပါ။"
    )

    st.code(str(exc))

    st.stop()

except Exception as exc:

    st.error(
        "❌ JSON ဖိုင်ဖတ်ရာတွင် Error ဖြစ်နေပါတယ်။"
    )

    st.code(str(exc))

    st.stop()


# ============================================================
# 6. VALIDATE DATA
# ============================================================

if not isinstance(data, dict):

    st.error(
        "❌ `matches_data.json` ရဲ့ root structure က "
        "JSON object မဟုတ်ပါ။"
    )

    st.stop()


# ============================================================
# 7. GET MATCH DATA
# ============================================================

matches = data.get(
    "matches",
    []
)

if not isinstance(matches, list):

    matches = []


updated_date = data.get(
    "updated_at",
    "N/A"
)

window_range = data.get(
    "window_range",
    "N/A"
)

mode = data.get(
    "mode",
    "N/A"
)

league_filter_data = data.get(
    "league_filter",
    "N/A"
)


# ============================================================
# 8. SAFE DISPLAY FUNCTIONS
# ============================================================

def safe_pct(value):

    if value is None:
        return "N/A"

    try:
        return f"{float(value):.0f}%"

    except (
        TypeError,
        ValueError
    ):
        return "N/A"


def safe_number(value):

    if value is None:
        return "N/A"

    try:
        return f"{float(value):.2f}"

    except (
        TypeError,
        ValueError
    ):
        return "N/A"


def safe_probability(value):

    if value is None:
        return "N/A"

    try:
        return f"{float(value):.1f}%"

    except (
        TypeError,
        ValueError
    ):
        return "N/A"


def safe_edge(value):

    if value is None:
        return "N/A"

    try:
        return f"{float(value):+.1f}%"

    except (
        TypeError,
        ValueError
    ):
        return "N/A"


def get_reason(stats):

    if not isinstance(stats, dict):
        return "UNKNOWN"

    return stats.get(
        "reason",
        stats.get(
            "status",
            "UNKNOWN"
        )
    )


def get_sample_size(stats):

    if not isinstance(stats, dict):
        return 0

    try:
        return int(
            stats.get(
                "sample_size",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):
        return 0


def is_available(stats):

    if not isinstance(stats, dict):
        return False

    # New format
    if "available" in stats:

        return bool(
            stats.get(
                "available",
                False
            )
        )

    # Existing model format
    status = stats.get(
        "status",
        ""
    )

    if status in [
        "PROXY_2024_25",
        "PARTIAL_PROXY_2024_25",
    ]:

        return True

    if get_sample_size(stats) >= 5:

        return True

    return False


# ============================================================
# 9. HEADER INFORMATION
# ============================================================

st.markdown(
    f"""
<div class="header-card">

    <div style="
        display:flex;
        justify-content:space-between;
        align-items:center;
        gap:20px;
        flex-wrap:wrap;
    ">

        <div>

            <span class="small-note">
                ACTIVE MATCHES DATE
            </span>

            <h4 style="
                margin:0;
                color:#00e676;
            ">
                📅 {updated_date}
            </h4>

        </div>

        <div>

            <span style="
                background-color:#21262d;
                color:#58a6ff;
                padding:7px 12px;
                border-radius:6px;
                font-weight:bold;
            ">
                Total Matches: {len(matches)}
            </span>

        </div>

    </div>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 10. WINDOW / MODE INFORMATION
# ============================================================

info_col1, info_col2 = st.columns(2)


with info_col1:

    st.markdown(
        f"""
        <div class="info-box">

        <span class="small-note">
        🕐 SEARCH WINDOW
        </span>

        <br>

        <b>
        {window_range}
        </b>

        </div>
        """,
        unsafe_allow_html=True,
    )


with info_col2:

    st.markdown(
        f"""
        <div class="info-box">

        <span class="small-note">
        ⚙️ MODE
        </span>

        <br>

        <b>
        {mode}
        </b>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 11. LEAGUE FILTER DISPLAY
#
# IMPORTANT:
# DO NOT use st.metric() with a list.
# league_filter can be a list/string.
# ============================================================

st.markdown(
    "### 🏆 League Filter"
)


if isinstance(
    league_filter_data,
    list
):

    # --------------------------------------------------------
    # LIST FORMAT
    # --------------------------------------------------------

    league_count = len(
        league_filter_data
    )

    st.markdown(
        f"""
        <div class="info-box">

        <span class="filter-title">
        📋 {league_count} League / Competition Groups
        </span>

        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(
        "📋 View League Filter",
        expanded=False
    ):

        for league in league_filter_data:

            st.markdown(
                f"""
                <div class="league-box">
                • {league}
                </div>
                """,
                unsafe_allow_html=True,
            )


elif isinstance(
    league_filter_data,
    str
):

    st.markdown(
        f"""
        <div class="info-box">

        <span class="filter-title">
        🏆 {league_filter_data}
        </span>

        </div>
        """,
        unsafe_allow_html=True,
    )


else:

    st.markdown(
        """
        <div class="info-box">

        <span class="small-note">
        League filter information is not available.
        </span>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 12. EMPTY MATCH CHECK
# ============================================================

if not matches:

    st.warning(
        "⚠️ လက်ရှိမှာ ပြသရန် match data မရှိသေးပါ။"
    )

    st.stop()


# ============================================================
# 13. MATCH FILTER
# ============================================================

available_leagues = []

for match in matches:

    if not isinstance(
        match,
        dict
    ):
        continue

    league_name = match.get(
        "league",
        "Unknown League"
    )

    if league_name not in available_leagues:

        available_leagues.append(
            league_name
        )


available_leagues.sort()


st.markdown(
    "### 🔎 Match Filter"
)


selected_leagues = st.multiselect(
    "League",
    options=available_leagues,
    default=available_leagues,
    key="league_selector",
)


filtered_matches = []


for match in matches:

    if not isinstance(
        match,
        dict
    ):
        continue

    league_name = match.get(
        "league",
        "Unknown League"
    )

    if league_name in selected_leagues:

        filtered_matches.append(
            match
        )


st.markdown(
    f"""
    <div class="info-box">

    <span class="small-note">
    MATCHES AFTER FILTER
    </span>

    <br>

    <b style="
        color:#58a6ff;
        font-size:18px;
    ">
    {len(filtered_matches)}
    </b>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 14. MATCH LOOP
# ============================================================

for m in filtered_matches:

    if not isinstance(
        m,
        dict
    ):
        continue


    # --------------------------------------------------------
    # BASIC MATCH DATA
    # --------------------------------------------------------

    h_name = m.get(
        "home",
        "Unknown Home"
    )

    a_name = m.get(
        "away",
        "Unknown Away"
    )

    l_name = m.get(
        "league",
        "Unknown League"
    )

    country = m.get(
        "country",
        ""
    )

    sig = m.get(
        "signal",
        "NEUTRAL"
    )

    prob = m.get(
        "prob",
        m.get(
            "probability",
            None
        )
    )

    edge = m.get(
        "edge",
        None
    )

    hs = m.get(
        "h_stats",
        {}
    )

    as_ = m.get(
        "a_stats",
        {}
    )


    if not isinstance(
        hs,
        dict
    ):

        hs = {}


    if not isinstance(
        as_,
        dict
    ):

        as_ = {}


    # --------------------------------------------------------
    # DATA AVAILABILITY
    # --------------------------------------------------------

    home_available = is_available(
        hs
    )

    away_available = is_available(
        as_
    )

    data_available = (
        home_available
        and away_available
    )


    # --------------------------------------------------------
    # EXPANDER TITLE
    # --------------------------------------------------------

    expander_title = (
        f"🏆 {l_name}"
        f"  |  ⏰ {m.get('time', 'N/A')} MMT"
        f"  |  ⚽ {h_name} vs {a_name}"
        f"  [{sig}]"
    )


    with st.expander(
        expander_title,
        expanded=(
            sig in [
                "OVER_2_5",
                "UNDER_2_5"
            ]
        )
    ):


        # ====================================================
        # MATCH HEADER
        # ====================================================

        c1, c2 = st.columns(
            [2, 1]
        )


        # ----------------------------------------------------
        # LEFT
        # ----------------------------------------------------

        with c1:

            st.markdown(
                f"### ⚽ {h_name} vs {a_name}"
            )

            country_text = ""

            if country:

                country_text = (
                    f" ({country})"
                )

            st.caption(
                f"🏆 {l_name}"
                f"{country_text}"
                f" | ⏰ {m.get('time', 'N/A')} MMT"
            )


        # ----------------------------------------------------
        # RIGHT
        # ----------------------------------------------------

        with c2:

            if sig == "OVER_2_5":

                st.markdown(
                    """
                    <div class="badge-over">
                    ⭐⭐⭐⭐⭐ OVER 2.5 TARGET
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            elif sig == "UNDER_2_5":

                st.markdown(
                    """
                    <div class="badge-under">
                    ⭐⭐⭐⭐⭐ UNDER 2.5 TARGET
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            elif sig == "DATA_UNAVAILABLE":

                st.markdown(
                    """
                    <div class="badge-unavailable">
                    ⚠️ DATA UNAVAILABLE
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    """
                    <div class="badge-neutral">
                    ⚪ NEUTRAL
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


            prob_display = safe_probability(
                prob
            )

            edge_display = safe_edge(
                edge
            )


            st.write(
                f"**Probability:** "
                f"{prob_display}"
                f" | "
                f"**Edge:** "
                f"{edge_display}"
            )


        # ====================================================
        # DATA STATUS
        # ====================================================

        st.divider()


        if not data_available:

            home_reason = get_reason(
                hs
            )

            away_reason = get_reason(
                as_
            )

            st.markdown(
                f"""
                <div class="data-warning">

                <b>
                ⚠️ MODEL DATA UNAVAILABLE
                </b>

                <br><br>

                🏠 Home Data:
                <b>{home_reason}</b>

                <br>

                ✈️ Away Data:
                <b>{away_reason}</b>

                <br><br>

                Model Probability နှင့် Edge ကို
                <b>မယုံကြည်ရသော data ဖြင့် မတွက်ပါ</b>။

                </div>
                """,
                unsafe_allow_html=True,
            )


        else:

            home_sample = get_sample_size(
                hs
            )

            away_sample = get_sample_size(
                as_
            )

            st.markdown(
                f"""
                <div class="data-success">

                ✅ Home data နှင့် Away data ရရှိပါသည်။

                <br>

                🏠 Home Sample:
                <b>{home_sample}</b>

                &nbsp;&nbsp;

                ✈️ Away Sample:
                <b>{away_sample}</b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        # ====================================================
        # STATS TITLE
        # ====================================================

        st.markdown(
            f"""
            #### 🏠 {h_name}
            (Home L5)
            vs
            ✈️ {a_name}
            (Away L5)
            """
        )


        # ====================================================
        # STAT VALUES
        # ====================================================

        home_over = safe_pct(
            hs.get(
                "over_pct"
            )
        )

        away_over = safe_pct(
            as_.get(
                "over_pct"
            )
        )

        home_under = safe_pct(
            hs.get(
                "under_pct"
            )
        )

        away_under = safe_pct(
            as_.get(
                "under_pct"
            )
        )

        home_btts = safe_pct(
            hs.get(
                "btts_pct"
            )
        )

        away_btts = safe_pct(
            as_.get(
                "btts_pct"
            )
        )


        # ====================================================
        # OVER / UNDER / BTTS
        # ====================================================

        b1, b2, b3, b4 = st.columns(
            4
        )


        # ----------------------------------------------------
        # HOME OVER
        # ----------------------------------------------------

        with b1:

            st.markdown(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                    HOME L5 OVER 2.5
                    </span>

                    <br>

                    <b style="
                        color:#58a6ff;
                        font-size:18px;
                    ">
                        {home_over}
                    </b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        # ----------------------------------------------------
        # AWAY OVER
        # ----------------------------------------------------

        with b2:

            st.markdown(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                    AWAY L5 OVER 2.5
                    </span>

                    <br>

                    <b style="
                        color:#58a6ff;
                        font-size:18px;
                    ">
                        {away_over}
                    </b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        # ----------------------------------------------------
        # HOME BTTS
        # ----------------------------------------------------

        with b3:

            st.markdown(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                    HOME L5 BTTS
                    </span>

                    <br>

                    <b style="
                        color:#00e676;
                        font-size:18px;
                    ">
                        {home_btts}
                    </b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        # ----------------------------------------------------
        # AWAY BTTS
        # ----------------------------------------------------

        with b4:

            st.markdown(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                    AWAY L5 BTTS
                    </span>

                    <br>

                    <b style="
                        color:#00e676;
                        font-size:18px;
                    ">
                        {away_btts}
                    </b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        # ====================================================
        # UNDER STATS
        # ====================================================

        st.write("")

        u1, u2 = st.columns(2)


        with u1:

            st.markdown(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                    HOME L5 UNDER 2.5
                    </span>

                    <br>

                    <b style="
                        color:#ff7b72;
                        font-size:18px;
                    ">
                        {home_under}
                    </b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        with u2:

            st.markdown(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                    AWAY L5 UNDER 2.5
                    </span>

                    <br>

                    <b style="
                        color:#ff7b72;
                        font-size:18px;
                    ">
                        {away_under}
                    </b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        # ====================================================
        # GOALS AVERAGES
        # ====================================================

        st.write("")

        st.markdown(
            "##### 📊 Goals Averages"
        )


        gf_home = safe_number(
            hs.get(
                "gf_avg"
            )
        )

        ga_home = safe_number(
            hs.get(
                "ga_avg"
            )
        )

        gf_away = safe_number(
            as_.get(
                "gf_avg"
            )
        )

        ga_away = safe_number(
            as_.get(
                "ga_avg"
            )
        )


        g1, g2, g3, g4 = st.columns(
            4
        )


        with g1:

            st.markdown(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                    HOME GF AVG
                    </span>

                    <br>

                    <b style="font-size:18px;">
                        {gf_home}
                    </b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        with g2:

            st.markdown(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                    HOME GA AVG
                    </span>

                    <br>

                    <b style="font-size:18px;">
                        {ga_home}
                    </b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        with g3:

            st.markdown(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                    AWAY GF AVG
                    </span>

                    <br>

                    <b style="font-size:18px;">
                        {gf_away}
                    </b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        with g4:

            st.markdown(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                    AWAY GA AVG
                    </span>

                    <br>

                    <b style="font-size:18px;">
                        {ga_away}
                    </b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        # ====================================================
        # RECENT MATCHES
        # ====================================================

        st.write("")

        st.markdown(
            "##### 📜 Recent Home / Away Matches"
        )


        sc1, sc2 = st.columns(
            2
        )


        # ====================================================
        # HOME RECENT MATCHES
        # ====================================================

        with sc1:

            st.caption(
                f"🏠 {h_name} — Last 5 Home Matches"
            )

            home_scores = hs.get(
                "scorelines",
                []
            )

            if (
                isinstance(
                    home_scores,
                    list
                )
                and home_scores
            ):

                for sc in home_scores:

                    if not isinstance(
                        sc,
                        dict
                    ):
                        continue

                    date = sc.get(
                        "date",
                        "N/A"
                    )

                    home_team = sc.get(
                        "home",
                        "N/A"
                    )

                    away_team = sc.get(
                        "away",
                        "N/A"
                    )

                    gh = sc.get(
                        "gh",
                        "?"
                    )

                    ga = sc.get(
                        "ga",
                        "?"
                    )

                    total = sc.get(
                        "total",
                        sc.get(
                            "tot",
                            "?"
                        )
                    )

                    st.markdown(
                        f"""
                        <div class="score-box">

                        {date}
                        •
                        <b>
                        {home_team}
                        {gh}
                        -
                        {ga}
                        {away_team}
                        </b>

                        (
                        {total}
                        G
                        )

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            else:

                st.markdown(
                    """
                    <div class="data-warning">

                    ⚠️ Home recent-match data
                    မရရှိသေးပါ။

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


        # ====================================================
        # AWAY RECENT MATCHES
        # ====================================================

        with sc2:

            st.caption(
                f"✈️ {a_name} — Last 5 Away Matches"
            )

            away_scores = as_.get(
                "scorelines",
                []
            )

            if (
                isinstance(
                    away_scores,
                    list
                )
                and away_scores
            ):

                for sc in away_scores:

                    if not isinstance(
                        sc,
                        dict
                    ):
                        continue

                    date = sc.get(
                        "date",
                        "N/A"
                    )

                    home_team = sc.get(
                        "home",
                        "N/A"
                    )

                    away_team = sc.get(
                        "away",
                        "N/A"
                    )

                    gh = sc.get(
                        "gh",
                        "?"
                    )

                    ga = sc.get(
                        "ga",
                        "?"
                    )

                    total = sc.get(
                        "total",
                        sc.get(
                            "tot",
                            "?"
                        )
                    )

                    st.markdown(
                        f"""
                        <div class="score-box">

                        {date}
                        •
                        <b>
                        {home_team}
                        {gh}
                        -
                        {ga}
                        {away_team}
                        </b>

                        (
                        {total}
                        G
                        )

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            else:

                st.markdown(
                    """
                    <div class="data-warning">

                    ⚠️ Away recent-match data
                    မရရှိသေးပါ။

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


        # ====================================================
        # MODEL DETAILS
        # ====================================================

        st.write("")

        with st.expander(
            "🔍 Model / Data Details",
            expanded=False
        ):

            model_status = m.get(
                "model_status",
                "N/A"
            )

            data_warning = m.get(
                "data_warning",
                ""
            )

            st.write(
                f"**Signal:** {sig}"
            )

            st.write(
                f"**Probability:** "
                f"{safe_probability(prob)}"
            )

            st.write(
                f"**Edge:** "
                f"{safe_edge(edge)}"
            )

            st.write(
                f"**Model Status:** "
                f"{model_status}"
            )

            if data_warning:

                st.warning(
                    data_warning
                )


# ============================================================
# 15. FOOTER
# ============================================================

st.divider()

st.caption(
    "⚽ Pre-Match Over/Under Intelligence Pro "
    "| API data availability is shown explicitly. "
    "| No fake 50% fallback values are used."
)
