from __future__ import annotations

import datetime as dt
import json
import os
import re
from dataclasses import dataclass
from typing import Any
from contextlib import suppress

import folium
import gspread
import pandas as pd
import streamlit as st
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from google.oauth2.service_account import Credentials
from streamlit_folium import st_folium


st.set_page_config(page_title="NomadBase", page_icon="☕", layout="wide")

HEADER_COLUMNS = [
    "Name",
    "WiFi Rating",
    "Noise Rating",
    "Coffee Rating",
    "Laptop Friendly",
    "Outlets",
    "Last Updated",
    "Address",
    "Latitude",
    "Longitude",
]

SHEET_DEFAULT_NAME = "NomadBase_Data"
WORKSHEET_DEFAULT_NAME = "Locations"
MAP_DEFAULT_CENTER = (37.7749, -122.4194)


@dataclass(frozen=True)
class AppConfig:
    spreadsheet_id: str | None
    spreadsheet_name: str | None
    worksheet_name: str


def _secret_lookup(*keys: str, default: Any = None) -> Any:
    for key in keys:
        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            return default
    return default


def load_config() -> AppConfig:
    spreadsheet_id = (
        _secret_lookup(
            "GOOGLE_SHEET_ID",
            "NOMADBASE_SPREADSHEET_ID",
            "spreadsheet_id",
        )
        or os.getenv("GOOGLE_SHEET_ID")
        or os.getenv("NOMADBASE_SPREADSHEET_ID")
    )
    spreadsheet_name = (
        _secret_lookup(
            "GOOGLE_SHEET_NAME",
            "NOMADBASE_SPREADSHEET_NAME",
            "spreadsheet_name",
        )
        or os.getenv("GOOGLE_SHEET_NAME")
        or os.getenv("NOMADBASE_SPREADSHEET_NAME")
        or SHEET_DEFAULT_NAME
    )
    worksheet_name = (
        _secret_lookup("GOOGLE_WORKSHEET_NAME", "NOMADBASE_WORKSHEET_NAME", "worksheet_name")
        or os.getenv("GOOGLE_WORKSHEET_NAME")
        or os.getenv("NOMADBASE_WORKSHEET_NAME")
        or WORKSHEET_DEFAULT_NAME
    )
    return AppConfig(spreadsheet_id=spreadsheet_id, spreadsheet_name=spreadsheet_name, worksheet_name=worksheet_name)


def _service_account_payload() -> dict[str, Any] | None:
    for key in ("gcp_service_account", "GCP_SERVICE_ACCOUNT"):
        try:
            if key in st.secrets:
                return dict(st.secrets[key])
        except Exception:
            return None

    env_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    return json.loads(env_json) if env_json else None


@st.cache_resource
def get_gspread_client() -> gspread.Client:
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    payload = _service_account_payload()
    
    if payload is not None:
        try:
            credentials = Credentials.from_service_account_info(payload, scopes=scope)
            return gspread.authorize(credentials)
        except ValueError as e:
            raise RuntimeError(
                f"Invalid service account key format. "
                f"Ensure the private_key field is valid JSON. "
                f"Error: {str(e)}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to authorize with service account credentials. "
                f"Check that the service account email is shared with the target Google Sheet (Editor access). "
                f"Error: {str(e)}"
            ) from e

    if os.path.exists("service_account.json"):
        try:
            credentials = Credentials.from_service_account_file("service_account.json", scopes=scope)
            return gspread.authorize(credentials)
        except ValueError as e:
            raise RuntimeError(
                f"Invalid service_account.json format. "
                f"Ensure it is a valid JSON file downloaded directly from Google Cloud Console. "
                f"Error: {str(e)}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to authorize with service_account.json. "
                f"Error: {str(e)}"
            ) from e

    raise RuntimeError(
        "Google credentials not found. "
        "\n\n"
        "**For Streamlit Cloud:**\n"
        "1. Go to your app settings on app.streamlit.io\n"
        "2. Click **Secrets** → paste your service account JSON (as TOML)\n"
        "3. Click Save and the app will reload\n\n"
        "**For local development:**\n"
        "1. Create `.streamlit/secrets.toml` (copy from `.streamlit/secrets.toml.example`)\n"
        "2. Download service account JSON from Google Cloud Console\n"
        "3. Paste the contents into the `[gcp_service_account]` section\n"
        "4. Restart Streamlit (Ctrl+C, then `streamlit run app.py`)"
    )


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


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text if text.lower() != "nan" else ""


