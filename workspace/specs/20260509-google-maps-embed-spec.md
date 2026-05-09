# Technical Spec: Google My Maps Embed

**Date**: 2026-05-09
**Scope**: Public venue map presentation in Streamlit Explore tab
**Decision**: embed-first; user manages map contents in Google My Maps

## Requirements
- Use the provided Google My Maps embed URL in the Explore tab.
- Keep Sheets-backed logging and the filtered venue table.
- Do not add geocoding or live map sync in this change.
- Keep the map visible to public users without extra setup noise.

## Implementation Notes
- `app.py` renders `st.components.v1.iframe()` with the shared embed URL from secrets/env, falling back to the current map.
- `requirements.txt` no longer needs folium/geopy/streamlit-folium.
- `README.md` documents the public-sharing requirement for the map.

## Acceptance Criteria
- Explore loads the embedded map.
- App starts without unused map dependencies.
- Existing log and filter flows still work.
