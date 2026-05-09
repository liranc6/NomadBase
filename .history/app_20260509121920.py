from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import dataclass
from typing import Any

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


st.set_page_config(page_title="NomadBase", page_icon="☕", layout="wide")

HEADER_COLUMNS = [
    "Name",
    "WiFi Rating",
    "Noise Rating",
    "Coffee Rating",
    "Laptop Friendly",
    "Outlets",
    "Last Updated",
]

SHEET_DEFAULT_NAME = "NomadBase_Data"
WORKSHEET_DEFAULT_NAME = "Locations"


@dataclass(frozen=True)
class AppConfig:
    spreadsheet_id: str | None
    spreadsheet_name: str | None
    worksheet_name: str


def _secret_lookup(*keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in st.secrets:
            return st.secrets[key]
    return default


def load_config() -> AppConfig:
    spreadsheet_id = _secret_lookup("NOMADBASE_SPREADSHEET_ID", "spreadsheet_id") or os.getenv("NOMADBASE_SPREADSHEET_ID")
    spreadsheet_name = _secret_lookup("NOMADBASE_SPREADSHEET_NAME", "spreadsheet_name") or os.getenv("NOMADBASE_SPREADSHEET_NAME") or SHEET_DEFAULT_NAME
    worksheet_name = _secret_lookup("NOMADBASE_WORKSHEET_NAME", "worksheet_name") or os.getenv("NOMADBASE_WORKSHEET_NAME") or WORKSHEET_DEFAULT_NAME
    return AppConfig(spreadsheet_id=spreadsheet_id, spreadsheet_name=spreadsheet_name, worksheet_name=worksheet_name)


def _service_account_payload() -> dict[str, Any] | None:
    if "gcp_service_account" in st.secrets:
        return dict(st.secrets["gcp_service_account"])
    if "GCP_SERVICE_ACCOUNT" in st.secrets:
        return dict(st.secrets["GCP_SERVICE_ACCOUNT"])

    env_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if env_json:
        return json.loads(env_json)
    return None


@st.cache_resource
def get_gspread_client() -> gspread.Client:
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    payload = _service_account_payload()
    if payload is not None:
        credentials = Credentials.from_service_account_info(payload, scopes=scope)
        return gspread.authorize(credentials)

    if os.path.exists("service_account.json"):
        credentials = Credentials.from_service_account_file("service_account.json", scopes=scope)
        return gspread.authorize(credentials)

    raise RuntimeError("Google credentials missing. Add st.secrets.gcp_service_account or service_account.json.")


def open_workbook(client: gspread.Client, config: AppConfig) -> gspread.Spreadsheet:
    if config.spreadsheet_id:
        return client.open_by_key(config.spreadsheet_id)
    if config.spreadsheet_name:
        return client.open(config.spreadsheet_name)
    raise RuntimeError("Missing spreadsheet identifier. Set NOMADBASE_SPREADSHEET_ID or NOMADBASE_SPREADSHEET_NAME.")


def get_worksheet(client: gspread.Client, config: AppConfig) -> gspread.Worksheet:
    workbook = open_workbook(client, config)
    try:
        worksheet = workbook.worksheet(config.worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = workbook.add_worksheet(title=config.worksheet_name, rows=1000, cols=len(HEADER_COLUMNS))
        worksheet.append_row(HEADER_COLUMNS)

    current_header = worksheet.row_values(1)
    if current_header != HEADER_COLUMNS:
        if not current_header:
            worksheet.insert_row(HEADER_COLUMNS, index=1)
        else:
            worksheet.update("A1", [HEADER_COLUMNS])
    return worksheet


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "yes", "y", "1"}


def load_locations(worksheet: gspread.Worksheet) -> pd.DataFrame:
    records = worksheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=HEADER_COLUMNS + ["Nomad Score"])

    df = pd.DataFrame(records)
    for column in ["WiFi Rating", "Noise Rating", "Coffee Rating"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)

    for column in ["Laptop Friendly", "Outlets"]:
        df[column] = df[column].apply(_coerce_bool)

    df["Name"] = df["Name"].fillna("").astype(str).str.strip()
    df["Last Updated"] = df.get("Last Updated", pd.Series(dtype=str)).fillna("").astype(str)
    df["Nomad Score"] = df[["WiFi Rating", "Noise Rating", "Coffee Rating"]].mean(axis=1).round(1)
    return df


