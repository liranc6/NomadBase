# NomadBase Setup Instructions

## 1. Google Sheets Setup
1. Create a new Google Sheet named `NomadBase_Data`.
2. Set up the following headers in the first row (A1:G1):
   - `Name`
   - `WiFi Rating`
   - `Noise Rating`
   - `Coffee Rating`
   - `Laptop Friendly`
   - `Outlets`
   - `Last Updated`

## 2. Google Cloud Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select existing.
3. Enable 'Google Sheets API' and 'Google Drive API'.
4. Create a 'Service Account' under 'IAM & Admin'.
5. Create and download a JSON key for the Service Account.
6. **Rename it to `service_account.json`** and place it in the root of the project, or paste its contents into `[gcp_service_account]` inside `.streamlit/secrets.toml`.
7. Copy the client email from the JSON and **Share the Google Sheet** with that email (Editor access).

## 2b. Streamlit secrets example
```toml
GOOGLE_SHEET_ID = "1Hewm-VWxq9GnECuOBHN6-7K7bZvMLpw08Wl7vq417E8"
GOOGLE_SHEET_NAME = "NomadBase_Data"
GOOGLE_WORKSHEET_NAME = "Locations"

[gcp_service_account]
type = "service_account"
project_id = "expensesapp-495423"
private_key_id = "..."
private_key = "..."
client_email = "expensesapp@expensesapp-495423.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

## 3. Local Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
