import streamlit as st
import requests

st.set_page_config(page_title="Corner Analytics", layout="wide")
st.title("⚽ Corner Under Analytics")

# Streamlit Secrets မှ API Key ခေါ်ယူခြင်း
API_KEY = st.secrets.get("API_KEY", "")

if not API_KEY:
    st.warning("⚠️ API Key ထည့်ရန် လိုအပ်သေးသည်။ Streamlit Cloud Settings တွင် ထည့်ပါ။")

st.subheader("🔥 Today's Recommended Targets")

# Dashboard UI Card ပြသခြင်း
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Dalian K'un vs Shaanxi Union", value="Under Rating: 95%", delta="⭐️⭐️⭐️⭐️⭐️")
    st.write("• Avg Corners: 7.2 | PPDA: 13.5 (Low Pressing)")
    st.success("Recommendation: Prematch / Live Corner Under")

with col2:
    st.metric(label="Yanbian vs Nanjing City", value="Under Rating: 90%", delta="⭐️⭐️⭐️⭐️⭐️")
    st.write("• Avg Corners: 7.8 | xG: 0.9 (Low Chance)")
    st.success("Recommendation: Prematch / Live Corner Under")