def append_location(worksheet: gspread.Worksheet, payload: dict[str, Any]) -> None:
    row = [
        payload["Name"],
        payload["WiFi Rating"],
        payload["Noise Rating"],
        payload["Coffee Rating"],
        payload["Laptop Friendly"],
        payload["Outlets"],
        payload["Last Updated"],
    ]
    worksheet.append_row(row, value_input_option="USER_ENTERED")


def apply_filters(
    df: pd.DataFrame,
    search_text: str,
    min_wifi: int,
    min_noise: int,
    min_coffee: int,
    laptop_only: bool,
    outlets_only: bool,
) -> pd.DataFrame:
    filtered = df.copy()

    if search_text:
        filtered = filtered[filtered["Name"].str.contains(search_text, case=False, na=False)]
    filtered = filtered[filtered["WiFi Rating"] >= min_wifi]
    filtered = filtered[filtered["Noise Rating"] >= min_noise]
    filtered = filtered[filtered["Coffee Rating"] >= min_coffee]
    if laptop_only:
        filtered = filtered[filtered["Laptop Friendly"]]
    if outlets_only:
        filtered = filtered[filtered["Outlets"]]

    return filtered.sort_values(by=["Nomad Score", "WiFi Rating", "Coffee Rating"], ascending=False)


def yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def render_metrics(df: pd.DataFrame) -> None:
    total_locations = len(df)
    avg_wifi = round(df["WiFi Rating"].mean(), 1) if total_locations else 0.0
    avg_noise = round(df["Noise Rating"].mean(), 1) if total_locations else 0.0
    avg_coffee = round(df["Coffee Rating"].mean(), 1) if total_locations else 0.0
    laptop_share = round(df["Laptop Friendly"].mean() * 100, 0) if total_locations else 0.0

    metric_cols = st.columns(4)
    metric_cols[0].metric("Spots logged", total_locations)
    metric_cols[1].metric("Avg WiFi", avg_wifi)
    metric_cols[2].metric("Avg quietness", avg_noise)
    metric_cols[3].metric("Laptop-friendly share", f"{int(laptop_share)}%")

    sub_cols = st.columns(2)
    sub_cols[0].caption(f"Coffee quality avg: {avg_coffee}")
    sub_cols[1].caption("Noise rating uses 1 = loud, 5 = quiet.")


def render_setup_panel(config: AppConfig, worksheet_status: str) -> None:
    st.subheader("Setup")
    st.markdown(
        """
        1. Create a Google Sheet and share it with your Service Account email.
        2. Add `gcp_service_account` to Streamlit secrets or `service_account.json` locally.
        3. Set `NOMADBASE_SPREADSHEET_ID` or `NOMADBASE_SPREADSHEET_NAME`.
        4. Keep headers aligned with the schema shown below.
        """
    )

    st.info(
        f"Active config => spreadsheet_id: {config.spreadsheet_id or 'unset'} | "
        f"spreadsheet_name: {config.spreadsheet_name or 'unset'} | worksheet: {config.worksheet_name}"
    )
    st.success(f"Worksheet state: {worksheet_status}")
    st.dataframe(pd.DataFrame({"Header": HEADER_COLUMNS}), use_container_width=True, hide_index=True)


