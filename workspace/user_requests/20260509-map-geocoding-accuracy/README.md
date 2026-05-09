# User Request: Map Geocoding Accuracy

request: fix Explore map so logged venues land in the right place

Q? why are imported rows mostly blank coords, and one wrong marker?
A: use address-first geocoding, reduce ambiguous venue-name bias, and keep sheet-backed markers.

Acceptance
- New log entries get stable Latitude/Longitude values when geocoding succeeds.
- CSV uploads geocode with address priority and do not over-bias by venue name.
- Explore still renders markers from sheet data inside Streamlit.
- App makes geocoding failures visible enough to debug instead of silently dropping them.
