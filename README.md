# NomadBase

NomadBase is a Streamlit app for remote workers to log and explore cafés and coworking spaces.

## Features
- Log venues with Wi-Fi, noise, and coffee ratings.
- Track laptop-friendliness and outlet availability.
- Search and filter spots by rating and feature flags.
- Render a real in-app map from Sheet-backed coordinates.
- Store data in Google Sheets using free-tier tooling.

## Setup
1. Create a Google Sheet and share it with your service account.
2. Add credentials in Streamlit secrets or place `service_account.json` in the project root.
3. Set `NOMADBASE_SPREADSHEET_ID` or `NOMADBASE_SPREADSHEET_NAME`.
4. Install dependencies with `pip install -r requirements.txt`.
5. Run `streamlit run app.py`.
6. Add the cleanest address you have when logging a spot; the app geocodes name/address data with OpenStreetMap + Nominatim, and CSV uploads will use Latitude/Longitude directly when present before falling back to geocoding.

## Streamlit secrets example
The app reads these TOML values from Streamlit secrets or `.streamlit/secrets.toml`.

```toml
GOOGLE_SHEET_ID = "your-google-sheet-id"
GOOGLE_SHEET_NAME = "NomadBase_Data"
GOOGLE_WORKSHEET_NAME = "Locations"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```
