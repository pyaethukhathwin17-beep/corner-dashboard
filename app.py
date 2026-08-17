from datetime import datetime, timedelta, timezone
import streamlit as st

st.set_page_config(
    page_title="Pre-Match Over/Under Intelligence Pro",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ==================== 1. CYBER DARK THEME ====================
st.markdown(
    """
<style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    .hero-card {
        background: linear-gradient(135deg, #131b26 0%, #1c2636 100%);
        border: 1px solid #00f2fe44;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 242, 254, 0.1);
    }
    .badge-over { background-color: #00e676; color: #042410; padding: 8px 16px; border-radius: 8px; font-weight: 900; font-size: 16px; text-align: center; }
    .badge-under { background-color: #ff1744; color: #ffffff; padding: 8px 16px; border-radius: 8px; font-weight: 900; font-size: 16px; text-align: center; }
    .badge-neutral { background-color: #30363d; color: #8b949e; padding: 8px 16px; border-radius: 8px; font-weight: 900; font-size: 16px; text-align: center; }
    .edge-pos { color: #00e676; font-weight: 900; font-size: 20px; }
    .edge-neg { color: #ff1744; font-weight: 900; font-size: 20px; }
</style>
""",
    unsafe_allow_html=True,
)

# ==================== 2. HEADER ====================
st.markdown(
    """
    ## ⚽ Pre-Match <span style="color:#00f2fe;">Over/Under Intelligence Pro</span>
    <p style="color:#8b949e; font-size:13px;">🛡️ 100% Offline & Anti-Ban Mode • Strict L5 Quantitative Algorithm</p>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ==================== 3. INPUT FORM ====================
col_t1, col_t2 = st.columns(2)
with col_t1:
    home_team = st.text_input("🏠 အိမ်ရှင်အသင်း အမည်", value="Home Team")
with col_t2:
    away_team = st.text_input("✈️ ဧည့်သည်အသင်း အမည်", value="Away Team")

st.markdown("### 📊 အသင်း ၂ သင်း၏ L5 စာရင်းအင်းများ ထည့်သွင်းပါ")

col_h, col_a = st.columns(2)

with col_h:
    st.markdown(f"#### 🏠 {home_team} (Home L5)")
    h_over = st.number_input(
        "Home L5 Over 2.5 %", min_value=0, max_value=100, value=80, step=20
    )
    h_btts = st.number_input(
        "Home L5 BTTS %", min_value=0, max_value=100, value=80, step=20
    )
    h_gf = st.number_input(
        "Home GF (သွင်းဂိုး ပျမ်းမျှ)",
        min_value=0.0,
        max_value=10.0,
        value=2.2,
        step=0.1,
    )
    h_ga = st.number_input(
        "Home GA (ပေးဂိုး ပျမ်းမျှ)",
        min_value=0.0,
        max_value=10.0,
        value=1.4,
        step=0.1,
    )

with col_a:
    st.markdown(f"#### ✈️ {away_team} (Away L5)")
    a_over = st.number_input(
        "Away L5 Over 2.5 %", min_value=0, max_value=100, value=60, step=20
    )
    a_btts = st.number_input(
        "Away L5 BTTS %", min_value=0, max_value=100, value=60, step=20
    )
    a_gf = st.number_input(
        "Away GF (သွင်းဂိုး ပျမ်းမျှ)",
        min_value=0.0,
        max_value=10.0,
        value=1.4,
        step=0.1,
    )
    a_ga = st.number_input(
        "Away GA (ပေးဂိုး ပျမ်းမျှ)",
        min_value=0.0,
        max_value=10.0,
        value=1.6,
        step=0.1,
    )

st.divider()

# ==================== 4. QUANTITATIVE CALCULATION ====================
if st.button("⚡ Calculate & Evaluate 5-Star Target", type="primary", use_container_width=True):
    # Over Criteria
    over_pass = (
        h_over >= 60
        and a_over >= 60
        and h_btts >= 60
        and a_btts >= 60
        and h_gf > 1.5
        and h_ga > 1.0
        and a_gf > 1.0
        and a_ga > 1.0
    )

    # Under Criteria
    under_pass = (
        (100 - h_over) >= 60
        and (100 - a_over) >= 60
        and h_btts <= 50
        and a_btts <= 50
        and h_gf < 1.3
        and h_ga < 1.0
        and a_gf < 1.1
        and a_ga < 1.2
    )

    # Probabilities
    over_comp = (h_over + a_over) / 2
    btts_comp = (h_btts + a_btts) / 2
    atk_comp = min(100, ((h_gf + a_gf) / 4.0) * 100)
    def_comp = min(100, ((h_ga + a_ga) / 3.2) * 100)
    over_prob = round(
        (over_comp * 0.40 + btts_comp * 0.20 + atk_comp * 0.20 + def_comp * 0.20),
        1,
    )

    under_comp = ((100 - h_over) + (100 - a_over)) / 2
    no_btts_comp = ((100 - h_btts) + (100 - a_btts)) / 2
    low_atk = max(0, min(100, 100 - (((h_gf + a_gf) / 3.6) * 100)))
    low_def = max(0, min(100, 100 - (((h_ga + a_ga) / 3.0) * 100)))
    under_prob = round(
        (under_comp * 0.40 + no_btts_comp * 0.20 + low_atk * 0.20 + low_def * 0.20),
        1,
    )

    over_edge = round(over_prob - 60, 1)
    under_edge = round(under_prob - 60, 1)

    signal = "NEUTRAL"
    stars = 0
    prob = max(over_prob, under_prob)
    edge = over_edge if over_prob >= under_prob else under_edge

    if over_pass and over_edge >= 5:
        signal = "OVER_2_5"
        stars = 5
        prob = over_prob
        edge = over_edge
    elif under_pass and under_edge >= 5:
        signal = "UNDER_2_5"
        stars = 5
        prob = under_prob
        edge = under_edge

    st.markdown("### 🎯 Decision & Model Output")

    st.markdown('<div class="hero-card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if signal == "OVER_2_5":
            st.markdown(
                "<div class='badge-over'>⭐⭐⭐⭐⭐ OVER 2.5 TARGET</div>",
                unsafe_allow_html=True,
            )
        elif signal == "UNDER_2_5":
            st.markdown(
                "<div class='badge-under'>⭐⭐⭐⭐⭐ UNDER 2.5 TARGET</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='badge-neutral'>⚪ NEUTRAL (စံနှုန်းမပြည့်ပါ)</div>",
                unsafe_allow_html=True,
            )
    with c2:
        st.markdown(
            f"<b>Model Probability:</b><br><span style='color:#ffd600; font-size:22px; font-weight:900;'>{prob}%</span>",
            unsafe_allow_html=True,
        )
    with c3:
        cls = "edge-pos" if edge >= 0 else "edge-neg"
        st.markdown(
            f"<b>Model Edge (vs 60%):</b><br><span class='{cls}'>{edge:+.1f}%</span>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### 🔎 Strict Rules Verification:")
    st.write(
        f"• Home Over $\ge$ 60%: {'✅ Pass' if h_over >= 60 else '❌ Fail'} ({h_over}%)"
    )
    st.write(
        f"• Away Over $\ge$ 60%: {'✅ Pass' if a_over >= 60 else '❌ Fail'} ({a_over}%)"
    )
    st.write(
        f"• Home BTTS $\ge$ 60%: {'✅ Pass' if h_btts >= 60 else '❌ Fail'} ({h_btts}%)"
    )
    st.write(
        f"• Away BTTS $\ge$ 60%: {'✅ Pass' if a_btts >= 60 else '❌ Fail'} ({a_btts}%)"
    )
    st.write(
        f"• Home GF > 1.5 & GA > 1.0: {'✅ Pass' if (h_gf > 1.5 and h_ga > 1.0) else '❌ Fail'} (GF: {h_gf}, GA: {h_ga})"
    )
    st.write(
        f"• Away GF > 1.0 & GA > 1.0: {'✅ Pass' if (a_gf > 1.0 and a_ga > 1.0) else '❌ Fail'} (GF: {a_gf}, GA: {a_ga})"
    )
    st.write(
        f"• Required Edge $\ge$ +5%: {'✅ Pass' if edge >= 5 else '❌ Fail'} ({edge:+.1f}%)"
    )
