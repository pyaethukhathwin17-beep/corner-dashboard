import json
import os
import textwrap
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

/* ============================================================
   HEADER
   ============================================================ */

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


/* ============================================================
   BADGES
   ============================================================ */

.badge-over {
    background-color: #00e676;
    color: #042410;

    padding: 6px 14px;
    border-radius: 6px;

    font-weight: 800;
    display: inline-block;
}

.badge-under {
    background-color: #ff1744;
    color: #ffffff;

    padding: 6px 14px;
    border-radius: 6px;

    font-weight: 800;
    display: inline-block;
}

.badge-neutral {
    background-color: #30363d;
    color: #8b949e;

    padding: 6px 14px;
    border-radius: 6px;

    font-weight: 800;
    display: inline-block;
}

.badge-unavailable {
    background-color: #5a2028;
    color: #ff7b72;

    padding: 6px 14px;
    border-radius: 6px;

    font-weight: 800;
    display: inline-block;
}


/* ============================================================
   STAT BOX
   ============================================================ */

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


/* ============================================================
   SCORE BOX
   ============================================================ */

.score-box {
    background-color: #0d1117;

    border: 1px solid #30363d;
    border-radius: 8px;

    padding: 8px 12px;
    margin-bottom: 6px;
}


/* ============================================================
   TEXT
   ============================================================ */

.small-note {
    color: #8b949e;
    font-size: 12px;
}


/* ============================================================
   WARNING
   ============================================================ */

.data-warning {
    background-color: #2d1b1e;

    border: 1px solid #5a2028;

    color: #ff7b72;

    border-radius: 8px;

    padding: 12px;

    margin: 8px 0;
}


/* ============================================================
   SUCCESS
   ============================================================ */

.data-success {
    background-color: #12251a;

    border: 1px solid #238636;

    color: #56d364;

    border-radius: 8px;

    padding: 12px;

    margin: 8px 0;
}


/* ============================================================
   MODEL CARD
   ============================================================ */

.model-card {
    background-color: #161b22;

    border: 1px solid #30363d;

    border-radius: 10px;

    padding: 14px;

    margin-top: 8px;
}


/* ============================================================
   DATA SOURCE NOTE
   ============================================================ */

