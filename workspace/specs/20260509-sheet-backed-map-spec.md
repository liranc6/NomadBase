# Technical Spec: Sheet-Backed In-App Map

**Date**: 2026-05-09
**Scope**: Replace embed map with a real in-app map driven by Google Sheet data
**Decision**: geocode on write, persist Latitude/Longitude, render markers in Streamlit

## Requirements
- Add Latitude and Longitude columns to the sheet schema.
- Geocode new manual log entries using name + address.
- Geocode CSV uploads using address when available, fallback to name.
- Backfill missing coordinates for existing rows when possible.
- Render Explore with a folium map inside Streamlit and keep the filtered table.

## Implementation Notes
- `app.py` uses `geopy` + `Nominatim` for free geocoding.
- `app.py` uses `folium` + `streamlit-folium` for map rendering.
- Existing rows stay compatible because new columns are appended at the end.
- Address is stored with each row to improve geocoding quality.

## Acceptance Criteria
- New spots appear on the in-app map after saving.
- CSV uploads also appear on the map after import.
- App loads without syntax errors and preserves current filter UX.
