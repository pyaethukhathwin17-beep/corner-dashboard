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

    .stat-box-unavailable {
        background-color: #161b22;
        border: 1px solid #5a2028;
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
# 4. CHECK JSON FILE
# ============================================================

if not os.path.exists("matches_data.json"):

    st.error(
        "⚠️ `matches_data.json` ဖိုင် မတွေ့ရှိသေးပါ။ "
        "ကျေးဇူးပြု၍ GitHub Actions မှ Workflow ကို "
        "စတင် run ပေးပါခင်ဗျာ။"
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
        f"❌ `matches_data.json` ဖိုင်ကို ဖတ်မရပါ။\n\n{e}"
    )

    st.stop()

except Exception as e:

    st.error(
        f"❌ JSON ဖိုင်ဖတ်ရာတွင် Error ဖြစ်နေပါတယ်:\n\n{e}"
    )

    st.stop()


# ============================================================
# 6. GET DATA
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
# 8. EMPTY MATCH CHECK
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
    """
    Percentage value ကို UI မှာ လုံခြုံစွာပြရန်။
    None ဖြစ်ရင် N/A ပြမယ်။
    """

    if value is None:
        return "N/A"

    try:
        return f"{float(value):.0f}%"
    except (TypeError, ValueError):
        return "N/A"


def safe_number(value):
    """
    Normal number display.
    None ဖြစ်ရင် N/A.
    """

    if value is None:
        return "N/A"

    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "N/A"


def safe_probability(value):
    """
    Probability display.
    """

    if value is None:
        return "N/A"

    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def safe_edge(value):
    """
    Model edge display.
    None ဖြစ်ရင် N/A.
    """

    if value is None:
        return "N/A"

    try:
        return f"{float(value):+.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def get_reason(stats):
    """
    API data unavailable ဖြစ်ရင် reason ထုတ်ပြရန်။
    """

    if not isinstance(stats, dict):
        return "UNKNOWN"

    return stats.get(
        "reason",
        "UNKNOWN"
    )


# ============================================================
# 10. MATCH LOOP
# ============================================================

for m in matches:

    # --------------------------------------------------------
    # Basic match data
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
    # Data availability
    # --------------------------------------------------------

    home_available = (
        isinstance(hs, dict)
        and hs.get(
            "available",
            False
        )
    )

    away_available = (
        isinstance(as_, dict)
        and as_.get(
            "available",
            False
        )
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
        # LEFT SIDE
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
        # RIGHT SIDE
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
                f" vs 60% threshold"
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

                <b>⚠️ MODEL DATA UNAVAILABLE</b>
                <br><br>

                🏠 Home Data:
                <b>{home_reason}</b>

                <br>

                ✈️ Away Data:
                <b>{away_reason}</b>

                <br><br>

                Model Probability နှင့် Edge ကို
                <b>မတွက်ထားပါ</b>။

                </div>
                """,
                unsafe_allow_html=True,
            )


        else:

            st.markdown(
                """
                <div class="data-success">

                ✅ Home L5 နှင့် Away L5 data
                နှစ်ဖက်စလုံး ရရှိပြီး
                Model တွက်ချက်ထားပါသည်။

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
        # STATS COLUMNS
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


        # ----------------------------------------------------
        # AWAY OVER
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # HOME BTTS
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # AWAY BTTS
        # ----------------------------------------------------

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
        # GF / GA AVERAGES
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
        # HOME RECENT MATCHES
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
                        {sc.get('total', sc.get('tot', '?'))}
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
        # AWAY RECENT MATCHES
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
                        {sc.get('total', sc.get('tot', '?'))}
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
# 11. FOOTER
# ============================================================

st.divider()

st.caption(
    "⚽ Pre-Match Over/Under Intelligence Pro "
    "| API data availability is shown explicitly. "
    "No fake 50% fallback values are used."
)
