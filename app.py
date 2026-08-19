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
    padding: 6px 14px;
    border-radius: 6px;
    font-weight: 800;
}

.badge-under {
    background-color: #ff1744;
    color: #ffffff;
    padding: 6px 14px;
    border-radius: 6px;
    font-weight: 800;
}

.badge-neutral {
    background-color: #30363d;
    color: #8b949e;
    padding: 6px 14px;
    border-radius: 6px;
    font-weight: 800;
}

.badge-unavailable {
    background-color: #5a2028;
    color: #ff7b72;
    padding: 6px 14px;
    border-radius: 6px;
    font-weight: 800;
}

.stat-box {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px;
    text-align: center;
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

.model-box {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px;
    margin-top: 8px;
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
<span style='color:#58a6ff; font-size:14px;'>
Pre-Match Intelligence Pro
</span>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 4. CHECK JSON
# ============================================================

if not os.path.exists("matches_data.json"):

    st.error(
        "⚠️ `matches_data.json` ဖိုင် မတွေ့ရှိသေးပါ။ "
        "GitHub Actions မှ Fetch Workflow ကို run ပေးပါ။"
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
    ) as f:

        data = json.load(f)

except json.JSONDecodeError as e:

    st.error(
        f"❌ `matches_data.json` JSON format မှားနေပါတယ်။\n\n{e}"
    )

    st.stop()

except Exception as e:

    st.error(
        f"❌ JSON ဖိုင်ဖတ်ရာတွင် Error ဖြစ်နေပါတယ်:\n\n{e}"
    )

    st.stop()


# ============================================================
# 6. GET MATCH DATA
# ============================================================

matches = data.get(
    "matches",
    []
)

updated_date = data.get(
    "updated_at",
    data.get(
        "window_range",
        "N/A"
    )
)


# ============================================================
# 7. HEADER CARD
# ============================================================

st.markdown(
    f"""
<div class="header-card"
     style="
        display:flex;
        justify-content:space-between;
        align-items:center;
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

    <span style="
        background-color:#21262d;
        color:#58a6ff;
        padding:6px 12px;
        border-radius:6px;
        font-weight:bold;
    ">
        Total Matches: {len(matches)}
    </span>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 8. EMPTY DATA
# ============================================================

if not matches:

    st.warning(
        "⚠️ လက်ရှိမှာ ပြသရန် match data မရှိသေးပါ။"
    )

    st.stop()


# ============================================================
# 9. HELPER FUNCTIONS
# ============================================================

def safe_pct(value):

    if value is None:
        return "N/A"

    try:
        return f"{float(value):.0f}%"

    except (TypeError, ValueError):

        return "N/A"


def safe_number(value):

    if value is None:
        return "N/A"

    try:
        return f"{float(value):.2f}"

    except (TypeError, ValueError):

        return "N/A"


def safe_probability(value):

    if value is None:
        return "N/A"

    try:
        return f"{float(value):.1f}%"

    except (TypeError, ValueError):

        return "N/A"


def safe_edge(value):

    if value is None:
        return "N/A"

    try:
        return f"{float(value):+.1f}%"

    except (TypeError, ValueError):

        return "N/A"


# ============================================================
# 10. IMPORTANT DATA AVAILABILITY CHECK
# ============================================================

def stats_available(stats):

    """
    IMPORTANT:

    Fetcher version တချို့မှာ `available` field မပါနိုင်ပါတယ်။

    ဒါကြောင့် available=True ဖြစ်မှ data ရှိတယ်လို့
    မသတ်မှတ်တော့ပါဘူး။

    Actual statistical fields ရှိမရှိကို စစ်ပါမယ်။
    """

    if not isinstance(stats, dict):
        return False

    # Explicit unavailable states
    reason = str(
        stats.get(
            "reason",
            ""
        )
    ).upper()

    status = str(
        stats.get(
            "status",
            ""
        )
    ).upper()

    if reason in [
        "API_ERROR",
        "API_DATA_UNAVAILABLE",
        "INSUFFICIENT_L5_DATA",
        "DATA_UNAVAILABLE",
        "UNKNOWN",
    ]:
        return False

    if status in [
        "API_ERROR",
        "API_DATA_UNAVAILABLE",
        "INSUFFICIENT_L5_DATA",
        "DATA_UNAVAILABLE",
    ]:
        return False

    # New fetcher may provide explicit available=True
    if stats.get("available") is True:
        return True

    # Actual L5 statistics are enough
    required_fields = [
        "over_pct",
        "btts_pct",
        "gf_avg",
        "ga_avg",
    ]

    found = 0

    for field in required_fields:

        if stats.get(field) is not None:
            found += 1

    return found >= 3


# ============================================================
# 11. MATCH LOOP
# ============================================================

for m in matches:

    # --------------------------------------------------------
    # BASIC DATA
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
        None
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


    # --------------------------------------------------------
    # DATA AVAILABILITY
    # --------------------------------------------------------

    home_available = stats_available(
        hs
    )

    away_available = stats_available(
        as_
    )

    data_available = (
        home_available
        and away_available
    )


    # ========================================================
    # EXPANDER TITLE
    # ========================================================

    expander_title = (
        f"🏆 {l_name}"
        f" | ⏰ {m.get('time', 'N/A')} MMT"
        f" | ⚽ {h_name} vs {a_name}"
        f" [{sig}]"
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
        # MATCH NAME
        # ----------------------------------------------------

        with c1:

            st.markdown(
                f"### ⚽ {h_name} vs {a_name}"
            )

            st.caption(
                f"🏆 {l_name}"
                f" ({country})"
                f" | ⏰ {m.get('time', 'N/A')} MMT"
            )


        # ----------------------------------------------------
        # SIGNAL
        # ----------------------------------------------------

        with c2:

            if sig == "OVER_2_5":

                st.markdown(
                    """
                    <div class='badge-over'>
                    ⭐⭐⭐⭐⭐ OVER 2.5 TARGET
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            elif sig == "UNDER_2_5":

                st.markdown(
                    """
                    <div class='badge-under'>
                    ⭐⭐⭐⭐⭐ UNDER 2.5 TARGET
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            elif sig == "DATA_UNAVAILABLE":

                st.markdown(
                    """
                    <div class='badge-unavailable'>
                    ⚠️ DATA UNAVAILABLE
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    """
                    <div class='badge-neutral'>
                    ⚪ NEUTRAL
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


            # =================================================
            # PROBABILITY / EDGE
            # =================================================

            st.write(
                f"**Probability:** "
                f"{safe_probability(prob)}"
                f" | "
                f"**Edge:** "
                f"{safe_edge(edge)}"
                f" vs 60% threshold"
            )


        # ====================================================
        # MODEL STATUS
        # ====================================================

        st.divider()


        if data_available:

            st.markdown(
                """
                <div class="data-success">

                ✅ <b>MODEL DATA AVAILABLE</b>

                <br><br>

                🏠 Home L5:
                <b>AVAILABLE</b>

                <br>

                ✈️ Away L5:
                <b>AVAILABLE</b>

                <br><br>

                Model Probability နှင့် Edge
                ကို API မှရရှိသော L5 data
                အပေါ်အခြေခံ၍ တွက်ချက်ထားပါသည်။

                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            # Only show unavailable when actual stats are missing
            home_reason = hs.get(
                "reason",
                hs.get(
                    "status",
                    "DATA_UNAVAILABLE"
                )
            )

            away_reason = as_.get(
                "reason",
                as_.get(
                    "status",
                    "DATA_UNAVAILABLE"
                )
            )

            st.markdown(
                f"""
                <div class="data-warning">

                ⚠️ <b>MODEL DATA UNAVAILABLE</b>

                <br><br>

                🏠 Home Data:
                <b>{home_reason}</b>

                <br>

                ✈️ Away Data:
                <b>{away_reason}</b>

                </div>
                """,
                unsafe_allow_html=True,
            )


        # ====================================================
        # L5 TITLE
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
        # OVER / BTTS
        # ====================================================

        home_over = safe_pct(
            hs.get("over_pct")
        )

        away_over = safe_pct(
            as_.get("over_pct")
        )

        home_btts = safe_pct(
            hs.get("btts_pct")
        )

        away_btts = safe_pct(
            as_.get("btts_pct")
        )


        b1, b2, b3, b4 = st.columns(
            4
        )


        with b1:

            st.markdown(
                f"""
                <div class='stat-box'>

                <span class='small-note'>
                HOME L5 OVER
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


        with b2:

            st.markdown(
                f"""
                <div class='stat-box'>

                <span class='small-note'>
                AWAY L5 OVER
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


        with b3:

            st.markdown(
                f"""
                <div class='stat-box'>

                <span class='small-note'>
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


        with b4:

            st.markdown(
                f"""
                <div class='stat-box'>

                <span class='small-note'>
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
        # GOALS AVERAGES
        # ====================================================

        st.write("")

        st.markdown(
            "##### 📊 Goals Averages"
        )


        gf_home = safe_number(
            hs.get("gf_avg")
        )

        ga_home = safe_number(
            hs.get("ga_avg")
        )

        gf_away = safe_number(
            as_.get("gf_avg")
        )

        ga_away = safe_number(
            as_.get("ga_avg")
        )


        g1, g2, g3, g4 = st.columns(
            4
        )


        with g1:

            st.markdown(
                f"""
                <div class='stat-box'>

                <span class='small-note'>
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
                <div class='stat-box'>

                <span class='small-note'>
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
                <div class='stat-box'>

                <span class='small-note'>
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
                <div class='stat-box'>

                <span class='small-note'>
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
            "##### 📜 Recent Home/Away Matches:"
        )


        sc1, sc2 = st.columns(
            2
        )


        # ====================================================
        # HOME MATCHES
        # ====================================================

        with sc1:

            st.caption(
                f"🏠 {h_name} Last 5 Home Matches"
            )

            home_scores = hs.get(
                "scorelines",
                []
            )


            if home_scores:

                for sc in home_scores:

                    total_goals = sc.get(
                        "total",
                        sc.get(
                            "tot",
                            "?"
                        )
                    )

                    st.markdown(
                        f"""
                        <div class='score-box'>

                        {sc.get('date', 'N/A')}
                        •
                        <b>
                        {sc.get('home', 'N/A')}
                        {sc.get('gh', '?')}
                        -
                        {sc.get('ga', '?')}
                        {sc.get('away', 'N/A')}
                        </b>

                        (
                        {total_goals}
                        G
                        )

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            else:

                st.markdown(
                    """
                    <div class='data-warning'>
                    ⚠️ Home recent-match data
                    မရရှိသေးပါ။
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


        # ====================================================
        # AWAY MATCHES
        # ====================================================

        with sc2:

            st.caption(
                f"✈️ {a_name} Last 5 Away Matches"
            )

            away_scores = as_.get(
                "scorelines",
                []
            )


            if away_scores:

                for sc in away_scores:

                    total_goals = sc.get(
                        "total",
                        sc.get(
                            "tot",
                            "?"
                        )
                    )

                    st.markdown(
                        f"""
                        <div class='score-box'>

                        {sc.get('date', 'N/A')}
                        •
                        <b>
                        {sc.get('home', 'N/A')}
                        {sc.get('gh', '?')}
                        -
                        {sc.get('ga', '?')}
                        {sc.get('away', 'N/A')}
                        </b>

                        (
                        {total_goals}
                        G
                        )

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            else:

                st.markdown(
                    """
                    <div class='data-warning'>
                    ⚠️ Away recent-match data
                    မရရှိသေးပါ။
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ============================================================
# 12. FOOTER
# ============================================================

st.divider()

st.caption(
    "⚽ Pre-Match Over/Under Intelligence Pro "
    "| Real API L5 data is displayed explicitly. "
    "| No fake 50% fallback values are used."
)