.proxy-note {
    background-color: #211f12;

    border: 1px solid #6e5c20;

    color: #d8c56a;

    border-radius: 8px;

    padding: 10px;

    margin-top: 8px;

    font-size: 13px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 3. HTML HELPER
# ============================================================

def render_html(html):
    """
    HTML indentation ကို ဖြုတ်ပြီး Streamlit မှာ
    raw HTML code မပြဘဲ HTML အဖြစ် render လုပ်ရန်။
    """

    st.markdown(
        textwrap.dedent(html).strip(),
        unsafe_allow_html=True,
    )


# ============================================================
# 4. HEADER
# ============================================================

st.markdown(
    """
## ⚽ MATCHES FEED
<span style="color:#58a6ff; font-size:14px;">
Pre-Match Intelligence Pro
</span>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 5. CHECK JSON FILE
# ============================================================

if not os.path.exists("matches_data.json"):

    st.error(
        "⚠️ `matches_data.json` ဖိုင် မတွေ့ရှိသေးပါ။\n\n"
        "ကျေးဇူးပြု၍ GitHub Actions Workflow ကို "
        "အရင် run ပေးပါ။"
    )

    st.stop()


# ============================================================
# 6. LOAD JSON
# ============================================================

try:

    with open(
        "matches_data.json",
        "r",
        encoding="utf-8",
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
# 7. GET DATA
# ============================================================

matches = data.get(
    "matches",
    [],
)

updated_date = data.get(
    "updated_at",
    data.get(
        "window_range",
        "N/A",
    ),
)

total_matches = len(matches)

mode = data.get(
    "mode",
    "UNKNOWN",
)

league_filter = data.get(
    "league_filter",
    "N/A",
)

history_season = data.get(
    "history_season",
    "N/A",
)

api_calls = data.get(
    "api_calls_this_run",
    "N/A",
)

remaining_quota = data.get(
    "remaining_quota",
    "N/A",
)


# ============================================================
# 8. HEADER CARD
# ============================================================

render_html(
    f"""
    <div class="header-card">

        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:15px;
            flex-wrap:wrap;
        ">

            <div>

                <span class="small-note">
                    ACTIVE MATCHES WINDOW
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
                Total Matches: {total_matches}
            </span>

        </div>

    </div>
    """
)


# ============================================================
# 9. SYSTEM INFORMATION
# ============================================================

with st.expander(
    "⚙️ System Information",
    expanded=False,
):

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Mode",
            mode,
        )

    with c2:

        st.metric(
            "League Filter",
            league_filter,
        )

    with c3:

        st.metric(
            "API Calls",
            api_calls,
        )

    with c4:

        st.metric(
            "Remaining Quota",
            remaining_quota,
        )

    st.caption(
        f"History Season: {history_season}"
    )


# ============================================================
# 10. EMPTY MATCH CHECK
# ============================================================

if not matches:

    st.warning(
        "⚠️ လက်ရှိမှာ ပြသရန် match data မရှိသေးပါ။"
    )

    st.info(
        "GitHub Actions က `matches_data.json` ထဲမှာ "
        "match မထည့်ပေးထားတာဖြစ်နိုင်ပါတယ်။"
    )

    st.stop()


# ============================================================
# 11. HELPER FUNCTIONS
# ============================================================

def safe_pct(value):

    if value is None:
        return "N/A"

    try:

        return f"{float(value):.0f}%"

    except (
        TypeError,
        ValueError,
    ):

        return "N/A"


def safe_number(value):

    if value is None:
        return "N/A"

    try:

        return f"{float(value):.2f}"

    except (
        TypeError,
        ValueError,
    ):

        return "N/A"


def safe_probability(value):

    if value is None:
        return "N/A"

    try:

        return f"{float(value):.1f}%"

    except (
        TypeError,
        ValueError,
    ):

        return "N/A"


def safe_edge(value):

    if value is None:
        return "N/A"

    try:

        return f"{float(value):+.1f}%"

    except (
        TypeError,
        ValueError,
    ):

        return "N/A"


def get_reason(stats):

    if not isinstance(
        stats,
        dict,
    ):

        return "UNKNOWN"

    status = stats.get(
        "status"
    )

    if status:
        return str(status)

    reason = stats.get(
        "reason"
    )

    if reason:
        return str(reason)

    return "UNKNOWN"


def get_model_status(match):

    status = match.get(
        "model_status"
    )

    if status:
        return status

    return "UNKNOWN"


# ============================================================
# 12. MATCH LOOP
# ============================================================

for m in matches:

    # --------------------------------------------------------
    # BASIC DATA
    # --------------------------------------------------------

    h_name = m.get(
        "home",
        "Unknown Home",
    )

    a_name = m.get(
        "away",
        "Unknown Away",
    )

    l_name = m.get(
        "league",
        "Unknown League",
    )

    country = m.get(
        "country",
        "",
    )

    sig = m.get(
        "signal",
        "NEUTRAL",
    )

    prob = m.get(
        "prob",
        None,
    )

    edge = m.get(
        "edge",
        None,
    )

    hs = m.get(
        "h_stats",
        {},
    )

    as_ = m.get(
        "a_stats",
        {},
    )

    model_status = get_model_status(
        m
    )


    # --------------------------------------------------------
    # DATA AVAILABILITY
    # --------------------------------------------------------

    home_available = (
        isinstance(hs, dict)
        and hs.get(
            "sample_size",
            0,
        ) >= 5
    )

    away_available = (
        isinstance(as_, dict)
        and as_.get(
            "sample_size",
            0,
        ) >= 5
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
                "UNDER_2_5",
            ]
        ),
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

            st.caption(
                f"🏆 {l_name}"
                f" ({country})"
                f" | ⏰ {m.get('time', 'N/A')} MMT"
            )


        # ----------------------------------------------------
        # RIGHT
        # ----------------------------------------------------

        with c2:

            if sig == "OVER_2_5":

                render_html(
                    """
                    <div class="badge-over">
                        ⭐⭐⭐⭐⭐ OVER 2.5 TARGET
                    </div>
                    """
                )

            elif sig == "UNDER_2_5":

                render_html(
                    """
                    <div class="badge-under">
                        ⭐⭐⭐⭐⭐ UNDER 2.5 TARGET
                    </div>
                    """
                )

            elif sig == "DATA_UNAVAILABLE":

                render_html(
                    """
                    <div class="badge-unavailable">
                        ⚠️ DATA UNAVAILABLE
                    </div>
                    """
                )

            else:

                render_html(
                    """
                    <div class="badge-neutral">
                        ⚪ NEUTRAL
                    </div>
                    """
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

            render_html(
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
                    <b>မတွက်ထားပါ</b>။

                </div>
                """
            )

        else:

            render_html(
                f"""
                <div class="data-success">

                    ✅ Home L5 နှင့် Away L5 data
                    နှစ်ဖက်စလုံး ရရှိပြီး
                    Model တွက်ချက်ထားပါသည်။

                    <br><br>

                    <span style="font-size:12px;">
                        Model Status:
                        {model_status}
                    </span>

                </div>
                """
            )


        # ====================================================
        # PROXY WARNING
        # ====================================================

        warning = m.get(
            "data_warning",
            "",
        )

        if warning:

            render_html(
                f"""
                <div class="proxy-note">
                    ⚠️ {warning}
                </div>
                """
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
        # OVER / BTTS STAT COLUMNS
        # ====================================================

        b1, b2, b3, b4 = st.columns(
            4
        )


        # ----------------------------------------------------
        # HOME OVER
        # ----------------------------------------------------

        with b1:

            render_html(
                f"""
                <div class="stat-box">

                    <span class="small-note">
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
                """
            )


        # ----------------------------------------------------
        # AWAY OVER
        # ----------------------------------------------------

        with b2:

            render_html(
                f"""
                <div class="stat-box">

                    <span class="small-note">
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
                """
            )


        # ----------------------------------------------------
        # HOME BTTS
        # ----------------------------------------------------

        with b3:

            render_html(
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
                """
            )


        # ----------------------------------------------------
        # AWAY BTTS
        # ----------------------------------------------------

        with b4:

            render_html(
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
                """
            )


        # ====================================================
        # UNDER STATISTICS
        # ====================================================

        st.write("")

        st.markdown(
            "##### 📉 Under 2.5 Statistics"
        )

        u1, u2 = st.columns(2)


        with u1:

            render_html(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                        HOME L5 UNDER
                    </span>

                    <br>

                    <b style="
                        color:#ff7b72;
                        font-size:18px;
                    ">
                        {home_under}
                    </b>

                </div>
                """
            )


        with u2:

            render_html(
                f"""
                <div class="stat-box">

                    <span class="small-note">
                        AWAY L5 UNDER
                    </span>

                    <br>

                    <b style="
                        color:#ff7b72;
                        font-size:18px;
                    ">
                        {away_under}
                    </b>

                </div>
                """
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


        # ----------------------------------------------------
        # HOME GF
        # ----------------------------------------------------

        with g1:

            render_html(
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
                """
            )


        # ----------------------------------------------------
        # HOME GA
        # ----------------------------------------------------

        with g2:

            render_html(
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
                """
            )


        # ----------------------------------------------------
        # AWAY GF
        # ----------------------------------------------------

        with g3:

            render_html(
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
                """
            )


        # ----------------------------------------------------
        # AWAY GA
        # ----------------------------------------------------

        with g4:

            render_html(
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
                """
            )


        # ====================================================
        # MODEL DETAILS
        # ====================================================

        st.write("")

        with st.expander(
            "🎯 Model Details",
            expanded=False,
        ):

            mc1, mc2, mc3 = st.columns(3)

            with mc1:

                st.metric(
                    "Probability",
                    prob_display,
                )

            with mc2:

                st.metric(
                    "Edge",
                    edge_display,
                )

            with mc3:

                st.metric(
                    "Model Status",
                    model_status,
                )

            if sig == "OVER_2_5":

                st.success(
                    "✅ OVER 2.5 signal generated."
                )

            elif sig == "UNDER_2_5":

                st.error(
                    "🔻 UNDER 2.5 signal generated."
                )

            elif sig == "NEUTRAL":

                st.info(
                    "⚪ No qualifying Over/Under signal."
                )

            else:

                st.warning(
                    "⚠️ Model signal unavailable."
                )


        # ====================================================
        # RECENT MATCHES
        # ====================================================

        st.write("")

        st.markdown(
            "##### 📜 Recent Home/Away Matches:"
        )


        sc1, sc2 = st.columns(2)


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

                    date = sc.get(
                        "date",
                        "N/A",
                    )

                    home_team = sc.get(
                        "home",
                        "N/A",
                    )

                    away_team = sc.get(
                        "away",
                        "N/A",
                    )

                    gh = sc.get(
                        "gh",
                        "?",
                    )

                    ga = sc.get(
                        "ga",
                        "?",
                    )

                    total = sc.get(
                        "total",
                        sc.get(
                            "tot",
                            "?",
                        ),
                    )

                    render_html(
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
                            {total} G
                            )

                        </div>
                        """
                    )

            else:

                render_html(
                    """
                    <div class="data-warning">

                        ⚠️ Home recent-match data
                        မရရှိသေးပါ။

                    </div>
                    """
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

                    date = sc.get(
                        "date",
                        "N/A",
                    )

                    home_team = sc.get(
                        "home",
                        "N/A",
                    )

                    away_team = sc.get(
                        "away",
                        "N/A",
                    )

                    gh = sc.get(
                        "gh",
                        "?",
                    )

                    ga = sc.get(
                        "ga",
                        "?",
                    )

                    total = sc.get(
                        "total",
                        sc.get(
                            "tot",
                            "?",
                        ),
                    )

                    render_html(
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
                            {total} G
                            )

                        </div>
                        """
                    )

            else:

                render_html(
                    """
                    <div class="data-warning">

                        ⚠️ Away recent-match data
                        မရရှိသေးပါ။

                    </div>
                    """
                )


# ============================================================
# 13. FOOTER
# ============================================================

st.divider()

st.caption(
    "⚽ Pre-Match Over/Under Intelligence Pro "
    "| API data availability is shown explicitly. "
    "| No fake 50% fallback values are used."
)