def _normalize_location_text(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        return ""

    text = re.sub(r"\s*\([^)]*\)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,")


@st.cache_resource
def get_geocoder() -> RateLimiter:
    geolocator = Nominatim(user_agent="nomadbase_app", timeout=10)
    return RateLimiter(
        geolocator.geocode,
        min_delay_seconds=1.1,
        max_retries=2,
        error_wait_seconds=2,
        swallow_exceptions=True,
    )


@st.cache_data(ttl=86400)
def geocode_location(query: str, country_codes: str | None = None) -> tuple[float, float] | None:
    if not query or not query.strip():
        return None
    with suppress(Exception):
        geolocator = get_geocoder()
        if location := geolocator(query, exactly_one=True, country_codes=country_codes):
            return (location.latitude, location.longitude)
    return None


def get_marker_color(wifi_rating: int) -> str:
    if wifi_rating >= 4:
        return "green"
    return "orange" if wifi_rating == 3 else "red"


def resolve_coordinates(name: str, address: str) -> tuple[float | None, float | None]:
    address = _clean_text(address)
    name = _clean_text(name)

    candidates: list[str] = []
    if address:
        candidates.append(address)

    normalized_address = _normalize_location_text(address)
    if normalized_address and normalized_address not in candidates:
        candidates.append(normalized_address)

    if not address and name:
        candidates.append(name)

    for candidate in candidates:
        country_codes = "il" if "israel" in candidate.lower() else None
        geocoded = geocode_location(candidate, country_codes=country_codes)
        if geocoded is not None:
            return geocoded

    return (None, None)


def get_map_center(map_df: pd.DataFrame) -> tuple[float, float]:
    return float(map_df["Latitude"].mean()), float(map_df["Longitude"].mean())


def build_folium_map(map_df: pd.DataFrame) -> folium.Map:
    center_lat, center_lon = get_map_center(map_df)
    map_object = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")
    marker_points: list[tuple[float, float]] = []

    for _, row in map_df.iterrows():
        latitude = float(row["Latitude"])
        longitude = float(row["Longitude"])
        marker_points.append((latitude, longitude))
        popup_text = f"""
        <b>{row['Name']}</b><br>
        {row.get('Address', '')}<br>
        WiFi: {render_rating_mugs(row['WiFi Rating'])} | Coffee: {render_rating_mugs(row['Coffee Rating'])} | Quiet: {render_rating_mugs(row['Noise Rating'])}<br>
        Laptop-friendly: {yes_no(row['Laptop Friendly'])}<br>
        Outlets: {yes_no(row['Outlets'])}<br>
        <small>{row['Last Updated']}</small>
        """
        folium.Marker(
            location=[latitude, longitude],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=row["Name"],
            icon=folium.Icon(color=get_marker_color(int(row["WiFi Rating"])), icon="coffee", prefix="fa"),
        ).add_to(map_object)

    if len(marker_points) > 1:
        map_object.fit_bounds(marker_points)

    return map_object


def build_location_payload(
    name: str,
    address: str,
    wifi_rating: int,
    noise_rating: int,
    coffee_rating: int,
    laptop_friendly: bool,
    outlets: bool,
) -> dict[str, Any]:
    latitude, longitude = resolve_coordinates(name, address)
    return {
        "Name": name,
        "Address": address,
        "WiFi Rating": wifi_rating,
        "Noise Rating": noise_rating,
        "Coffee Rating": coffee_rating,
        "Laptop Friendly": laptop_friendly,
        "Outlets": outlets,
        "Latitude": latitude,
        "Longitude": longitude,
        "Last Updated": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def render_coffee_rating(label: str, default_value: int = 3, help_text: str = "", key: str = None) -> int:
    """Render a coffee mug emoji rating selector (1-5 mugs)."""
    # Create emoji display for each level
    options = {
        1: "☕",
        2: "☕☕",
        3: "☕☕☕",
        4: "☕☕☕☕",
        5: "☕☕☕☕☕",
    }
    
    return st.select_slider(
        label,
        options=list(options.keys()),
        value=default_value,
        format_func=lambda x: options[x],
        key=key,
        help=help_text,
    )


def load_locations(worksheet: gspread.Worksheet) -> pd.DataFrame:
    records = worksheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=HEADER_COLUMNS + ["Nomad Score"])

    df = pd.DataFrame(records)
    for column in ["Address", "Last Updated"]:
        if column not in df.columns:
            df[column] = ""

    for column in ["WiFi Rating", "Noise Rating", "Coffee Rating"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)

    for column in ["Laptop Friendly", "Outlets"]:
        df[column] = df[column].apply(_coerce_bool)

    for column in ["Latitude", "Longitude"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
        else:
            df[column] = pd.Series(dtype=float)

    for row_index, row in df.iterrows():
        latitude = row.get("Latitude")
        longitude = row.get("Longitude")
        if pd.notna(latitude) and pd.notna(longitude):
            continue

        name = _clean_text(row.get("Name"))
        address = _clean_text(row.get("Address"))
        resolved_latitude, resolved_longitude = resolve_coordinates(name, address)
        if resolved_latitude is None or resolved_longitude is None:
            continue

        df.at[row_index, "Latitude"] = resolved_latitude
        df.at[row_index, "Longitude"] = resolved_longitude

        with suppress(Exception):
            worksheet.update_cell(row_index + 2, 9, resolved_latitude)
            worksheet.update_cell(row_index + 2, 10, resolved_longitude)

    df["Name"] = df["Name"].fillna("").astype(str).str.strip()
    df["Address"] = df["Address"].fillna("").astype(str).str.strip()
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
        payload["Address"],
        payload["Latitude"],
        payload["Longitude"],
    ]
    worksheet.append_row(row, value_input_option="USER_ENTERED")


def create_csv_template() -> bytes:
    """Generate a CSV template for batch uploads."""
    template_df = pd.DataFrame({
        "Name": ["Blue Bottle Coffee", "WeWork San Francisco"],
        "Address": ["1600 Powell St, San Francisco, CA", "535 Mission St, San Francisco, CA"],
        "WiFi Rating": [5, 4],
        "Noise Rating": [4, 3],
        "Coffee Rating": [5, 3],
        "Laptop Friendly": [True, True],
        "Outlets": [True, True],
    })
    return template_df.to_csv(index=False).encode()


def process_csv_upload(csv_file, worksheet: gspread.Worksheet) -> tuple[int, list[str]]:
    """Parse and validate CSV file, then batch insert into Google Sheet.
    
    Returns:
        tuple: (successful_inserts, list_of_error_messages)
    """
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        return 0, [f"Failed to parse CSV: {str(e)}"]
    
    required_cols = {"Name", "WiFi Rating", "Noise Rating", "Coffee Rating", "Laptop Friendly", "Outlets"}
    if missing_cols := required_cols - set(df.columns):
        return 0, [f"Missing required columns: {', '.join(missing_cols)}"]

    if "Address" not in df.columns:
        df["Address"] = ""
    
    errors = []
    rows_to_insert = []
    
    for line_num, (idx, row) in enumerate(df.iterrows(), start=2):
        try:
            name = str(row["Name"]).strip()
            if not name:
                errors.append(f"Row {line_num}: Venue name cannot be empty")
                continue
            
            # Validate ratings are 1-5
            try:
                wifi_rating = int(row["WiFi Rating"])
                noise_rating = int(row["Noise Rating"])
                coffee_rating = int(row["Coffee Rating"])
                
                for rating_val, rating_name in [(wifi_rating, "WiFi Rating"), 
                                                  (noise_rating, "Noise Rating"),
                                                  (coffee_rating, "Coffee Rating")]:
                    if not 1 <= rating_val <= 5:
                        raise ValueError(f"{rating_name} must be 1-5")
            except (ValueError, TypeError) as e:
                errors.append(f"Row {line_num} ({name}): {str(e)}")
                continue
            
            # Convert boolean fields
            try:
                truthy_values = {"true", "yes", "1", "t", "y"}
                laptop_friendly = str(row["Laptop Friendly"]).lower() in truthy_values
                outlets = str(row["Outlets"]).lower() in truthy_values
            except Exception as e:
                errors.append(f"Row {line_num} ({name}): Invalid boolean value - {str(e)}")
                continue
            
            address = _clean_text(row.get("Address"))
            latitude, longitude = resolve_coordinates(name, address)

            # Build row for batch insert
            row_data = [
                name,
                wifi_rating,
                noise_rating,
                coffee_rating,
                laptop_friendly,
                outlets,
                dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                address,
                latitude,
                longitude,
            ]
            rows_to_insert.append(row_data)
        
        except Exception as e:
            errors.append(f"Row {line_num}: {str(e)}")
    
    # Batch insert all valid rows in a single API call
    if rows_to_insert:
        try:
            worksheet.append_rows(rows_to_insert, value_input_option="USER_ENTERED")
        except Exception as e:
            return 0, [f"Failed to insert rows: {str(e)}"] + errors
    
    return len(rows_to_insert), errors


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


def render_rating_mugs(rating: float) -> str:
    """Convert numeric rating (1-5) to coffee mug emoji display."""
    return "—" if rating == 0 else "☕" * int(round(rating))


def render_metrics(df: pd.DataFrame) -> None:
    total_locations = len(df)
    avg_wifi = round(df["WiFi Rating"].mean(), 1) if total_locations else 0.0
    avg_noise = round(df["Noise Rating"].mean(), 1) if total_locations else 0.0
    avg_coffee = round(df["Coffee Rating"].mean(), 1) if total_locations else 0.0
    laptop_share = round(df["Laptop Friendly"].mean() * 100, 0) if total_locations else 0.0

    metric_cols = st.columns(4)
    metric_cols[0].metric("Spots logged", total_locations)
    metric_cols[1].metric("Avg WiFi", render_rating_mugs(avg_wifi), help="Coffee mug rating")
    metric_cols[2].metric("Avg quietness", render_rating_mugs(avg_noise), help="Coffee mug rating")
    metric_cols[3].metric("Laptop-friendly", f"{int(laptop_share)}%")

    sub_cols = st.columns(2)
    sub_cols[0].caption(f"Coffee quality: {render_rating_mugs(avg_coffee)}")
    sub_cols[1].caption("More mugs = better! ☕☕☕☕☕")


def render_setup_panel(config: AppConfig, worksheet_status: str) -> None:
    st.subheader("⚙️ Admin Setup")
    
    st.markdown("### Quick Setup Steps")
    st.markdown(
        """
        1. **Create a Google Sheet** named `NomadBase_Data` (or your preferred name)
        2. **Set headers** in row 1: Name, WiFi Rating, Noise Rating, Coffee Rating, Laptop Friendly, Outlets, Last Updated
        3. **Create a Google Cloud Service Account** and download JSON key
        4. **Share the Sheet** with the service account email (Editor access)
        5. **Add credentials** to Streamlit secrets (see below for your platform)
        """
    )

    if "connected" in worksheet_status:
        st.success(f"✅ Worksheet connection active: {worksheet_status}")
    else:
        st.error(f"❌ Worksheet connection blocked: {worksheet_status}")
        
        st.markdown("### Troubleshooting")
        with st.expander("Fix 'Invalid PEM file' error", expanded=True):
            st.markdown("""
            **Error:** `InvalidData(InvalidByte(0, 46))` or similar PEM parsing error
            
            **Cause:** Service account JSON is corrupted or manually edited.
            
            **Fix:**
            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. IAM & Admin → Service Accounts → select your account
            3. Keys → **delete old keys**
            4. Create a **new JSON key** (download directly, don't edit)
            5. Paste the fresh JSON into your secrets
            6. Restart the app
            """)
        
        with st.expander("For Streamlit Cloud"):
            st.markdown("""
            1. Go to [app.streamlit.io](https://app.streamlit.io) → your app
            2. Settings (gear icon) → **Secrets**
            3. Paste your service account JSON as TOML
            4. Click **Save** → app auto-reloads
            """)
        
        with st.expander("For Local Development"):
            st.markdown("""
            1. Create `.streamlit/secrets.toml` (copy from `.streamlit/secrets.toml.example`)
            2. Download JSON key from Google Cloud Console
            3. Paste contents into the `[gcp_service_account]` section
            4. Save the file
            5. Restart: `Ctrl+C` then `streamlit run app.py`
            """)

    st.markdown("### Active Configuration")
    config_dict = {
        "Spreadsheet ID": config.spreadsheet_id or "(not set)",
        "Spreadsheet Name": config.spreadsheet_name or "(not set)",
        "Worksheet Name": config.worksheet_name or "(not set)",
    }
    st.dataframe(pd.DataFrame(list(config_dict.items()), columns=["Setting", "Value"]), 
                 use_container_width=True, hide_index=True)

    st.markdown("### Schema (Headers)")
    st.dataframe(pd.DataFrame({"Header": HEADER_COLUMNS}), use_container_width=True, hide_index=True)


def render_explore_with_map(df: pd.DataFrame) -> None:
    """Render Explore tab with a real in-app folium map and filters."""
    st.subheader("🗺️ Find work-friendly spots")

    if df.empty:
        st.info("No spots logged yet. Use the **Log** tab to add your first favorite café or coworking space.")
        return

    # Filters
    st.markdown("### Filter spots (☕ = minimum quality)")
    filter_cols = st.columns([2, 1, 1, 1])
    with filter_cols[0]:
        search_text = st.text_input("Search by name", placeholder="e.g., Starbucks, WeWork, Local Café")
    with filter_cols[1]:
        min_wifi = render_coffee_rating(
            "Min WiFi",
            default_value=1,
            key="explore_wifi"
        )
    with filter_cols[2]:
        min_noise = render_coffee_rating(
            "Min Quiet",
            default_value=1,
            key="explore_noise"
        )
    with filter_cols[3]:
        min_coffee = render_coffee_rating(
            "Min Coffee",
            default_value=1,
            key="explore_coffee"
        )

    feature_cols = st.columns(2)
    with feature_cols[0]:
        laptop_only = st.checkbox("Laptop-friendly only")
    with feature_cols[1]:
        outlets_only = st.checkbox("Outlets required")

    # Apply filters
    filtered = apply_filters(df, search_text, min_wifi, min_noise, min_coffee, laptop_only, outlets_only)

    if filtered.empty:
        st.info("No spots match your filters. Try adjusting the criteria.")
        return

    map_df = filtered.dropna(subset=["Latitude", "Longitude"]).copy()
    if map_df.empty:
        st.warning("No map coordinates yet. Add an address for new spots, or wait for geocoding to complete.")
    else:
        st_folium(build_folium_map(map_df), width=1200, height=560)

    # Display table view
    st.markdown(f"### Details ({len(filtered)} results)")
    display_df = filtered.copy()
    display_df["Address"] = display_df["Address"].fillna("").astype(str)
    display_df["Laptop Friendly"] = display_df["Laptop Friendly"].apply(yes_no)
    display_df["Outlets"] = display_df["Outlets"].apply(yes_no)
    display_df["WiFi Rating"] = display_df["WiFi Rating"].apply(render_rating_mugs)
    display_df["Noise Rating"] = display_df["Noise Rating"].apply(render_rating_mugs)
    display_df["Coffee Rating"] = display_df["Coffee Rating"].apply(render_rating_mugs)
    display_df = display_df[
        [
            "Name",
            "Address",
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
    st.subheader("📝 Log a new spot")
    st.markdown("Help the community by logging a café or coworking space you love!")

    with st.form("nomadbase_log_form", clear_on_submit=True):
        name = st.text_input(
            "Venue name",
            placeholder="e.g., Blue Bottle Coffee, WeWork San Francisco, Local Café"
        )
        address = st.text_input(
            "Address (optional, helps with location)",
            placeholder="e.g., 123 Main St, San Francisco, CA"
        )

        st.markdown("### Ratings (☕ = better)")
        rating_cols = st.columns(3)
        with rating_cols[0]:
            wifi_rating = render_coffee_rating(
                "WiFi speed",
                default_value=4,
                help_text="☕=slow, ☕☕☕☕☕=blazing fast",
                key="log_wifi"
            )
        with rating_cols[1]:
            noise_rating = render_coffee_rating(
                "Noise level",
                default_value=3,
                help_text="☕=loud, ☕☕☕☕☕=silent",
                key="log_noise"
            )
        with rating_cols[2]:
            coffee_rating = render_coffee_rating(
                "Coffee quality",
                default_value=4,
                help_text="☕=undrinkable, ☕☕☕☕☕=amazing",
                key="log_coffee"
            )

        st.markdown("### Amenities")
        feature_cols = st.columns(2)
        with feature_cols[0]:
            laptop_friendly = st.checkbox("Laptop-friendly (desk space, outlets)")
        with feature_cols[1]:
            outlets = st.checkbox("Power outlets available")

        submitted = st.form_submit_button("📍 Save spot", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Venue name is required.")
            return

        payload = build_location_payload(
            name=name.strip(),
            address=address.strip(),
            wifi_rating=int(wifi_rating),
            noise_rating=int(noise_rating),
            coffee_rating=int(coffee_rating),
            laptop_friendly=bool(laptop_friendly),
            outlets=bool(outlets),
        )
        
        append_location(worksheet, payload)
        st.session_state[refresh_key] = st.session_state.get(refresh_key, 0) + 1
        st.balloons()
        st.success(f"🎉 Successfully logged **{payload['Name']}**! Thanks for sharing!")

    # CSV Batch Upload Section
    st.markdown("---")
    st.subheader("📤 Batch upload spots (CSV)")
    st.markdown("Upload multiple venues at once using a CSV file. Download the template below to get started.")
    
    csv_col1, csv_col2 = st.columns(2)
    with csv_col1:
        # Template download button
        st.download_button(
            label="📋 Download CSV template",
            data=create_csv_template(),
            file_name="nomadbase_template.csv",
            mime="text/csv",
        )
    
    with csv_col2:
        # File uploader
        uploaded_file = st.file_uploader("Choose CSV file", type="csv", key="batch_upload")
    
    if uploaded_file is not None:
        successful, errors = process_csv_upload(uploaded_file, worksheet)
        
        if successful > 0:
            st.session_state[refresh_key] = st.session_state.get(refresh_key, 0) + 1
            st.success(f"✅ Successfully logged {successful} venue{'s' if successful != 1 else ''}!")
        
        if errors:
            with st.expander(f"⚠️ {len(errors)} error{'s' if len(errors) != 1 else ''} (see details)", expanded=len(errors) <= 3):
                for error in errors:
                    st.error(error)


def is_admin_mode() -> bool:
    """Check if admin mode is enabled via URL param."""
    return st.query_params.get("admin") == "true"


def app() -> None:
    config = load_config()
    st.title("☕ NomadBase")
    st.markdown("**Find and log your favorite work-friendly cafés and coworking spaces.**")

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
        st.error(
            "⚠️ **Google Sheets not configured.** "
            "Please contact the app administrator to set up credentials."
        )

    render_metrics(df)

    # Determine which tabs to show
    admin_mode = is_admin_mode()
    worksheet_error = "blocked" in worksheet_status

    if admin_mode or worksheet_error:
        tab_explore, tab_log, tab_setup = st.tabs(["Explore", "Log", "Setup"])
        show_setup = True
    else:
        tab_explore, tab_log = st.tabs(["Explore", "Log"])
        show_setup = False

    with tab_explore:
        render_explore_with_map(df)

    with tab_log:
        if worksheet is None:
            st.error("Logging is disabled until Google Sheets is configured.")
        else:
            render_log_tab(worksheet, refresh_key)

    if show_setup:
        with tab_setup:
            render_setup_panel(config, worksheet_status)


if __name__ == "__main__":
    app()
