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
6. **Rename it to `service_account.json`** and place it in the root of the project (or use Streamlit Secrets).
7. Copy the client email from the JSON and **Share the Google Sheet** with that email (Editor access).

## 3. Local Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
