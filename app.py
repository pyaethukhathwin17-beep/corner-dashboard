import json
import os
import streamlit as st

st.set_page_config(
    page_title="Pre-Match Over/Under Intelligence Pro",
    page_icon="⚽",
    layout="wide",
)

st.markdown(
    """
<style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    .header-card {
        background: linear-gradient(135deg, #161b22 0%, #21262d 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .badge-over { background-color: #00e676; color: #042410; padding: 6px 14px; border-radius: 6px; font-weight: 800; }
    .badge-under { background-color: #ff1744; color: #ffffff; padding: 6px 14px; border-radius: 6px; font-weight: 800; }
    .badge-neutral { background-color: #30363d; color: #8b949e; padding: 6px 14px; border-radius: 6px; font-weight: 800; }
    .stat-box { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 10px; text-align: center; }
    .score-box { background-color: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; margin-bottom: 6px; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    "## ⚽ MATCHES FEED <span style='color:#58a6ff; font-size:14px;'>Pre-Match Pro</span>",
    unsafe_allow_html=True,
)

if not os.path.exists("matches_data.json"):
    st.error(
        "⚠️ `matches_data.json` ဖိုင် မတွေ့ရှိသေးပါ။ ကျေးဇူးပြု၍ `fetch_data.py` ကို run ပေးပါ။"
    )
    st.stop()

with open("matches_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

matches = data.get("matches", [])
updated_date = data.get("updated_at", "N/A")

st.markdown(
    f"""
<div class="header-card" style="display:flex; justify-content:space-between; align-items:center;">
    <div>
        <span style="color:#8b949e; font-size:12px;">ACTIVE DATA DATE</span>
        <h4 style="margin:0; color:#00e676;">📅 {updated_date}</h4>
    </div>
    <span style="background-color:#21262d; color:#58a6ff; padding:4px 10px; border-radius:6px; font-weight:bold;">
        Total Matches: {len(matches)}
    </span>
</div>
""",
    unsafe_allow_html=True,
)

for m in matches:
    h_name = m["home"]
    a_name = m["away"]
    l_name = m["league"]
    sig = m["signal"]
    prob = m["prob"]
    edge = m["edge"]
    hs = m["h_stats"]
    as_ = m["a_stats"]

    badge_title = "⭐ 5-STAR PICK" if sig != "NEUTRAL" else "MATCH"
    expander_title = (
        f"🏆 {l_name}  |  ⏰ {m['time']}  |  ⚽ {h_name} vs {a_name}  [{sig}]"
    )

    with st.expander(expander_title, expanded=(sig != "NEUTRAL")):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"### ⚽ {h_name} vs {a_name}")
            st.caption(f"🏆 {l_name} ({m['country']}) | ⏰ {m['time']} MMT")
        with c2:
            if sig == "OVER_2_5":
                st.markdown(
                    "<div class='badge-over'>⭐⭐⭐⭐⭐ OVER 2.5</div>",
                    unsafe_allow_html=True,
                )
            elif sig == "UNDER_2_5":
                st.markdown(
                    "<div class='badge-under'>⭐⭐⭐⭐⭐ UNDER 2.5</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div class='badge-neutral'>⚪ NEUTRAL</div>",
                    unsafe_allow_html=True,
                )
            st.write(
                f"**Prob:** {prob}% | **Edge:** {edge:+.1f}% vs 60% threshold"
            )

        st.divider()

        # Stats Columns
        st.markdown(f"#### 🏠 {h_name} (Home L5) vs ✈️ {a_name} (Away L5)")
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            st.markdown(
                f"<div class='stat-box'><b>HOME L5 OVER</b><br><span style='color:#58a6ff; font-size:18px;'>{hs['over_pct']}%</span></div>",
                unsafe_allow_html=True,
            )
        with b2:
            st.markdown(
                f"<div class='stat-box'><b>AWAY L5 OVER</b><br><span style='color:#58a6ff; font-size:18px;'>{as_['over_pct']}%</span></div>",
                unsafe_allow_html=True,
            )
        with b3:
            st.markdown(
                f"<div class='stat-box'><b>HOME L5 BTTS</b><br><span style='color:#00e676; font-size:18px;'>{hs['btts_pct']}%</span></div>",
                unsafe_allow_html=True,
            )
        with b4:
            st.markdown(
                f"<div class='stat-box'><b>AWAY L5 BTTS</b><br><span style='color:#00e676; font-size:18px;'>{as_['btts_pct']}%</span></div>",
                unsafe_allow_html=True,
            )
