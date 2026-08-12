import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Nifty 100 Dashboard", layout="wide")

st.title("Nifty 100 Financial Dashboard")

def fetch_health():
    try:
        r = requests.get(f"{API_BASE_URL}/health")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
    return None

def fetch_companies():
    try:
        r = requests.get(f"{API_BASE_URL}/companies")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

health_data = fetch_health()
if health_data:
    st.sidebar.success("API Status: OK")
    st.sidebar.text(f"Uptime: {health_data.get('uptime_seconds')}s")
else:
    st.sidebar.error("API Status: Offline")

companies = fetch_companies()

if companies:
    st.header(f"Companies ({len(companies)})")
    st.dataframe(companies)
    
    selected_ticker = st.selectbox("Select a company to view details", [c["ticker"] for c in companies])
    if selected_ticker:
        r = requests.get(f"{API_BASE_URL}/companies/{selected_ticker}")
        if r.status_code == 200:
            profile = r.json()
            st.subheader(f"{profile['company_name']} ({profile['ticker']})")
            st.write(f"Sector: {profile['sector_name']}")
            if profile.get('latest_kpis'):
                st.metric("Latest ROE", f"{profile['latest_kpis']['roe']}%")
                st.metric("Debt to Equity", profile['latest_kpis']['debt_to_equity'])
else:
    st.info("No companies found or API is not running.")