def render_explore_tab(df: pd.DataFrame) -> None:
    st.subheader("Find a work-friendly spot")

    if df.empty:
        st.info("No logs yet. Use the Log tab to add the first NomadBase entry.")
        return

    search_col, wifi_col, noise_col, coffee_col = st.columns([2, 1, 1, 1])
    with search_col:
        search_text = st.text_input("Search by venue name", placeholder="Might search a café, coworking space, or neighborhood")
    with wifi_col:
        min_wifi = st.slider("Min WiFi", 1, 5, 1)
    with noise_col:
        min_noise = st.slider("Min quietness", 1, 5, 1)
    with coffee_col:
        min_coffee = st.slider("Min coffee", 1, 5, 1)

    flag_cols = st.columns(2)
    with flag_cols[0]:
        laptop_only = st.checkbox("Laptop-friendly only")
    with flag_cols[1]:
        outlets_only = st.checkbox("Outlets required")

    filtered = apply_filters(df, search_text, min_wifi, min_noise, min_coffee, laptop_only, outlets_only)

    st.caption(f"Filtered results: {len(filtered)} / {len(df)}")
    display_df = filtered.copy()
    display_df["Laptop Friendly"] = display_df["Laptop Friendly"].apply(yes_no)
    display_df["Outlets"] = display_df["Outlets"].apply(yes_no)
    display_df = display_df[
        [
            "Name",
            "Nomad Score",
            "WiFi Rating",
            "Noise Rating",
            "Coffee Rating",
            "Laptop Friendly",
            "Outlets",
            "Last Updated",
        ]
    ]

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_log_tab(worksheet: gspread.Worksheet, refresh_key: str) -> None:
    st.subheader("Log a café or coworking space")
    with st.form("nomadbase_log_form", clear_on_submit=True):
        name = st.text_input("Venue name", placeholder="e.g. Blue Bottle, WeWork, local café")

        rating_cols = st.columns(3)
        with rating_cols[0]:
            wifi_rating = st.slider("WiFi speed rating", 1, 5, 4)
        with rating_cols[1]:
            noise_rating = st.slider("Noise level rating", 1, 5, 3, help="Use 1 for loud, 5 for quiet")
        with rating_cols[2]:
            coffee_rating = st.slider("Coffee quality rating", 1, 5, 4)

        feature_cols = st.columns(2)
        with feature_cols[0]:
            laptop_friendly = st.checkbox("Laptop-friendly")
        with feature_cols[1]:
            outlets = st.checkbox("Outlets available")

        submitted = st.form_submit_button("Save log")

    if submitted:
        if not name.strip():
            st.error("Venue name is required.")
            return

        payload = {
            "Name": name.strip(),
            "WiFi Rating": int(wifi_rating),
            "Noise Rating": int(noise_rating),
            "Coffee Rating": int(coffee_rating),
            "Laptop Friendly": bool(laptop_friendly),
            "Outlets": bool(outlets),
            "Last Updated": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
        append_location(worksheet, payload)
        st.session_state[refresh_key] = st.session_state.get(refresh_key, 0) + 1
        st.success(f"Saved {payload['Name']} to Google Sheets.")


def app() -> None:
    config = load_config()
    st.title("NomadBase")
    st.markdown("Remote Work Hub for logging and finding café + coworking spots with free tooling.")

    refresh_key = "nomadbase_refresh_counter"
    st.session_state.setdefault(refresh_key, 0)

    try:
        client = get_gspread_client()
        worksheet = get_worksheet(client, config)
        df = load_locations(worksheet)
        worksheet_status = f"connected ({worksheet.title})"
    except Exception as exc:
        worksheet = None
        df = pd.DataFrame(columns=HEADER_COLUMNS + ["Nomad Score"])
        worksheet_status = f"blocked: {exc}"
        st.warning(
            "Google Sheets is not configured yet. Add Streamlit secrets or `service_account.json`, then share the target sheet with the service account."
        )

    render_metrics(df)

    tab_explore, tab_log, tab_setup = st.tabs(["Explore", "Log", "Setup"])

    with tab_explore:
        render_explore_tab(df)

    with tab_log:
        if worksheet is None:
            st.error("Logging is disabled until Google Sheets connection is ready.")
        else:
            render_log_tab(worksheet, refresh_key)

    with tab_setup:
        render_setup_panel(config, worksheet_status)


if __name__ == "__main__":
    app()
