import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- CONFIG ---
st.set_page_config(page_title="NomadBase", layout="wide")

# --- AUTH ---
def get_gspread_client():
    # In Streamlit Cloud, use st.secrets. Local: expects secrets.toml or env vars.
    # For now, searching for service_account.json in root for local dev.
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Priority: st.secrets > service_account.json
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        else:
            creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None

# --- CORE LOGIC ---
def app():
    st.title("🏙️ NomadBase - Remote Work Hub")
    st.markdown("Log and find the best cafés and co-working spaces for nomad life.")

    tab1, tab2 = st.tabs(["🔍 Find a Spot", "📝 Log a Visit"])

    # Placeholder for sheet name - users must create this sheet
    SHEET_NAME = "NomadBase_Data"

    client = get_gspread_client()
    if not client:
        st.warning("Please configure Google Cloud Service Account in `st.secrets` or `service_account.json`.")
        return

    try:
        sh = client.open(SHEET_NAME)
        worksheet = sh.get_worksheet(0)
    except Exception:
        st.error(f"Could not find sheet named '{SHEET_NAME}'. Please create it and share it with your Service Account email.")
        return

    # --- TAB 1: VIEW/SEARCH ---
    with tab1:
        st.subheader("Filter Locations")
        data = worksheet.get_all_records()
        if not data:
            st.info("No logs yet! Be the first to add one.")
        else:
            df = pd.DataFrame(data)
            
            # Simple filters
            col1, col2, col3 = st.columns(3)
            with col1:
                search_q = st.text_input("Search Name")
            with col2:
                min_wifi = st.slider("Min WiFi Rating", 1, 5, 1)
            with col3:
                only_outlets = st.checkbox("Must have Outlets")

            # Apply filters
            if search_q:
                df = df[df['Name'].str.contains(search_q, case=False)]
            df = df[df['WiFi Rating'] >= min_wifi]
            if only_outlets:
                df = df[df['Outlets'] == True]

            st.dataframe(df, use_container_width=True)

    # --- TAB 2: LOG VISIT ---
    with tab2:
        st.subheader("Add New Location")
        with st.form("log_form"):
            name = st.text_input("Venue Name")
            col1, col2, col3 = st.columns(3)
            with col1:
                wifi = st.slider("WiFi Speed", 1, 5, 3)
            with col2:
                noise = st.slider("Noise Level (5=Quiet)", 1, 5, 3)
            with col3:
                coffee = st.slider("Coffee Quality", 1, 5, 3)
            
            c1, c2 = st.columns(2)
            with c1:
                laptop = st.checkbox("Laptop-friendly?")
            with c2:
                outlets = st.checkbox("Available Outlets?")

            submitted = st.form_submit_button("Submit Log")
            if submitted:
                if name:
                    new_row = [
                        name, 
                        wifi, 
                        noise, 
                        coffee, 
                        laptop, 
                        outlets, 
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    worksheet.append_row(new_row)
                    st.success(f"Added {name}! Refreshing...")
                    st.rerun()
                else:
                    st.error("Name is required.")

if __name__ == "__main__":
    app()
